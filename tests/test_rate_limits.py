import json
import unittest
from datetime import UTC, datetime

from asktrace.rate_limits import duration, hints


class RateLimitTests(unittest.TestCase):
    def test_fractional_retry_and_duration_headers(self):
        self.assertEqual(duration("2m3.5s"), 123.5)
        self.assertEqual(hints({"Retry-After": "2.5"}, b"{}")["retry_after_seconds"], 2.5)
        result = hints(
            {"x-ratelimit-remaining-tokens": "0", "x-ratelimit-reset-tokens": "1m2s"}, b"{}"
        )
        self.assertEqual(result["retry_after_seconds"], 62)

    def test_safe_groq_message_extracts_only_limit_and_duration(self):
        body = json.dumps(
            {
                "error": {
                    "message": "private-project token-secret: Limit TPM; "
                    "please try again in 2m3.5s."
                }
            }
        ).encode()
        result = hints({}, body)
        self.assertEqual(result["limit_kind"], "tokens_per_minute")
        self.assertEqual(result["retry_after_seconds"], 123.5)
        self.assertNotIn("private", json.dumps(result))
        self.assertNotIn("secret", json.dumps(result))

    def test_date_and_invalid_payloads(self):
        now = datetime(2026, 11, 4, 12, 0, tzinfo=UTC)
        self.assertEqual(
            hints({"Retry-After": "Wed, 04 Nov 2026 12:01:00 GMT"}, b"{}", now)[
                "retry_after_seconds"
            ],
            60,
        )
        for body in (b"not-json", b"[]", b"x" * 65537):
            self.assertEqual(hints({}, body), {})
        for value in ("inf", "NaN", "-30", "30secret"):
            self.assertIsNone(duration(value))
