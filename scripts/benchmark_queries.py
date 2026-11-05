"""Measure public query paths locally with real Neon and already prepared source files.

Not a Render benchmark or an artifact restoration/restart test. Reserves twelve baseline
requests. Credentials are read from the ignored runtime file and never printed.
"""

import hashlib
import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from dotenv import dotenv_values
from fastapi.testclient import TestClient

from asktrace.public import create_app
from asktrace.web import Application


def main():
    root = Path.cwd()
    report = {
        "started_at": datetime.now(UTC).isoformat(),
        "transport": "local ASGI with real Neon, prepared and verified source files",
        "external_deployment_verified": False,
        "artifact_restoration_tested": False,
        "restart_verified": False,
        "external_ai_calls": 0,
        "queries": [],
        "passed": False,
    }
    folder = root / "runs" / ("query-benchmark-" + str(uuid4()))
    folder.mkdir()

    def save():
        (folder / "verification.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    try:
        settings = dict(dotenv_values(root / "data/deploy/runtime.env"))
        assert all(
            settings.get(k)
            for k in (
                "ASKTRACE_DATABASE_URL",
                "ASKTRACE_STATE_DATABASE_URL",
                "ASKTRACE_DATA_SHA256",
            )
        )
        settings.update(
            ASKTRACE_PUBLIC_ORIGIN="https://asktrace-benchmark.example", ASKTRACE_PUBLIC_AI="false"
        )
        with patch.dict(os.environ, settings), patch("asktrace.connections.load_dotenv"):
            for key in (
                "ASKTRACE_ADMIN_DATABASE_URL",
                "ASKTRACE_TEST_DATABASE",
                "ASKTRACE_DATABASE_NAME",
            ):
                os.environ.pop(key, None)
            started = time.perf_counter()
            application = Application(root, verified_runtime=True)
            report["evidence_verification_seconds"] = round(time.perf_counter() - started, 3)
            print("Source evidence verified; measuring queries", flush=True)
            with TestClient(
                create_app(root, application=application),
                base_url=settings["ASKTRACE_PUBLIC_ORIGIN"],
            ) as client:
                assert client.get("/healthz").status_code == 200
                session = client.get("/api/session").json()
                headers = {
                    "Origin": settings["ASKTRACE_PUBLIC_ORIGIN"],
                    "X-AskTrace-Token": session["token"],
                }
                questions = {
                    "summary": "Qual é o resumo da cobertura?",
                    "municipalities": "Quais municípios têm mais compras?",
                    "monthly": "Como evoluíram as compras por mês?",
                    "organizations": "Quais órgãos têm mais compras?",
                    "quality": "Como está a qualidade dos dados?",
                }
                for dataset in session["datasets"]:
                    expected = {"expanded": (2537, 679, 2536), "original": (1081, 125, 1080)}[
                        dataset["id"]
                    ]
                    for action, question in {
                        **questions,
                        "purchase": "Rastreie a compra " + dataset["example_purchase_id"] + ".",
                    }.items():
                        started = time.perf_counter()
                        response = client.post(
                            "/api/ask",
                            json={
                                "question": question,
                                "provider": "baseline",
                                "dataset": dataset["id"],
                            },
                            headers=headers,
                        )
                        elapsed = round(time.perf_counter() - started, 3)
                        data = response.json()
                        assert response.status_code == 200 and data["status"] == "answered"
                        facts = data["evidence"]["coverage"]
                        assert data["evidence"]["question"] == action
                        assert (
                            tuple(facts[k] for k in ("purchases", "contracts", "covered_purchases"))
                            == expected
                        )
                        report["queries"].append(
                            {
                                "dataset": dataset["id"],
                                "action": action,
                                "seconds": elapsed,
                                "response_sha256": hashlib.sha256(response.content).hexdigest(),
                            }
                        )
                        save()
                        print(dataset["id"], action, elapsed, flush=True)
            report["passed"] = True
    except Exception as error:
        report["error_type"] = type(error).__name__
        print("Benchmark incomplete:", type(error).__name__, flush=True)
    finally:
        report["finished_at"] = datetime.now(UTC).isoformat()
        report["source_sha256"] = {
            name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in (
                "asktrace/agent.py",
                "asktrace/query.py",
                "asktrace/web.py",
                "asktrace/public.py",
                "asktrace/contracts.py",
            )
        }
        save()
        print(folder.relative_to(root), flush=True)
    return int(not report["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
