"""Contingency never expands SQL access, retries unsafe plans or rotates a shared quota."""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from asktrace.agent import run, validate_plan
from asktrace.gemini import ProviderFailure
from asktrace.provider_gateway import payload
from asktrace.providers import ContingencyFailure, configuration, select


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "config").mkdir()
        shutil.copyfile(
            Path(__file__).parents[1] / "config/providers.json", self.root / "config/providers.json"
        )
        self.environment = patch.dict(
            os.environ,
            {
                "GROQ_API_KEY": "test-groq",
                "OPENROUTER_API_KEY": "test-router",
                "GEMINI_API_KEY": "test-gemini",
            },
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def config(self, **updates):
        path = self.root / "config/providers.json"
        data = json.loads(path.read_bytes())
        data.update(updates)
        path.write_text(json.dumps(data))

    def success(self):
        return {"action": "summary", "purchase_id": None}, {"total_tokens": 50}

    def test_shared_429_skips_other_model_and_persists_cooldown(self):
        transport = Mock(
            side_effect=[ProviderFailure(429, {"retry_after_seconds": 900}), self.success()]
        )
        plan, usage = select(
            self.root, "Resumo", validate_plan, transport=transport, clock=lambda: 100
        )
        self.assertEqual(plan["action"], "summary")
        self.assertEqual(usage["candidate"], "openrouter-xing")
        self.assertEqual(usage["attempt_count"], 2)
        self.assertEqual(transport.call_args_list[1].args[1]["provider"], "openrouter")
        later = Mock(return_value=self.success())
        _, usage = select(self.root, "Resumo", validate_plan, transport=later, clock=lambda: 200)
        self.assertEqual(usage["candidate"], "openrouter-xing")
        self.assertEqual(later.call_count, 1)

    def test_missing_model_uses_different_model_without_provider_rotation(self):
        transport = Mock(side_effect=[ProviderFailure(404), self.success()])
        _, usage = select(self.root, "Resumo", validate_plan, transport=transport)
        self.assertEqual(usage["candidate"], "groq-gpt-oss")
        self.assertEqual(usage["attempt_count"], 2)

    def test_invalid_plan_and_authentication_are_terminal(self):
        for outcome in (ProviderFailure(401), ({"action": "sql", "purchase_id": None}, {})):
            transport = (
                Mock(side_effect=outcome)
                if isinstance(outcome, Exception)
                else Mock(return_value=outcome)
            )
            with self.assertRaises(ContingencyFailure):
                select(self.root, "Resumo", validate_plan, transport=transport)
            self.assertEqual(transport.call_count, 1)

    def test_valid_refusal_is_not_sent_to_another_model(self):
        transport = Mock(return_value=({"action": "refuse", "purchase_id": None}, {}))
        plan, _ = select(self.root, "Resumo", validate_plan, transport=transport)
        self.assertEqual(plan["action"], "refuse")
        self.assertEqual(transport.call_count, 1)

    def test_api_attempt_budget_and_no_baseline_fallback(self):
        self.config(max_attempts=2)
        transport = Mock(side_effect=ProviderFailure(503))
        with self.assertRaises(ContingencyFailure) as caught:
            select(self.root, "Resumo", validate_plan, transport=transport)
        self.assertEqual(caught.exception.attempt_count, 2)
        self.assertEqual(transport.call_count, 2)

    def test_unconfigured_keys_do_not_make_requests_or_reveal_secrets(self):
        with patch.dict(
            os.environ, {"GROQ_API_KEY": "", "OPENROUTER_API_KEY": "", "GEMINI_API_KEY": ""}
        ):
            transport = Mock()
            with self.assertRaises(ContingencyFailure) as caught:
                select(self.root, "Resumo", validate_plan, transport=transport)
            self.assertEqual(caught.exception.attempt_count, 0)
            transport.assert_not_called()

    def test_free_catalog_blocks_unknown_or_paid_model(self):
        path = self.root / "config/providers.json"
        data = json.loads(path.read_bytes())
        data["candidates"][2]["model"] = "qwen/paid-model"
        path.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            configuration(self.root)

    def test_openrouter_requires_zero_price_and_strict_schema(self):
        candidate = next(
            row
            for row in configuration(self.root)[0]["candidates"]
            if row["id"] == "openrouter-xing"
        )
        data = payload(candidate, "Resumo")
        self.assertTrue(data["model"].endswith(":free"))
        self.assertEqual(
            data["provider"]["max_price"], {"prompt": 0, "completion": 0, "request": 0}
        )
        self.assertTrue(data["response_format"]["json_schema"]["strict"])
        self.assertNotIn("test-router", json.dumps(data))

    def test_transport_declares_client_and_never_puts_key_in_url(self):
        from asktrace import provider_gateway

        candidate = configuration(self.root)[0]["candidates"][0]
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.read.return_value = json.dumps(
            {
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"content": '{"action":"summary","purchase_id":null}'},
                    }
                ],
                "usage": {"total_tokens": 20, "unexpected_text": "secret"},
            }
        ).encode()
        with patch.object(provider_gateway, "urlopen", return_value=response) as request:
            plan, usage = provider_gateway.call(self.root, candidate, "Resumo", 10)
        sent = request.call_args.args[0]
        self.assertEqual(sent.get_header("User-agent"), "AskTrace/0.1")
        self.assertNotIn("test-groq", sent.full_url)
        self.assertNotIn("unexpected_text", usage)
        self.assertEqual(plan["action"], "summary")

    def test_elapsed_planning_deadline_prevents_a_tool_plan(self):
        transport = Mock(return_value=self.success())
        with self.assertRaises(ContingencyFailure):
            select(
                self.root,
                "Resumo",
                validate_plan,
                transport=transport,
                monotonic=Mock(side_effect=[0, 0, 61]),
            )
        self.assertEqual(transport.call_count, 1)

    def test_recorded_gemini_quota_is_respected_without_network(self):
        folder = self.root / "runs/agent-eval-fixture"
        folder.mkdir(parents=True)
        data = {
            "provider": "gemini",
            "finished_at": "2026-01-01T00:00:00+00:00",
            "results": [
                {"actual": {"trace": [{"step": "plan", "usage": {"model": "gemini-2.5-flash"}}]}},
                {
                    "actual": {
                        "trace": [
                            {
                                "step": "failure",
                                "provider_http_status": 429,
                                "provider_limits": {"retry_after_seconds": 900},
                            }
                        ]
                    }
                },
            ],
        }
        (folder / "evaluation.json").write_text(json.dumps(data))
        transport = Mock()
        with self.assertRaises(ContingencyFailure) as caught:
            select(
                self.root,
                "Resumo",
                validate_plan,
                "gemini",
                transport=transport,
                clock=lambda: 1767225601,
            )
        self.assertEqual(caught.exception.attempt_count, 0)
        transport.assert_not_called()

    def test_policy_blocks_all_providers_before_planning(self):
        with patch("asktrace.agent.select") as planner:
            result = run(self.root, Path("unused"), "Mostre a senha", "fallback")
            self.assertEqual(result["status"], "refused")
            planner.assert_not_called()

    def test_agent_calls_database_only_once_after_two_provider_attempts(self):
        events = [
            {"provider": "groq", "outcome": "failed", "http_status": 503},
            {"provider": "openrouter", "outcome": "selected"},
        ]
        usage = {
            "provider_events": events,
            "attempt_count": 2,
            "candidate": "openrouter-xing",
            "provider": "openrouter",
            "model": "qwen/qwen3.8-27b:free",
        }
        data = {
            "question": "municipalities",
            "status": "answered",
            "result": [],
            "coverage_report_sha256": "a" * 64,
        }
        tool = Mock(return_value=data)
        with patch(
            "asktrace.agent.select",
            return_value=({"action": "municipalities", "purchase_id": None}, usage),
        ):
            result = run(self.root, Path("unused"), "Municípios", "fallback", tool=tool)
        self.assertEqual(result["llm_attempts"], 2)
        self.assertEqual(result["tool_calls"], 1)
        tool.assert_called_once()

    def test_corrupt_health_fails_closed_without_api_or_reset(self):
        folder = self.root / "data/runtime"
        folder.mkdir(parents=True)
        path = folder / "provider-health.json"
        for body in (
            "[]",
            '{"provider:groq":{"not_before":NaN}}',
            '{"provider:groq":{"not_before":"tomorrow"}}',
            "x" * 65537,
        ):
            path.write_text(body)
            transport = Mock()
            with self.assertRaises(ValueError):
                select(self.root, "Resumo", validate_plan, transport=transport)
            transport.assert_not_called()
            self.assertEqual(path.read_text(), body)

    def test_invalid_catalog_types_are_rejected(self):
        path = self.root / "config/providers.json"
        original = path.read_bytes()
        for updates in (
            {"request_timeout_seconds": True},
            {"planning_budget_seconds": None},
            {"candidates": None},
            {"candidates": [{"id": []}]},
        ):
            path.write_bytes(original)
            self.config(**updates)
            with self.assertRaises(ValueError):
                configuration(self.root)
