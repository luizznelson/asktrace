"""Explicit contingency with bounded attempts, persistent quota cooldown and no SQL access."""

import json
import math
import os
import time
from datetime import datetime
from uuid import uuid4

from dotenv import load_dotenv

from asktrace.gemini import ProviderFailure
from asktrace.ingest import digest
from asktrace.provider_gateway import KEYS, call

MODES = (
    "baseline",
    "gemini",
    "fallback",
    "groq-qwen",
    "groq-gpt-oss",
    "openrouter-qwen",
    "openrouter-nemotron",
    "openrouter-liquid",
    "openrouter-gemma",
    "openrouter-xing",
    "ollama-qwen",
)
REGISTRY = {
    "openrouter-gemma": ("openrouter", "google/gemma-4-26b-a4b-it:free"),
    "openrouter-xing": ("openrouter", "xingchen-agi/xing4.0-29b-a4b:free"),
    "openrouter-liquid": ("openrouter", "liquid/lfm-2.5-2.6b:free"),
    "openrouter-nemotron": ("openrouter", "nvidia/nemotron-3.5-super-vl:free"),
    "groq-qwen": ("groq", "qwen/qwen3.8-27b"),
    "groq-gpt-oss": ("groq", "openai/gpt-oss-20b"),
    "openrouter-qwen": ("openrouter", "qwen/qwen3.8-27b:free"),
    "gemini": ("gemini", "gemini-2.5-flash"),
    "ollama-qwen": ("ollama", "qwen3:4b"),
}
TRANSIENT = {0, 408, 429, 500, 502, 503, 504}


class ContingencyFailure(RuntimeError):
    def __init__(self, events, attempts):
        self.provider_events = events
        self.attempt_count = attempts
        super().__init__("no_usable_provider_or_terminal_failure")


def configuration(root):
    body = (root / "config/providers.json").read_bytes()
    if len(body) > 65536:
        raise ValueError("provider_config_too_large")
    config = json.loads(body)
    if (
        config.get("version") != 1
        or config.get("free_only") is not True
        or type(config.get("max_attempts")) is not int
        or not 1 <= config["max_attempts"] <= 3
        or not 1 <= config["request_timeout_seconds"] <= 20
        or not 1 <= config["planning_budget_seconds"] <= 60
    ):
        raise ValueError("invalid_provider_budget")
    seen = set()
    for candidate in config["candidates"]:
        identifier = candidate["id"]
        if (
            identifier in seen
            or identifier not in REGISTRY
            or (candidate["provider"], candidate["model"]) != REGISTRY[identifier]
            or type(candidate["enabled"]) is not bool
            or set(candidate) != {"id", "provider", "model", "enabled"}
        ):
            raise ValueError("provider_not_in_reviewed_free_catalog")
        seen.add(identifier)
    if not seen:
        raise ValueError("empty_provider_catalog")
    return config, digest(body)


def health_path(root):
    return root / "data/runtime/provider-health.json"


def health(root):
    path = health_path(root)
    state = json.loads(path.read_bytes()) if path.exists() else {}
    # Bootstrap the already observed Gemini daily cooldown, without making another API call.
    for report in (root / "runs").glob("agent-eval-*/evaluation.json"):
        data = json.loads(report.read_bytes())
        if data.get("provider") != "gemini":
            continue
        models = {
            (step.get("usage") or {}).get("model")
            for row in data.get("results", [])
            for step in row["actual"]["trace"]
            if step["step"] == "plan"
        }
        if models != {"gemini-2.5-flash"}:
            continue
        for row in data.get("results", []):
            for step in row["actual"]["trace"]:
                if step.get("provider_http_status") != 429:
                    continue
                delay = (step.get("provider_limits") or {}).get("retry_after_seconds")
                if type(delay) in (int, float) and math.isfinite(delay) and delay >= 0:
                    until = datetime.fromisoformat(data["finished_at"]).timestamp() + delay
                    previous = state.get("provider:gemini", {}).get("not_before", 0)
                    if until > previous:
                        state["provider:gemini"] = {"not_before": until, "reason": "recorded_429"}
    return state


def save_health(root, state):
    path = health_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".health-{uuid4()}.json")
    temporary.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def select(
    root,
    question,
    validator,
    candidate_id=None,
    transport=call,
    clock=time.time,
    monotonic=time.monotonic,
):
    load_dotenv(root / ".env", override=False)
    config, checksum = configuration(root)
    state = health(root)
    save_health(root, state)
    events, attempts = [], 0
    deadline = monotonic() + config["planning_budget_seconds"]
    candidates = [
        row for row in config["candidates"] if candidate_id is None or row["id"] == candidate_id
    ]
    for candidate in candidates:
        identity = {
            "candidate": candidate["id"],
            "provider": candidate["provider"],
            "model": candidate["model"],
        }
        provider = candidate["provider"]
        if not candidate["enabled"]:
            events.append({**identity, "outcome": "skipped", "reason": "disabled"})
            continue
        if provider in KEYS and not os.environ.get(KEYS[provider]):
            events.append({**identity, "outcome": "skipped", "reason": "missing_key"})
            continue
        cooldown = max(
            state.get("provider:" + provider, {}).get("not_before", 0),
            state.get("candidate:" + candidate["id"], {}).get("not_before", 0),
        )
        if cooldown > clock():
            events.append(
                {
                    **identity,
                    "outcome": "skipped",
                    "reason": "cooldown",
                    "not_before_epoch": cooldown,
                }
            )
            continue
        remaining = deadline - monotonic()
        if attempts >= config["max_attempts"] or remaining <= 0:
            events.append({"outcome": "stopped", "reason": "planning_budget"})
            break
        attempts += 1
        try:
            proposal, usage = transport(
                root, candidate, question, min(config["request_timeout_seconds"], remaining)
            )
            if monotonic() > deadline:
                raise TimeoutError("planning_budget_exceeded")
            proposal = validator(proposal, question)
        except ProviderFailure as error:
            status = error.http_status
            events.append(
                {
                    **identity,
                    "outcome": "failed",
                    "http_status": status,
                    "provider_limits": error.limits,
                }
            )
            if status not in TRANSIENT and status != 404:
                raise ContingencyFailure(events, attempts) from None
            delay = error.limits.get("retry_after_seconds", 600 if status == 429 else 30)
            if type(delay) not in (int, float) or not math.isfinite(delay) or delay < 0:
                delay = 600
            # Shared provider quotas are not multiplied by rotating its model IDs.
            key = "candidate:" + candidate["id"] if status == 404 else "provider:" + provider
            state[key] = {"not_before": clock() + max(1, delay), "reason": f"http_{status}"}
            save_health(root, state)
            continue
        except Exception as error:
            events.append(
                {**identity, "outcome": "terminal_error", "error_type": type(error).__name__}
            )
            raise ContingencyFailure(events, attempts) from None
        events.append({**identity, "outcome": "selected"})
        return proposal, {
            **usage,
            "candidate": candidate["id"],
            "provider": provider,
            "model": candidate["model"],
            "attempt_count": attempts,
            "provider_config_sha256": checksum,
            "provider_events": events,
            "fallback_used": candidate_id is None and candidate != candidates[0],
        }
    raise ContingencyFailure(events, attempts)
