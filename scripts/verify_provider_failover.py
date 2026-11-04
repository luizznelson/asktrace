"""Controlled model-404 injection followed by one real GPT-OSS call and one read-only query."""

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv

from asktrace.agent import run, validate_plan
from asktrace.gemini import ProviderFailure
from asktrace.provider_gateway import call
from asktrace.providers import health, save_health, select
from asktrace.query import serialize


def verify_failover(root):
    load_dotenv(root / ".env", override=False)
    coverage = root / "runs/contracts-resume-c1345679-59ea-49ad-af35-be2cc924ceab/coverage.json"
    network_calls = 0
    with tempfile.TemporaryDirectory(prefix="asktrace-failover-") as directory:
        isolated = Path(directory)
        (isolated / "config").mkdir()
        (isolated / "config/providers.json").write_bytes(
            (root / "config/providers.json").read_bytes()
        )
        # Honor real cooldowns; only the injected model-404 goes into disposable test state.
        save_health(isolated, health(root))

        def transport(_, candidate, question, timeout):
            nonlocal network_calls
            if candidate["id"] == "groq-qwen":
                raise ProviderFailure(404)
            network_calls += 1
            return call(root, candidate, question, timeout)

        def planner(question):
            plan, usage = select(isolated, question, validate_plan, transport=transport)
            for event in usage["provider_events"]:
                if event.get("candidate") == "groq-qwen":
                    event["fault_injected"] = True
            return plan, usage

        answer = run(root, coverage, "Qual é o resumo da cobertura?", "fallback", planner=planner)
    passed = (
        answer["status"] == "answered"
        and answer.get("selected_provider", {}).get("candidate") == "groq-gpt-oss"
        and answer["tool_calls"] == 1
        and network_calls == 1
        and answer["evidence"]["coverage"]["contracts"] == 125
    )
    folder = root / "runs" / f"provider-failover-{uuid4()}"
    folder.mkdir()
    report = {
        "verified_at": datetime.now(UTC).isoformat(),
        "passed": passed,
        "simulation": "First model 404 injected before network; not an observed Groq outage.",
        "actual_network_calls": network_calls,
        "logical_planner_attempts": answer["llm_attempts"],
        "production_health_state_modified": False,
        "result": answer,
    }
    with (folder / "verification.json").open("x", encoding="utf-8") as stream:
        json.dump(report, stream, default=serialize, ensure_ascii=False, indent=2)
        stream.write("\n")
    return folder / "verification.json", passed


def main():
    try:
        path, passed = verify_failover(Path.cwd())
        print(path.relative_to(Path.cwd()))
        print(json.dumps({"passed": passed}))
        return int(not passed)
    except Exception as error:
        print(f"Failover verification failed: {type(error).__name__}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
