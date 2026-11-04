"""Verify a consolidated report against PostgreSQL before selecting it in the application."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from asktrace import contracts, query
from asktrace.ingest import digest


def publish(root, report):
    root = root.resolve()
    report = (root / report).resolve()
    if not report.is_relative_to(root / "runs"):
        raise ValueError("report_outside_runs")
    data = json.loads(report.read_bytes())
    if data["parent_run_id"] != "74d68096-1e27-451d-b423-f8cded554d54":
        raise ValueError("unexpected_parent_snapshot")
    # Integrity and actual SELECT results must agree before the application changes.
    result = query.answer(root, report, "summary")
    counts = result["coverage"]
    if (
        counts["covered_purchases"] != data["covered_distinct_purchases"]
        or counts["contracts"] != data["distinct_contracts"]
        or counts["purchases_with_contracts"] != data["purchases_with_contracts"]
        or counts["none_returned"] != data["purchases_none_returned"]
        or counts["purchases"] != data["population"]
        or data["eligible"] != counts["covered_purchases"] + data["remaining_eligible"]
        or data["population"] != data["eligible"] + len(data["excluded_purchases"])
    ):
        raise ValueError("coverage_totals_do_not_match_database")
    repeat = [
        {"path": item["path"], "load_result": contracts.load(root, root / item["path"])}
        for item in data["snapshots"]
    ]
    if any(row["load_result"] != "already_loaded" for row in repeat):
        raise ValueError("unexpected_non_idempotent_load")
    checks = []
    for outcome in ("with_contracts", "none_returned"):
        identifier = next(
            (key for key, value in data["coverage"].items() if value["outcome"] == outcome), None
        )
        if identifier:
            purchase = query.answer(root, report, "purchase", identifier)["result"][0]
            assert purchase["outcome"] == outcome
            assert len(purchase["contracts"] or []) == len(
                data["coverage"][identifier]["contracts"]
            )
            checks.append(
                {
                    "purchase_id": identifier,
                    "outcome": outcome,
                    "contracts": len(purchase["contracts"] or []),
                }
            )
    config_path = root / "config/datasets.json"
    before = config_path.read_bytes()
    config = json.loads(before)
    for item in config["datasets"]:
        if item["id"] == "expanded":
            previous = item["coverage"]
            item["coverage"] = report.relative_to(root).as_posix()
            break
    else:
        raise ValueError("expanded_dataset_not_registered")
    after = (json.dumps(config, indent=2, ensure_ascii=False) + "\n").encode()
    folder = root / "runs" / ("contracts-publication-" + str(uuid4()))
    folder.mkdir()
    verification = {
        "verified_at": datetime.now(UTC).isoformat(),
        "coverage_report": report.relative_to(root).as_posix(),
        "coverage_sha256": result["coverage_report_sha256"],
        "database_counts": counts,
        "eligible": data["eligible"],
        "remaining_eligible": data["remaining_eligible"],
        "excluded_purchases": data["excluded_purchases"],
        "idempotent_loads": repeat,
        "purchase_checks": checks,
        "previous_coverage": previous,
        "config_before_sha256": digest(before),
        "config_after_sha256": digest(after),
        "external_api_calls": 0,
    }
    (folder / "verification.json").write_text(
        json.dumps(verification, default=query.serialize, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temporary = config_path.with_suffix(".tmp")
    temporary.write_bytes(after)
    temporary.replace(config_path)
    print(
        json.dumps(
            {
                "publication": folder.relative_to(root).as_posix(),
                "counts": counts,
                "remaining": data["remaining_eligible"],
                "excluded": len(data["excluded_purchases"]),
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    return folder / "verification.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    publish(Path.cwd(), args.report)


if __name__ == "__main__":
    main()
