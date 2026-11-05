"""Executed from the repository root; publishes only minimized local verification results."""

import hashlib
import http.client
import json
import os
import re
import subprocess
import threading
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from dotenv import dotenv_values

from asktrace.query import connect
from asktrace.web import Server

root = Path.cwd()
report = {
    "version": 1,
    "started_at": datetime.now(UTC).isoformat(),
    "external_ai_calls": 0,
    "browser_visual_inspection": False,
    "checks": [],
}
environment = dict(os.environ, ASKTRACE_TEST_DATABASE="1")
commands = [
    [".venv/Scripts/python.exe", "-m", "unittest", "discover", "-s", "tests", "-q"],
    [".venv/Scripts/ruff.exe", "check", "."],
    [".venv/Scripts/ruff.exe", "format", "--check", "."],
    ["node", "--check", "web/app.js"],
    ["node", "--check", "web/presentation.js"],
    ["node", "tests/test_result_presentation.cjs"],
    ["node", "--check", "web/formatters.js"],
    ["node", "tests/test_display_formatters.cjs"],
    ["node", "tests/test_assistant_ui.cjs"],
    ["git", "diff", "--check"],
]
for command in commands:
    result = subprocess.run(command, env=environment, capture_output=True, text=True)
    check = {"command": command, "exit_code": result.returncode}
    if command[1:3] == ["-m", "unittest"]:
        count = re.search(r"Ran (\d+) tests", result.stderr)
        check["tests_run"] = int(count[1]) if count else None
    report["checks"].append(check)
    if result.returncode:
        print(result.stdout, result.stderr)
        raise SystemExit("Validation failed: " + command[0])
    print("Passed:", " ".join(command), flush=True)

files = (
    subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"])
    .decode()
    .split("\0")
)
secrets = [
    value.encode()
    for key, value in dotenv_values(root / ".env").items()
    if value
    and len(value) >= 12
    and any(marker in key for marker in ("KEY", "PASSWORD", "TOKEN", "SECRET"))
]
matches = [
    name
    for name in files
    if name
    and (root / name).is_file()
    and any(secret in (root / name).read_bytes() for secret in secrets)
]
if matches or ".env" in files:
    raise SystemExit("Credential scan failed; no secret contents are printed.")
report["credential_check"] = {
    "scope": "tracked and nonignored untracked files; exact configured secret values",
    "files_checked": len([name for name in files if name]),
    "configured_secret_matches": 0,
    "env_tracked": False,
    "limitation": "Not a scan of Git history or unknown/revoked credentials.",
}

with connect(root) as db:
    role = db.execute(
        "SELECT rolsuper, rolcreatedb, rolcreaterole FROM pg_roles WHERE rolname=current_user"
    ).fetchone()
    readonly = db.execute("SHOW transaction_read_only").fetchone()["transaction_read_only"]
    permissions = db.execute(
        "SELECT has_table_privilege(current_user, 'asktrace.report_purchases', 'SELECT') "
        "AS can_read, has_table_privilege(current_user, 'asktrace.purchases', 'INSERT') "
        "AS can_insert"
    ).fetchone()
    assert (
        readonly == "on"
        and not any(role.values())
        and permissions == {"can_read": True, "can_insert": False}
    )
    report["database_permissions"] = {**role, **permissions, "transaction_read_only": readonly}

server = Server(root, 0)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()


def request(method, path, data=None):
    connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=30)
    headers = {
        "Content-Type": "application/json",
        "Origin": server.origin,
        "X-AskTrace-Token": server.token,
    }
    connection.request(method, path, json.dumps(data) if data else None, headers)
    response = connection.getresponse()
    body = response.read()
    connection.close()
    return response.status, body


try:
    status, body = request("GET", "/")
    assert status == 200 and re.search(rb'id="availability-notice"[^>]*\bhidden\b', body)
    status, body = request("GET", "/api/session")
    assert status == 200 and json.loads(body)["default_dataset"] == "expanded"
    report["http_queries"] = []
    for dataset, expected, action, question in [
        ("original", 1081, "summary", "Qual é o resumo da cobertura?"),
        ("expanded", 2537, "municipalities", "Quais municípios têm mais compras no recorte?"),
        ("expanded", 2537, "monthly", "Como evoluíram as compras por mês de publicação?"),
        ("expanded", 2537, "organizations", "Quais órgãos têm mais compras na base?"),
        ("expanded", 2537, "quality", "Como está a qualidade e o preenchimento dos dados?"),
    ]:
        status, body = request(
            "POST", "/api/ask", {"question": question, "provider": "baseline", "dataset": dataset}
        )
        result = json.loads(body)
        assert (
            status == 200 and result.get("status") == "answered" and result.get("llm_attempts") == 0
        ), {
            "dataset": dataset,
            "action": action,
            "http_status": status,
            "status": result.get("status"),
            "error": result.get("error"),
            "failure_types": [
                step.get("error_type")
                for step in result.get("trace", [])
                if step.get("step") == "failure"
            ],
        }
        assert result["evidence"]["coverage"]["purchases"] == expected
        assert result["evidence"]["question"] == action
        rows = result["evidence"]["result"]
        if action == "monthly":
            assert [row["purchases"] for row in rows] == [505, 527, 424, 412, 373, 296]
            assert sum(row["purchases"] for row in rows) == expected
        if action == "organizations":
            assert len(rows) <= 20 and len({row["org_cnpj"] for row in rows}) == len(rows)
            assert all(
                rows[i]["purchases"] >= rows[i + 1]["purchases"] for i in range(len(rows) - 1)
            )
        if action == "quality":
            assert rows[0]["purchases"] == expected and rows[0]["unknown_awarded_values"] == 1354
        report["http_queries"].append(
            {
                "dataset": dataset,
                "action": action,
                "row_count": len(rows),
                "status": result["status"],
                "purchases": expected,
                "tool_calls": result["tool_calls"],
                "llm_attempts": 0,
                "scope": result["evidence"]["scope"],
                "response_sha256": hashlib.sha256(body).hexdigest(),
            }
        )
finally:
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)

report["source_sha256"] = {
    name: hashlib.sha256((root / name).read_bytes()).hexdigest()
    for name in files
    if name
    and (
        (name.startswith("asktrace/") and name.endswith(".py"))
        or name.startswith("web/")
        or name.startswith("tests/")
    )
}
report["finished_at"] = datetime.now(UTC).isoformat()
folder = root / "runs" / ("application-review-" + str(uuid4()))
folder.mkdir()
(folder / "verification.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
)
print("Evidence saved:", folder.name, flush=True)
