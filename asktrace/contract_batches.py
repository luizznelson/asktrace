"""Resume bounded contract batches using verified, successfully loaded snapshots."""

import json
from datetime import UTC, datetime
from uuid import uuid4

from asktrace.contracts import collect, load, select_purchases, verify, write_json
from asktrace.ingest import digest


def inventory(root, parent, loader=load):
    parent_manifest, parent_hash, _ = select_purchases(root, parent, 1)
    population = parent_manifest["quality"]["normalized_records"]
    ordered = []
    for offset in range(0, population, 100):
        _, _, rows = select_purchases(root, parent, 100, offset)
        ordered.extend(row["purchase_id"] for row in rows)
    candidates = []
    for path in sorted((root / "runs").glob("contracts-*/manifest.json")):
        manifest = json.loads(path.read_bytes())
        if (
            manifest.get("parent_run_id") == parent_manifest["run_id"]
            and manifest.get("status") == "pilot_complete"
        ):
            verified, checksum = verify(root, path)
            if verified["parent_manifest_sha256"] != parent_hash:
                raise ValueError("parent_changed")
            loader(root, path)
            candidates.append((verified, path, checksum))
    covered, snapshots = {}, []
    for manifest, path, checksum in sorted(
        candidates, key=lambda item: (item[0]["finished_at"], item[0]["run_id"])
    ):
        snapshots.append({"path": path.relative_to(root).as_posix(), "sha256": checksum})
        for request in manifest["requests"]:
            covered[request["purchase_id"]] = {
                "outcome": request["outcome"],
                "run_id": manifest["run_id"],
                "contracts": [
                    row["contract_id"]
                    for row in manifest["contracts"]
                    if row["purchase_id"] == request["purchase_id"]
                ],
            }
    if not set(covered).issubset(ordered):
        raise ValueError("coverage_outside_eligible_population")
    return ordered, covered, snapshots, parent_manifest


def next_batch(ordered, covered):
    for start, identifier in enumerate(ordered):
        if identifier not in covered:
            end = start
            while end < len(ordered) and end - start < 100 and ordered[end] not in covered:
                end += 1
            return start, end - start
    return None


def resume(root, parent, max_batches=1, collector=collect, loader=load):
    if type(max_batches) is not int or not 1 <= max_batches <= 20:
        raise ValueError("max_batches_must_be_1_to_20")
    folder = root / "runs" / f"contracts-resume-{uuid4()}"
    folder.mkdir(parents=True)
    write_json(
        folder / "plan.json",
        {
            "started_at": datetime.now(UTC).isoformat(),
            "parent_sha256": digest(parent.read_bytes()),
            "max_batches": max_batches,
        },
    )
    events = []
    for _ in range(max_batches):
        ordered, covered, _, _ = inventory(root, parent, loader)
        batch = next_batch(ordered, covered)
        if batch is None:
            break
        offset, count = batch
        path = collector(root, parent, limit=count, offset=offset)
        manifest = json.loads(path.read_bytes())
        event = {
            "path": path.relative_to(root).as_posix(),
            "status": manifest["status"],
            "offset": offset,
            "selected": count,
        }
        if manifest["status"] == "pilot_complete":
            event["load_result"] = loader(root, path)
        events.append(event)
        write_json(folder / f"batch-{len(events):03}.json", event)
        if manifest["status"] != "pilot_complete":
            break
    ordered, covered, snapshots, parent_manifest = inventory(root, parent, loader)
    contracts = {identifier for row in covered.values() for identifier in row["contracts"]}
    report = {
        "finished_at": datetime.now(UTC).isoformat(),
        "parent_run_id": parent_manifest["run_id"],
        "population": parent_manifest["quality"]["normalized_records"],
        "eligible": len(ordered),
        "covered_distinct_purchases": len(covered),
        "remaining_eligible": len(ordered) - len(covered),
        "excluded_purchases": parent_manifest["contract_locator_exclusions"],
        "purchases_with_contracts": sum(
            row["outcome"] == "with_contracts" for row in covered.values()
        ),
        "purchases_none_returned": sum(
            row["outcome"] == "none_returned" for row in covered.values()
        ),
        "distinct_contracts": len(contracts),
        "snapshots": snapshots,
        "coverage": covered,
        "events": events,
        "status": "needs_review"
        if any(event["status"] != "pilot_complete" for event in events)
        else "bounded_run_complete",
    }
    write_json(folder / "coverage.json", report)
    return folder / "coverage.json"
