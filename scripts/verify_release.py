"""Cold-data restoration and twelve real read-only queries through the public ASGI routes."""

import argparse
import hashlib
import json
import os
import shutil
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from dotenv import load_dotenv
from fastapi.testclient import TestClient

from asktrace.deployment_data import restore
from asktrace.public import create_app
from asktrace.query import connect
from asktrace.web import Application


def reader_check(root):
    with connect(root) as db:
        assert db.execute("SHOW transaction_read_only").fetchone()["transaction_read_only"] == "on"
        assert db.execute("SELECT 1 AS healthy").fetchone()["healthy"] == 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--software-report", type=Path, required=True)
    args = parser.parse_args()
    root = Path.cwd()
    load_dotenv(root / ".env", override=False)
    software = json.loads(args.software_report.read_bytes())
    assert all(row["exit_code"] == 0 for row in software["checks"])
    for name, expected in software["source_sha256"].items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == expected, name
    artifact = json.loads((root / "data/deploy/artifact.json").read_bytes())
    started = time.perf_counter()
    report = {
        "started_at": datetime.now(UTC).isoformat(),
        "software_report": args.software_report.as_posix(),
        "artifact_sha256": artifact["sha256"],
        "artifact_bytes": artifact["bytes"],
        "external_ai_calls": 0,
        "remote_deployment_tested": False,
        "browser_visual_inspection": False,
        "transport_note": "ASGI TestClient and the real local read-only PostgreSQL login. "
        "Public role checks and persistent budget are tested separately; deployment uses both.",
        "queries": [],
    }
    with tempfile.TemporaryDirectory(prefix="asktrace-cold-") as folder:
        cold = Path(folder)
        for name in ("config", "runs", "web"):
            shutil.copytree(root / name, cold / name)
        assert not (cold / "data").exists()
        restore(cold, (root / "data/deploy/sources.zip").read_bytes(), artifact["sha256"])
        context = Application(cold)
        assert len(context.catalog) == 2
        report["cold_data_restoration_seconds"] = round(time.perf_counter() - started, 3)
        questions = {
            "summary": "Qual é o resumo da cobertura?",
            "municipalities": "Quais municípios têm mais compras?",
            "monthly": "Como evoluíram as compras por mês?",
            "organizations": "Quais órgãos têm mais compras?",
            "quality": "Como está a qualidade dos dados?",
        }
        # The fixture origin is HTTPS; local queries stay local. No public TLS is claimed.
        with patch.dict(
            os.environ,
            {"ASKTRACE_PUBLIC_ORIGIN": "https://release.example", "ASKTRACE_PUBLIC_AI": "false"},
        ):
            app = create_app(cold, context, reserver=lambda *_: True, checker=reader_check)
        with TestClient(app, base_url="https://release.example") as client:
            assert client.get("/healthz").status_code == 200
            session = client.get("/api/session").json()
            assert session["mode"] == "public" and session["providers"] == ["baseline"]
            for selected in context.catalog:
                assert selected["example_purchase_id"]
                selected_questions = {
                    **questions,
                    "purchase": "Rastreie a compra " + selected["example_purchase_id"] + ".",
                }
                for action, question in selected_questions.items():
                    result = client.post(
                        "/api/ask",
                        json={
                            "question": question,
                            "provider": "baseline",
                            "dataset": selected["id"],
                        },
                        headers={
                            "Origin": "https://release.example",
                            "X-AskTrace-Token": session["token"],
                        },
                    )
                    assert result.status_code == 200, (selected["id"], action)
                    data = result.json()
                    assert data["status"] == "answered", (selected["id"], action)
                    assert data["tool_calls"] == 1 and data["llm_attempts"] == 0
                    assert data["evidence"]["question"] == action
                    coverage = data["evidence"]["coverage"]
                    assert coverage["purchases"] == selected["purchases"]
                    assert coverage["contracts"] == selected["contracts"]
                    assert data["evidence"]["coverage_report_sha256"] == selected["coverage_sha256"]
                    report["queries"].append(
                        {
                            "dataset": selected["id"],
                            "action": action,
                            "purchases": coverage["purchases"],
                            "contracts": coverage["contracts"],
                            "response_sha256": hashlib.sha256(result.content).hexdigest(),
                        }
                    )
                    print("Passed public route:", selected["id"], action, flush=True)
    report["finished_at"] = datetime.now(UTC).isoformat()
    target = root / "runs" / ("release-verification-" + str(uuid4()))
    target.mkdir()
    (target / "verification.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    print("Evidence saved:", target.name, flush=True)


if __name__ == "__main__":
    main()
