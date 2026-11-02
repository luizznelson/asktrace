"""Collect a reproducible pilot of contracts linked to a verified purchase snapshot."""

import argparse
import json
import os
import time
from collections import Counter
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import UUID, uuid4

from asktrace.database import verified_snapshot
from asktrace.ingest import MAX_BODY, amount, decode, digest

BASE = "https://pncp.gov.br/api/pncp/v1/orgaos"


def fetch(url):
    for attempt in range(3):
        try:
            with urlopen(
                Request(url, headers={"Accept": "application/json"}), timeout=30
            ) as response:
                body = response.read(MAX_BODY + 1)
                if len(body) > MAX_BODY:
                    raise ValueError("response_too_large")
                return body, response.status
        except HTTPError as error:
            if error.code not in {429, 500, 502, 503, 504} or attempt == 2:
                return error.read(MAX_BODY + 1), error.code
            retry = error.headers.get("Retry-After", "")
            time.sleep(min(30, int(retry)) if retry.isdecimal() else 2**attempt)
        except URLError, TimeoutError:
            if attempt == 2:
                return b"", 0
            time.sleep(2**attempt)
    raise RuntimeError("unreachable")


def request_url(locator):
    return f"{BASE}/{locator['cnpj']}/contratos/contratacao/{locator['year']}/{locator['sequence']}"


def select_purchases(root, parent, limit):
    manifest, purchases, parent_hash = verified_snapshot(root, parent)
    if manifest["mode"] != "live" or not 1 <= limit <= 100:
        raise ValueError("live_snapshot_and_limit_1_to_100_required")
    sources = {}
    for page in manifest["pages"]:
        sources[page["body_sha256"]] = decode((root / page["relative_path"]).read_bytes())["data"]
    # Round-robin months; within each month order by control ID. No outcome-based selection.
    groups = {}
    for row in sorted(purchases, key=lambda row: row["control_id"]):
        groups.setdefault(row["publication_date"][:7], []).append(row)
    selected = []
    while groups and len(selected) < limit:
        for month in sorted(list(groups)):
            row = groups[month].pop(0)
            raw = sources[row["source_body_sha256"]][row["source_record_index"]]
            year, sequence = raw.get("anoCompra"), raw.get("sequencialCompra")
            if (
                raw.get("numeroControlePNCP") != row["control_id"]
                or type(year) is not int
                or type(sequence) is not int
                or not 1900 <= year <= 9999
                or sequence < 1
            ):
                raise ValueError("invalid_purchase_locator")
            selected.append(
                {
                    "purchase_id": row["control_id"],
                    "cnpj": row["org_cnpj"],
                    "year": year,
                    "sequence": sequence,
                }
            )
            if not groups[month]:
                del groups[month]
            if len(selected) == limit:
                break
    return manifest, parent_hash, selected


def parse(body, status, purchase_id):
    if status == 204 and not body:
        return [], "none_returned"
    if status != 200:
        return [], "request_failed"

    def reject(value):
        raise ValueError("nonfinite_json")

    data = json.loads(body, parse_float=Decimal, parse_constant=reject)
    if not isinstance(data, list):
        raise ValueError("unexpected_response_shape")
    rows, seen = [], set()
    for index, raw in enumerate(data):
        if not isinstance(raw, dict):
            raise ValueError("invalid_contract")
        link = raw.get("numeroControlePNCPCompra", raw.get("numeroControlePncpCompra"))
        identifier = raw.get("numeroControlePNCP")
        if link != purchase_id or not isinstance(identifier, str) or not identifier.strip():
            raise ValueError("contract_link_mismatch")
        if identifier in seen:
            raise ValueError("duplicate_contract")
        seen.add(identifier)
        values = {}
        for source, target in (("valorInicial", "initial_value"), ("valorGlobal", "global_value")):
            value, issue = amount(raw.get(source))
            if issue == "invalid":
                raise ValueError("invalid_contract_amount")
            values[target] = value
        # Supplier identifiers/names and free text are deliberately excluded from public evidence.
        rows.append(
            {
                "contract_id": identifier,
                "purchase_id": purchase_id,
                "source_record_index": index,
                **values,
            }
        )
    return rows, "with_contracts" if rows else "none_returned"


def write_json(path, data):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def collect(root, parent, limit=12, transport=fetch, interval=1):
    parent_manifest, parent_hash, selected = select_purchases(root, parent, limit)
    run_id = str(uuid4())
    folder = root / "runs" / f"contracts-{run_id}"
    raw_folder = root / "data/raw" / run_id
    folder.mkdir(parents=True)
    raw_folder.mkdir(parents=True)
    manifest = {
        "schema_version": 1,
        "run_id": run_id,
        "parent_run_id": parent_manifest["run_id"],
        "parent_manifest_sha256": parent_hash,
        "started_at": datetime.now(UTC).isoformat(),
        "status": "running",
        "selection": "round_robin_publication_month_then_control_id_v1",
        "population": parent_manifest["quality"]["normalized_records"],
        "selected": selected,
        "requests": [],
        "contracts": [],
    }
    interrupted = False
    try:
        for index, locator in enumerate(selected):
            url = request_url(locator)
            evidence = {
                "purchase_id": locator["purchase_id"],
                "url": url,
                "fetched_at": datetime.now(UTC).isoformat(),
            }
            try:
                body, status = transport(url)
                path = raw_folder / f"request-{index:04}.json"
                path.write_bytes(body)
                evidence.update(
                    http_status=status,
                    relative_path=path.relative_to(root).as_posix(),
                    body_sha256=digest(body),
                )
                rows, outcome = parse(body, status, locator["purchase_id"])
                evidence.update(outcome=outcome, contracts_count=len(rows))
                manifest["contracts"].extend(rows)
            except ValueError, OSError, RuntimeError:
                evidence.update(outcome="invalid_response", contracts_count=0)
            manifest["requests"].append(evidence)
            if interval:
                time.sleep(interval)
    except KeyboardInterrupt:
        interrupted = True
    counts = Counter(request["outcome"] for request in manifest["requests"])
    manifest["quality"] = {
        "selected": len(selected),
        "attempted": len(manifest["requests"]),
        **dict(counts),
        "contracts": len(manifest["contracts"]),
    }
    manifest["status"] = (
        "interrupted"
        if interrupted
        else (
            "pilot_complete"
            if not (counts["request_failed"] or counts["invalid_response"])
            else "needs_review"
        )
    )
    manifest["finished_at"] = datetime.now(UTC).isoformat()
    write_json(folder / "manifest.json", manifest)
    return folder / "manifest.json"


