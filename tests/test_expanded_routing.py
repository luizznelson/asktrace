"""Expanded routes share a catalog and preserve one-query and refusal boundaries."""

import unittest
from pathlib import Path
from unittest.mock import Mock

from asktrace import agent, gemini, provider_gateway
from asktrace.planning import PLAN_ACTIONS
from asktrace.query import QUERIES


class ExpandedRoutingTests(unittest.TestCase):
    def test_schemas_and_query_catalog_agree(self):
        self.assertEqual(set(PLAN_ACTIONS), set(QUERIES) | {"refuse"})
        self.assertEqual(gemini.SCHEMA["properties"]["action"]["enum"], list(PLAN_ACTIONS))
        self.assertEqual(
            provider_gateway.SCHEMA["properties"]["action"]["enum"], list(PLAN_ACTIONS)
        )

    def test_new_routes_are_validated_and_use_one_query(self):
        for action, question in (
            ("monthly", "Como evoluíram as compras por mês?"),
            ("organizations", "Quais órgãos têm mais compras?"),
            ("quality", "Como está a qualidade e o preenchimento dos dados?"),
        ):
            tool = Mock(
                return_value={
                    "question": action,
                    "status": "answered",
                    "result": [],
                    "coverage_report_sha256": "a" * 64,
                }
            )
            result = agent.run(Path.cwd(), Path("unused"), question, tool=tool)
            self.assertEqual(result["status"], "answered")
            self.assertEqual(result["tool_calls"], 1)
            self.assertEqual(result["llm_attempts"], 0)
            self.assertEqual(tool.call_args.args[2], action)

    def test_combined_dimensions_are_not_silently_dropped(self):
        for question in ("Compras por mês e órgão", "Compras por mês e município"):
            tool = Mock()
            result = agent.run(Path.cwd(), Path("unused"), question, tool=tool)
            self.assertEqual(result["status"], "refused")
            tool.assert_not_called()
