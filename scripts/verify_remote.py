"""Verify startup and six routes per dataset against the configured remote database.

Run before public traffic: this verifier reserves twelve requests in the shared demo budget.
Never prints credentials or raw records. Requires ignored data/deploy/runtime.env.
"""

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

from dotenv import dotenv_values
from fastapi.testclient import TestClient
from psycopg.rows import dict_row

from asktrace.connections import connect
from asktrace.public import create_app


def verify():
    root = Path.cwd()
    settings = dict(dotenv_values(root / "data/deploy/runtime.env"))
    assert all(
        settings.get(key)
        for key in ("ASKTRACE_DATABASE_URL", "ASKTRACE_STATE_DATABASE_URL", "ASKTRACE_DATA_SHA256")
    )
    settings.update(
        ASKTRACE_PUBLIC_ORIGIN="https://asktrace-verification.example", ASKTRACE_PUBLIC_AI="false"
    )
    report = {
        "started_at": datetime.now(UTC).isoformat(),
        "remote_database_verified": False,
        "external_deployment_verified": False,
        "browser_visual_inspection": False,
        "external_ai_calls": 0,
        "private_settings_file": "data/deploy/runtime.env",
        "artifact_sha256": settings["ASKTRACE_DATA_SHA256"],
        "queries": [],
    }
    with patch.dict(os.environ, settings):
        os.environ.pop("ASKTRACE_ADMIN_DATABASE_URL", None)
        os.environ.pop("ASKTRACE_TEST_DATABASE", None)
        os.environ.pop("ASKTRACE_DATABASE_NAME", None)
        with tempfile.TemporaryDirectory(prefix="asktrace-neon-") as folder:
            cold = Path(folder)
            for name in ("config", "runs", "web"):
                shutil.copytree(root / name, cold / name)
            assert not (cold / "data").exists()
            with connect(cold, row_factory=dict_row) as db:
                assert db.pgconn.ssl_in_use
                assert (
                    db.execute(
                        "SELECT count(*) AS n FROM asktrace.report_purchases "
                        "WHERE control_id LIKE %s",
                        ("synthetic-%",),
                    ).fetchone()["n"]
                    == 0
                )
            report["synthetic_records_remaining"] = 0
            with connect(cold, "state", row_factory=dict_row) as db:
                before = db.execute(
                    "SELECT value FROM asktrace.runtime_state WHERE name='public-budget'"
                ).fetchone()
            report["budget_before"] = (
                before["value"].get("daily", 0)
                if before and before["value"].get("day") == int(time.time() // 86400)
                else 0
            )
            questions = {
                "summary": "Qual é o resumo da cobertura?",
                "municipalities": "Quais municípios têm mais compras?",
                "monthly": "Como evoluíram as compras por mês?",
                "organizations": "Quais órgãos têm mais compras?",
                "quality": "Como está a qualidade dos dados?",
            }
            with TestClient(
                create_app(cold), base_url=settings["ASKTRACE_PUBLIC_ORIGIN"]
            ) as client:
                assert client.get("/healthz").status_code == 200
                session = client.get("/api/session").json()
                assert session["mode"] == "public"
                assert session["providers"] == ["baseline"]
                token = session["token"]
                for dataset in session["datasets"]:
                    expected = {"expanded": (2537, 679, 2536), "original": (1081, 125, 1080)}[
                        dataset["id"]
                    ]
                    for action, question in {
                        **questions,
                        "purchase": "Rastreie a compra " + dataset["example_purchase_id"] + ".",
                    }.items():
                        response = client.post(
                            "/api/ask",
                            json={
                                "question": question,
                                "provider": "baseline",
                                "dataset": dataset["id"],
                            },
                            headers={
                                "Origin": settings["ASKTRACE_PUBLIC_ORIGIN"],
                                "X-AskTrace-Token": token,
                            },
                        )
                        assert response.status_code == 200, (
                            dataset["id"],
                            action,
                            response.status_code,
                        )
                        data = response.json()
                        assert data["status"] == "answered", (dataset["id"], action, data["status"])
                        assert data["evidence"]["question"] == action
                        facts = data["evidence"]["coverage"]
                        assert (
                            facts["purchases"],
                            facts["contracts"],
                            facts["covered_purchases"],
                        ) == expected
                        report["queries"].append(
                            {
                                "dataset": dataset["id"],
                                "action": action,
                                "purchases": facts["purchases"],
                                "contracts": facts["contracts"],
                                "covered_purchases": facts["covered_purchases"],
                                "response_sha256": hashlib.sha256(response.content).hexdigest(),
                            }
                        )
                        print("Neon verified:", dataset["id"], action, flush=True)
            with TestClient(
                create_app(cold), base_url=settings["ASKTRACE_PUBLIC_ORIGIN"]
            ) as restarted:
                assert restarted.get("/healthz").status_code == 200
                fresh = restarted.get("/api/session").json()
                assert fresh["token"] != token
                invalid = restarted.post(
                    "/api/ask",
                    json={
                        "question": questions["summary"],
                        "provider": "baseline",
                        "dataset": "expanded",
                    },
                    headers={
                        "Origin": settings["ASKTRACE_PUBLIC_ORIGIN"],
                        "X-AskTrace-Token": token,
                    },
                )
                assert invalid.status_code == 403
            with connect(cold, "state", row_factory=dict_row) as db:
                after = db.execute(
                    "SELECT value FROM asktrace.runtime_state WHERE name='public-budget'"
                ).fetchone()["value"]
            assert after["daily"] == report["budget_before"] + 12
            report["budget_after_restart"] = after["daily"]
            report["budget_survived_application_restart"] = True
            report["client_tls_verified"] = True
            report["startup_checks_used_real_remote_roles"] = True
            report["private_artifact_restored_from_database"] = True
            report["remote_database_verified"] = True
    report["finished_at"] = datetime.now(UTC).isoformat()
    report["transport_note"] = (
        "ASGI client with actual remote database, artifact and runtime state. "
        "No public Render URL or browser inspection is claimed."
    )
    report["source_sha256"] = {
        str(path.relative_to(root)).replace("\\", "/"): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in [
            root / "asktrace/connections.py",
            root / "asktrace/database.py",
            root / "asktrace/contracts.py",
            root / "asktrace/public.py",
            root / "asktrace/release.py",
            root / "tests/test_deployment_data.py",
        ]
    }
    target = root / "runs" / ("neon-verification-" + str(uuid4()))
    target.mkdir()
    (target / "verification.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    print("Evidence saved:", target.name, flush=True)


def main():
    try:
        verify()
        return 0
    except Exception as error:
        print(json.dumps({"error_type": type(error).__name__, "verification": "remote"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