def verify(root, path):
    body = path.read_bytes()
    manifest = json.loads(body)
    UUID(manifest["run_id"])
    UUID(manifest["parent_run_id"])
    if manifest["status"] != "pilot_complete":
        raise ValueError("only_complete_pilots_can_be_loaded")
    parent = root / "runs" / f"pncp-{manifest['parent_run_id']}" / "manifest.json"
    _, parent_hash, selected = select_purchases(root, parent, len(manifest["selected"]))
    if parent_hash != manifest["parent_manifest_sha256"] or selected != manifest["selected"]:
        raise ValueError("parent_or_selection_mismatch")
    if len(manifest["requests"]) != len(selected):
        raise ValueError("incomplete_coverage")
    rows = []
    for locator, request in zip(selected, manifest["requests"], strict=True):
        expected_url = request_url(locator)
        if request["purchase_id"] != locator["purchase_id"] or request["url"] != expected_url:
            raise ValueError("request_locator_mismatch")
        source = (root / request["relative_path"]).resolve()
        if not source.is_relative_to((root / "data/raw" / manifest["run_id"]).resolve()):
            raise ValueError("unsafe_source_path")
        raw = source.read_bytes()
        if digest(raw) != request["body_sha256"]:
            raise ValueError("source_hash_mismatch")
        parsed, outcome = parse(raw, request["http_status"], request["purchase_id"])
        if outcome != request["outcome"] or len(parsed) != request["contracts_count"]:
            raise ValueError("outcome_mismatch")
        rows.extend(parsed)
    counts = Counter(request["outcome"] for request in manifest["requests"])
    quality = {
        "selected": len(selected),
        "attempted": len(selected),
        **dict(counts),
        "contracts": len(rows),
    }
    if manifest["quality"] != quality:
        raise ValueError("quality_mismatch")
    if rows != manifest["contracts"]:
        raise ValueError("normalized_contracts_mismatch")
    return manifest, digest(body)


def load(root, path):
    import psycopg
    from dotenv import load_dotenv
    from psycopg.types.json import Jsonb

    manifest, checksum = verify(root, path)
    load_dotenv(root / ".env", override=False)
    with psycopg.connect(
        host="127.0.0.1",
        port=15432,
        user="asktrace",
        dbname=os.environ.get("ASKTRACE_DATABASE_NAME", "asktrace"),
        password=os.environ["POSTGRES_PASSWORD"],
        connect_timeout=10,
    ) as connection:
        connection.execute("SELECT pg_advisory_xact_lock(717426001)")
        connection.execute((root / "sql/003_contracts.sql").read_text(encoding="utf-8"))
        parent = connection.execute(
            "SELECT manifest_sha256 FROM asktrace.ingestion_runs "
            "WHERE run_id=%s AND status='complete'",
            (manifest["parent_run_id"],),
        ).fetchone()
        if not parent or parent[0] != manifest["parent_manifest_sha256"]:
            raise ValueError("parent_not_loaded_or_changed")
        existing = connection.execute(
            "SELECT manifest_sha256 FROM asktrace.contract_runs WHERE run_id=%s",
            (manifest["run_id"],),
        ).fetchone()
        if existing:
            if existing[0] != checksum:
                raise ValueError("existing_run_changed")
            return "already_loaded"
        connection.execute(
            "INSERT INTO asktrace.contract_runs VALUES (%s,%s,%s,%s)",
            (manifest["run_id"], manifest["parent_run_id"], checksum, Jsonb(manifest["quality"])),
        )
        for request in manifest["requests"]:
            connection.execute(
                "INSERT INTO asktrace.contract_coverage VALUES (%s,%s,%s,%s,%s,%s)",
                (
                    manifest["run_id"],
                    manifest["parent_run_id"],
                    request["purchase_id"],
                    request["outcome"],
                    request["body_sha256"],
                    request["contracts_count"],
                ),
            )
        for row in manifest["contracts"]:
            connection.execute(
                "INSERT INTO asktrace.contracts VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (
                    manifest["run_id"],
                    row["contract_id"],
                    manifest["parent_run_id"],
                    row["purchase_id"],
                    row["initial_value"],
                    row["global_value"],
                    row["source_record_index"],
                ),
            )
    return "loaded"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    acquisition = sub.add_parser("collect")
    acquisition.add_argument("parent", type=Path)
    acquisition.add_argument("--limit", type=int, default=12)
    loading = sub.add_parser("load")
    loading.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "collect":
            path = collect(Path.cwd(), args.parent, args.limit)
            print(path.relative_to(Path.cwd()))
            return 0 if json.loads(path.read_bytes())["status"] == "pilot_complete" else 1
        print(load(Path.cwd(), args.manifest))
        return 0
    except Exception as error:
        print(f"Contract operation failed: {type(error).__name__}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
