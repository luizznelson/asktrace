"""Request-scoped model instructions never leak across dataset queries."""

import unittest

from asktrace.planning import ACTIVE_SCOPE, PROMPT, current_prompt


class ScopeTests(unittest.TestCase):
    def test_extended_period_is_explicit_and_context_is_restored(self):
        original = current_prompt()
        token = ACTIVE_SCOPE.set({"date_start": "2026-05-01", "date_end": "2026-10-31"})
        try:
            self.assertIn("2026-05-01", current_prompt())
            self.assertNotEqual(current_prompt(), PROMPT)
        finally:
            ACTIVE_SCOPE.reset(token)
        self.assertEqual(current_prompt(), original)
