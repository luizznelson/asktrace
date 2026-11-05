"""Local UI boundary: fixed routes, origin/session checks, request bounds and safe errors."""

import http.client
import json
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from asktrace.web import COVERAGE, Server


class WebTests(unittest.TestCase):
    def setUp(self):
        self.runner = Mock(return_value={"status": "refused", "trace": []})
        # HTTP boundary tests do not depend on ignored local downloads.
        # Real snapshot/database behavior is checked by integration tests and the verifier.
        metadata = (
            {"date_start": "2026-08-01", "date_end": "2026-10-31"},
            [{"awarded_value": None}, {"awarded_value": None}],
            {},
            "a" * 64,
        )
        with patch("asktrace.web.dataset", return_value=metadata):
            self.server = Server(Path(__file__).parents[1], 0, self.runner)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.close)

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def request(self, method, path, data=None, **headers):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        body = json.dumps(data).encode() if data is not None else None
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        result = response.status, dict(response.getheaders()), response.read()
        connection.close()
        return result

    def ask(self, data=None, **overrides):
        headers = {
            "Content-Type": "application/json",
            "Origin": self.server.origin,
            "X-AskTrace-Token": self.server.token,
            **overrides,
        }
        return self.request(
            "POST", "/api/ask", data or {"question": "Resumo", "provider": "baseline"}, **headers
        )

    def test_assets_security_headers_and_fixed_route_allowlist(self):
        for path in ("/", "/app.js", "/formatters.js", "/presentation.js", "/app.css"):
            status, headers, body = self.request("GET", path)
            self.assertEqual(status, 200)
            self.assertTrue(body)
            self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
        for path in ("/.env", "/../.env", "/api/evidence?path=.env", "/sql/001_schema.sql"):
            status, _, body = self.request("GET", path)
            if path.startswith("/api/evidence"):
                self.assertEqual(status, 200)
                self.assertIn("coverage", json.loads(body))
            else:
                self.assertEqual(status, 404)

    def test_session_and_same_origin_required(self):
        status, _, body = self.request("GET", "/api/session")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["token"], self.server.token)
        for headers in (
            {"Origin": "https://attacker.invalid"},
            {"X-AskTrace-Token": "wrong"},
            {"Host": "attacker.invalid"},
        ):
            self.assertEqual(self.ask(**headers)[0], 403)
        self.runner.assert_not_called()

    def test_reject_oversized_question_extra_fields_and_unapproved_provider(self):
        for data in (
            {"question": "x" * 1001, "provider": "baseline"},
            {"question": "Resumo", "provider": "gemini"},
            {"question": "Resumo", "provider": "baseline", "sql": "DELETE"},
        ):
            self.assertEqual(self.ask(data)[0], 400)
        self.runner.assert_not_called()

    def test_only_fixed_coverage_and_one_runner_call(self):
        self.assertEqual(self.ask()[0], 200)
        self.runner.assert_called_once_with(self.server.root, Path(COVERAGE), "Resumo", "baseline")

    def test_concurrent_question_does_not_spend_more_quota(self):
        self.server.busy.acquire()
        try:
            self.assertEqual(self.ask()[0], 429)
        finally:
            self.server.busy.release()
        self.runner.assert_not_called()

    def test_failure_does_not_disclose_internal_messages(self):
        self.runner.side_effect = RuntimeError("private-key-test-value")
        status, _, body = self.ask()
        self.assertEqual(status, 503)
        self.assertNotIn(b"private-key", body)

    def test_unknown_dataset_is_rejected_before_model_or_query(self):
        self.assertEqual(
            self.ask({"question": "Resumo", "provider": "baseline", "dataset": "../.env"})[0], 400
        )
        self.assertEqual(self.request("GET", "/api/evidence?dataset=unknown")[0], 404)
        self.runner.assert_not_called()

    def test_selected_dataset_uses_its_explicit_coverage(self):
        self.server.catalog.append({"id": "fixture", "coverage": "runs/fixture/coverage.json"})
        self.assertEqual(
            self.ask({"question": "Resumo", "provider": "baseline", "dataset": "fixture"})[0], 200
        )
        self.runner.assert_called_once_with(
            self.server.root, Path("runs/fixture/coverage.json"), "Resumo", "baseline"
        )

    def test_availability_check_does_not_execute_question(self):
        status, _, body = self.request("GET", "/api/availability")
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertIn("can_attempt_ai", data)
        self.assertFalse(data["database_checked"])
        self.runner.assert_not_called()

    def test_non_ascii_token_is_rejected_without_crashing(self):
        self.assertEqual(self.ask(**{"X-AskTrace-Token": "é"})[0], 403)
        self.runner.assert_not_called()

    def test_ambiguous_framing_and_nested_json_are_rejected(self):
        self.assertEqual(self.ask(**{"Transfer-Encoding": "chunked"})[0], 400)
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        connection.request(
            "POST",
            "/api/ask",
            body="[" * 1100 + "]" * 1100,
            headers={
                "Content-Type": "application/json",
                "Origin": self.server.origin,
                "X-AskTrace-Token": self.server.token,
            },
        )
        response = connection.getresponse()
        self.assertEqual(response.status, 400)
        response.read()
        connection.close()
        self.runner.assert_not_called()

    def test_corrupt_provider_state_does_not_block_local_session(self):
        with patch("asktrace.web.availability", side_effect=ValueError("private-path-secret")):
            status, _, body = self.request("GET", "/api/session")
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body)["availability"]["status"], "unknown")
            self.assertNotIn(b"secret", body)
            self.assertEqual(self.request("GET", "/api/availability")[0], 503)
            self.assertEqual(self.ask()[0], 200)

    def test_missing_asset_returns_safe_error(self):
        with patch("pathlib.Path.read_bytes", side_effect=OSError("private-path-secret")):
            status, _, body = self.request("GET", "/app.js")
        self.assertEqual(status, 503)
        self.assertNotIn(b"secret", body)

    def test_content_type_and_body_size_checked(self):
        self.assertEqual(self.ask(**{"Content-Type": "text/plain"})[0], 415)
        self.assertEqual(self.ask({"question": "x" * 9000, "provider": "baseline"})[0], 400)


if __name__ == "__main__":
    unittest.main()
