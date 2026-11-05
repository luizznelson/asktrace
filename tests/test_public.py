"""Public HTTP contract: no external AI, database or ignored downloads in these tests."""

import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from asktrace.public import create_app, public_origin


class PublicTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(
            os.environ,
            {"ASKTRACE_PUBLIC_ORIGIN": "https://asktrace.example", "ASKTRACE_PUBLIC_AI": "true"},
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.context = SimpleNamespace(
            root=Path.cwd(),
            token="test-session",
            datasets={"default": "expanded"},
            catalog=[{"id": "expanded", "coverage": "runs/example/coverage.json"}],
            default_coverage="runs/example/coverage.json",
            busy=threading.Lock(),
            runner=Mock(return_value={"status": "refused", "trace": []}),
        )
        self.reserve = Mock(return_value=True)
        self.checker = Mock()
        self.client = TestClient(
            create_app(Path.cwd(), self.context, self.reserve, self.checker),
            base_url="https://asktrace.example",
        )
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def ask(self, **kwargs):
        return self.client.post(
            "/api/ask",
            json={"question": "Resumo", "provider": "baseline"},
            headers={
                "Origin": "https://asktrace.example",
                "X-AskTrace-Token": "test-session",
                **kwargs,
            },
        )

    def test_fixed_assets_health_and_no_internal_files(self):
        for path in ("/", "/app.js", "/presentation.js", "/formatters.js", "/app.css", "/healthz"):
            result = self.client.get(path)
            self.assertEqual(result.status_code, 200)
            self.assertIn("frame-ancestors 'none'", result.headers["Content-Security-Policy"])
        for path in ("/.env", "/data/raw/example.json", "/sql/005_deployment.sql", "/docs"):
            self.assertEqual(self.client.get(path).status_code, 404)

    def test_host_origin_and_token_cannot_be_overridden_by_forwarded_headers(self):
        for headers in (
            {"Origin": "https://other.example"},
            {"X-AskTrace-Token": "wrong"},
            {"Host": "other.example", "X-Forwarded-Host": "asktrace.example"},
        ):
            self.assertEqual(self.ask(**headers).status_code, 403)
        self.context.runner.assert_not_called()
        self.reserve.assert_not_called()

    def test_query_uses_selected_default_and_budget(self):
        self.assertEqual(self.ask().status_code, 200)
        self.context.runner.assert_called_once_with(
            Path.cwd(), Path("runs/example/coverage.json"), "Resumo", "baseline"
        )
        self.reserve.assert_called_once_with(Path.cwd(), False, 10)
        self.assertFalse(self.context.busy.locked())

    def test_global_budget_denial_and_busy_do_not_execute_query(self):
        self.reserve.return_value = False
        self.assertEqual(self.ask().status_code, 429)
        self.assertFalse(self.context.busy.locked())
        self.context.busy.acquire()
        self.assertEqual(self.ask().status_code, 429)
        self.context.busy.release()
        self.context.runner.assert_not_called()

    def test_database_failure_is_safe_and_lock_is_released(self):
        self.reserve.side_effect = RuntimeError("private-database-password")
        result = self.ask()
        self.assertEqual(result.status_code, 503)
        self.assertNotIn("private", result.text)
        self.assertFalse(self.context.busy.locked())
        self.context.runner.assert_not_called()
        self.checker.side_effect = RuntimeError("private-host")
        self.assertEqual(self.client.get("/healthz").status_code, 503)

    def test_invalid_bodies_cannot_reach_runner(self):
        for body in (
            {"question": "x" * 1001, "provider": "baseline"},
            {"question": "Resumo", "provider": "baseline", "dataset": "../.env"},
            {"question": "Resumo", "provider": "baseline", "extra": "x"},
            {"question": "Resumo", "provider": "gemini"},
        ):
            result = self.client.post(
                "/api/ask",
                json=body,
                headers={"Origin": "https://asktrace.example", "X-AskTrace-Token": "test-session"},
            )
            self.assertEqual(result.status_code, 400)
        self.context.runner.assert_not_called()

    def test_public_session_and_disabled_ai(self):
        with patch.dict(os.environ, {"ASKTRACE_PUBLIC_AI": "false"}):
            with TestClient(
                create_app(Path.cwd(), self.context, self.reserve, self.checker),
                base_url="https://asktrace.example",
            ) as client:
                session = client.get("/api/session").json()
                self.assertEqual(session["mode"], "public")
                self.assertEqual(session["providers"], ["baseline"])
                result = client.post(
                    "/api/ask",
                    json={"question": "Resumo", "provider": "fallback"},
                    headers={
                        "Origin": "https://asktrace.example",
                        "X-AskTrace-Token": "test-session",
                    },
                )
                self.assertEqual(result.status_code, 503)
                self.reserve.assert_not_called()

    def test_oversize_stream_and_no_origin_rejected(self):
        result = self.client.post(
            "/api/ask",
            content=json.dumps({"question": "x" * 9000}),
            headers={
                "Content-Type": "application/json",
                "Origin": "https://asktrace.example",
                "X-AskTrace-Token": "test-session",
            },
        )
        self.assertEqual(result.status_code, 400)
        self.assertEqual(self.client.post("/api/ask", json={}).status_code, 403)

    def test_https_origin_is_explicit_and_canonical(self):
        for value in (
            "http://example.com",
            "https://example.com/",
            "https://u:p@example.com",
            "https://example.com?x=1",
            "https://example.com/path",
            "",
        ):
            with self.assertRaises(ValueError):
                public_origin(value)

    def test_startup_rejects_maintenance_secret_before_accessing_data(self):
        with (
            tempfile.TemporaryDirectory() as folder,
            patch.dict(
                os.environ,
                {"ASKTRACE_ADMIN_DATABASE_URL": "postgresql://owner:private-value@db.example/db"},
            ),
            patch("asktrace.public.restore_database_artifact") as restore,
        ):
            with self.assertRaisesRegex(RuntimeError, "public_startup_verification_failed"):
                with TestClient(create_app(Path(folder)), base_url="https://asktrace.example"):
                    pass
            restore.assert_not_called()
