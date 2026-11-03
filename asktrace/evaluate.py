"""Versioned routing and grounded-result evaluation; errors are not silently skipped."""

import argparse
import json
import statistics
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from asktrace.agent import run
from asktrace.ingest import digest
from asktrace.query import answer, serialize


def evaluate(root, report, cases_path, provider="baseline", limit=None, interval=0, start_case=1):
    if not 0 <= interval <= 60:
        raise ValueError("interval_must_be_0_to_60")
    corpus = cases_path.read_bytes()
    suite = json.loads(corpus)
    if type(start_case) is not int or not 1 <= start_case <= len(suite["cases"]):
        raise ValueError("invalid_start_case")
    cases = suite["cases"][start_case - 1 :]
    cases = cases[:limit] if limit else cases
    cache = {}

    def tool(root, report, action, identifier):
        key = (action, identifier)
        if key not in cache:
            cache[key] = answer(root, report, action, identifier)
        # Each result is copied; agent minimization cannot mutate another test case.
        return json.loads(json.dumps(cache[key], default=serialize))

    folder = root / "runs" / f"agent-eval-{uuid4()}"
    folder.mkdir(parents=True)
    results = []
    for case in cases:
        if provider == "gemini" and results and results[-1]["actual"]["llm_attempts"]:
            time.sleep(interval)
        result = run(root, report, case["question"], provider, tool=tool)
        action = next(
            (step["plan"]["action"] for step in result["trace"] if step["step"] == "plan"), "refuse"
        )
        expected = case["expected"]
        facts = result.get("evidence", {}).get("coverage", {})
        routing = action == expected["action"] and result["status"] == expected["status"]
        grounding = all(
            facts.get(key) == value for key, value in expected.get("coverage", {}).items()
        )
        if "purchase_id" in expected:
            rows = result.get("evidence", {}).get("result", [])
            grounding = (
                grounding and bool(rows) and rows[0].get("control_id") == expected["purchase_id"]
            )
        results.append(
            {
                "case_id": case["id"],
                "category": case["category"],
                "routing_passed": routing,
                "grounding_passed": grounding,
                "passed": routing and grounding,
                "actual": result,
            }
        )
        # Journal each completed case even if a later call or the process is interrupted.
        case_path = folder / f"case-{start_case + len(results) - 1:03}.json"
        with case_path.open("x", encoding="utf-8") as stream:
            json.dump(results[-1], stream, default=serialize, ensure_ascii=False, indent=2)
            stream.write("\n")
        if result["status"] == "error" and provider == "gemini":
            break  # Preserve quota/provider failure; never fall back to a different provider.
    latencies = [row["actual"]["latency_ms"] for row in results]
    summary = {
        "started_scope": suite["scope"],
        "provider": provider,
        "request_interval_seconds": interval if provider == "gemini" else 0,
        "code_sha256": {
            name: digest((root / "asktrace" / name).read_bytes())
            for name in ("agent.py", "gemini.py", "query.py", "evaluate.py")
            if (root / "asktrace" / name).exists()
        },
        "finished_at": datetime.now(UTC).isoformat(),
        "suite_sha256": digest(corpus),
        "coverage_report_sha256": digest(report.read_bytes()),
        "suite_size": len(suite["cases"]),
        "requested_cases": len(cases),
        "start_case": start_case,
        "unexecuted_requested_cases": len(cases) - len(results),
        "completion": "complete" if len(results) == len(cases) else "interrupted",
        "routing_failures_without_errors": sum(
            not row["routing_passed"] and row["actual"]["status"] != "error" for row in results
        ),
        "executed": len(results),
        "passed": sum(row["passed"] for row in results),
        "errors": sum(row["actual"]["status"] == "error" for row in results),
        "llm_attempts": sum(row["actual"]["llm_attempts"] for row in results),
        "tool_calls": sum(row["actual"]["tool_calls"] for row in results),
        "median_latency_ms": statistics.median(latencies) if latencies else None,
        "latency_note": "Local verified-query cache enabled; not uncached production latency.",
        "cost_currency": None,
        "cost_note": "No billing data available; not assumed zero.",
        "generalization_note": "Curated development suite, not a blind employment benchmark.",
        "results": results,
    }
    with (folder / "evaluation.json").open("x", encoding="utf-8") as stream:
        json.dump(summary, stream, default=serialize, ensure_ascii=False, indent=2)
        stream.write("\n")
    return folder / "evaluation.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coverage", required=True, type=Path)
    parser.add_argument("--cases", type=Path, default=Path("evals/business-v1.json"))
    parser.add_argument("--provider", choices=["baseline", "gemini"], default="baseline")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--interval", type=float, default=6)
    parser.add_argument("--start-case", type=int, default=1)
    args = parser.parse_args()
    try:
        if args.limit is not None and not 1 <= args.limit <= 100:
            raise ValueError("invalid_case_limit")
        path = evaluate(
            Path.cwd(),
            args.coverage,
            args.cases,
            args.provider,
            args.limit,
            args.interval,
            args.start_case,
        )
        result = json.loads(path.read_bytes())
        print(path.relative_to(Path.cwd()))
        print(
            json.dumps(
                {
                    key: result[key]
                    for key in ("provider", "executed", "passed", "errors", "llm_attempts")
                }
            )
        )
        return int(result["passed"] != result["requested_cases"])
    except Exception as error:
        print(f"Evaluation failed: {type(error).__name__}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
