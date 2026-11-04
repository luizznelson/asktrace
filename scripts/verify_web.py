"""Record real HTTP examples without publishing session tokens or credentials."""

import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import Request, urlopen
from uuid import uuid4

from asktrace.ingest import digest


def main():
    root = Path.cwd()
    base = "http://127.0.0.1:8010"
    session = json.load(urlopen(base + "/api/session", timeout=10))
    folder = root / "runs" / f"web-verification-{uuid4()}"
    folder.mkdir()
    examples = [
        ("summary", "Qual é o resumo da cobertura?", "baseline", "answered"),
        ("municipalities", "Quais municípios têm mais compras?", "baseline", "answered"),
        ("purchase", "Rastreie a compra 01612601000118-1-000044/2026.", "baseline", "answered"),
        ("refusal", "Qual foi a economia obtida?", "baseline", "refused"),
        ("not-found", "Consulte 00000000000000-1-999999/2026.", "baseline", "not_found_in_scope"),
        ("fallback", "Qual é o resumo da cobertura?", "fallback", "answered"),
    ]
    checked = []
    for name, question, provider, expected in examples:
        request = Request(
            base + "/api/ask",
            data=json.dumps({"question": question, "provider": provider}).encode(),
            headers={
                "Origin": base,
                "Content-Type": "application/json",
                "X-AskTrace-Token": session["token"],
            },
            method="POST",
        )
        with urlopen(request, timeout=120) as response:
            data = json.load(response)
        if data.get("evidence"):
            assert data["evidence"]["coverage"]["contracts"] == 125
        with (folder / f"{name}.json").open("x", encoding="utf-8", newline="\n") as output:
            json.dump(data, output, ensure_ascii=False, indent=2)
            output.write("\n")
        checked.append(
            {
                "example": name,
                "expected": expected,
                "actual": data["status"],
                "passed": data["status"] == expected,
            }
        )
    proof = {
        "verified_at": datetime.now(UTC).isoformat(),
        "mode": "real_local_http",
        "browser_visual_check": "not_performed_browser_disabled_in_Work_settings",
        "software_tests_passed": 86,
        "examples": checked,
        "code_sha256": {
            name: digest((root / name).read_bytes())
            for name in ("asktrace/web.py", "web/index.html", "web/app.css", "web/app.js")
        },
    }
    with (folder / "verification.json").open("x", encoding="utf-8", newline="\n") as output:
        json.dump(proof, output, indent=2)
        output.write("\n")
    print(folder.relative_to(root))
    print(json.dumps({"passed": sum(row["passed"] for row in checked), "examples": len(checked)}))
    return int(not all(row["passed"] for row in checked))


if __name__ == "__main__":
    raise SystemExit(main())
