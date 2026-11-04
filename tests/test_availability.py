"""Provider cooldown must not be presented as a database failure or trigger hidden fallback."""

import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from asktrace.agent import run
from asktrace.providers import ContingencyFailure


class AvailabilityTests(unittest.TestCase):
    def test_cooldown_reports_no_database_query_and_allows_explicit_local_retry(self):
        events = [
            {
                "candidate": "groq-qwen",
                "outcome": "skipped",
                "reason": "cooldown",
                "not_before_epoch": 2000000000,
            },
            {
                "candidate": "gemini",
                "outcome": "skipped",
                "reason": "cooldown",
                "not_before_epoch": 2100000000,
            },
        ]
        tool = Mock()
        with patch("asktrace.agent.select", side_effect=ContingencyFailure(events, 0)):
            result = run(Path.cwd(), Path("unused"), "Resumo", "fallback", tool=tool)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["llm_attempts"], 0)
        self.assertEqual(result["availability"]["component"], "ai_planner")
        self.assertEqual(result["availability"]["reason"], "cooldown")
        self.assertEqual(result["availability"]["next_candidate_retry_epoch"], 2000000000)
        self.assertFalse(result["availability"]["database_checked"])
        tool.assert_not_called()

    def test_database_failure_is_not_labeled_provider_cooldown(self):
        tool = Mock(side_effect=RuntimeError("private connection details"))
        result = run(Path.cwd(), Path("unused"), "Resumo da cobertura", "baseline", tool=tool)
        self.assertEqual(result["status"], "error")
        self.assertNotIn("availability", result)
        self.assertEqual(result["tool_calls"], 1)
