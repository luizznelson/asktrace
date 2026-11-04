"""Verify the expanded corpus locally; --live opts into three bounded AI smoke cases."""

import argparse
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from asktrace.agent import run
from asktrace.evaluate import evaluate
from asktrace.providers import availability
from asktrace.query import serialize


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    root = Path.cwd()
    config = json.loads((root / "config/datasets.json").read_bytes())
    coverage = root / next(row["coverage"] for row in config["datasets"] if row["id"] == "expanded")
    corpus = root / "evals/routing-expanded-v3.json"
    evaluated = evaluate(root, coverage, corpus, "baseline")
    evaluation = json.loads(evaluated.read_bytes())
    assert evaluation["executed"] == 12 and evaluation["passed"] == 12
    print("Expanded baseline corpus: 12/12; zero external AI calls.", flush=True)
    folder = root / "runs" / ("analytics-verification-" + str(uuid4()))
    folder.mkdir()
    result = {
        "started_at": datetime.now(UTC).isoformat(),
        "baseline_evaluation": evaluated.relative_to(root).as_posix(),
        "baseline_passed": 12,
        "live_requested": args.live,
        "live_cases": [],
        "note": "Author-curated cases. AI smoke is not a full-model quality benchmark.",
    }
    if args.live:
        cases = json.loads(corpus.read_bytes())["cases"]
        for index in (0, 3, 6):
            case = cases[index]
            if not availability(root)["can_attempt_ai"]:
                result["live_cases"].append(
                    {
                        "action": case["expected"]["action"],
                        "status": "not_attempted",
                        "reason": "no_available_candidate",
                    }
                )
                continue
            answer = run(root, coverage, case["question"], "fallback")
            name = f"live-{index + 1:02}.json"
            (folder / name).write_text(
                json.dumps(answer, default=serialize, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            actual = answer.get("evidence", {}).get("question")
            passed = answer["status"] == "answered" and actual == case["expected"]["action"]
            result["live_cases"].append(
                {
                    "action": case["expected"]["action"],
                    "status": answer["status"],
                    "passed": passed,
                    "llm_attempts": answer["llm_attempts"],
                    "tool_calls": answer["tool_calls"],
                    "selected_provider": answer.get("selected_provider"),
                    "evidence": name,
                }
            )
            print(
                "AI smoke:",
                case["expected"]["action"],
                answer["status"],
                "passed=" + str(passed),
                flush=True,
            )
            if index != 6 and answer["llm_attempts"]:
                time.sleep(6)
    result["finished_at"] = datetime.now(UTC).isoformat()
    (folder / "verification.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    print("Analytics verification:", folder.name, flush=True)


if __name__ == "__main__":
    main()
