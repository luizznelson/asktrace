"""Collect a reproducible pilot of contracts linked to a verified purchase snapshot."""

import argparse
import json
import os
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import UUID, uuid4

from asktrace.database import verified_snapshot
from asktrace.evidence import read_evidence
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


def request_url(locator, page=1):
    return (
        f"{BASE}/{locator['cnpj']}/contratos/contratacao/"
        f"{locator['year']}/{locator['sequence']}?pagina={page}&tamanhoPagina=50"
    )


def select_purchases(root, parent, limit, offset=0):
    manifest, purchases, parent_hash = verified_snapshot(root, parent)
    if (
        manifest["mode"] != "live"
        or not 1 <= limit <= 100
        or type(offset) is not int
        or not 0 <= offset <= len(purchases)
    ):
        raise ValueError("live_snapshot_and_limit_1_to_100_required")
    sources = {}
    for page in manifest["pages"]:
        sources[page["body_sha256"]] = decode((root / page["relative_path"]).read_bytes())["data"]
    # Exclusions concern source locators, never contract outcomes.
    groups, exclusions = {}, []
    for row in sorted(purchases, key=lambda row: row["control_id"]):
        raw = sources[row["source_body_sha256"]][row["source_record_index"]]
        if raw.get("numeroControlePNCP") != row["control_id"]:
            raise ValueError("purchase_source_mismatch")
        year, sequence = raw.get("anoCompra"), raw.get("sequencialCompra")
        if (
            type(year) is not int
            or type(sequence) is not int
            or not 1900 <= year <= 9999
            or sequence < 1
        ):
            exclusions.append(
                {
                    "purchase_id": row["control_id"],
                    "reason": "invalid_purchase_locator",
                    "source_body_sha256": row["source_body_sha256"],
                    "source_record_index": row["source_record_index"],
                }
            )
            continue
        groups.setdefault(row["publication_date"][:7], []).append(
            {
                "purchase_id": row["control_id"],
                "cnpj": row["org_cnpj"],
                "year": year,
                "sequence": sequence,
            }
        )
    selected = []
    while groups and len(selected) < limit + offset:
        for month in sorted(list(groups)):
            selected.append(groups[month].pop(0))
            if not groups[month]:
                del groups[month]
            if len(selected) == limit + offset:
                break
    return {**manifest, "contract_locator_exclusions": exclusions}, parent_hash, selected[offset:]


def unpublished_response(body, status):
    # Observed official API response, distinct from a generic HTTP 404.
    if status != 404:
        return False
    try:
        payload = json.loads(body)
    except ValueError, UnicodeError:
        return False
    return (
        isinstance(payload, dict)
        and str(payload.get("status")) == "404"
        and payload.get("message") == "Não há contrato publicado no PNCP para esta contratação."
    )


def parse(body, status, purchase_id):
    if unpublished_response(body, status):
        return [], "none_returned"
    if status == 204 and not body:
        return [], "none_returned"
    if status != 200:
        return [], "request_failed"

    data = decode(body)["data"]
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


def replay(pages, purchase_id, read):
    rows, expected, seen = [], None, set()
    if not pages:
        raise ValueError("missing_pages")
    for number, page in enumerate(pages, 1):
        body = read(page)
        status = page["http_status"]
        if (
            number == 1
            and len(pages) == 1
            and ((status == 204 and not body) or unpublished_response(body, status))
        ):
            return [], "none_returned"
        if status != 200:
            return [], "request_failed"
        envelope = decode(body)
        totals = (envelope["totalRegistros"], envelope["totalPaginas"])
        if envelope["numeroPagina"] != number or (expected is not None and totals != expected):
            raise ValueError("pagination_changed")
        expected = totals
        part, _ = parse(body, status, purchase_id)
        for row in part:
            if row["contract_id"] in seen:
                raise ValueError("duplicate_contract_across_pages")
            seen.add(row["contract_id"])
            # Index in the logical concatenation of all source pages, in page order.
            row["source_record_index"] += len(rows)
        rows.extend(part)
    if len(pages) != max(1, expected[1]) or len(rows) != expected[0]:
        raise ValueError("incomplete_contract_pagination")
    return rows, "with_contracts" if rows else "none_returned"


def collect(root, parent, limit=12, transport=fetch, interval=1, max_pages=100, offset=0):
    if not 1 <= max_pages <= 100:
        raise ValueError("invalid_page_budget")
    parent_manifest, parent_hash, selected = select_purchases(root, parent, limit, offset)
    if not selected:
        raise ValueError("no_eligible_purchases_at_offset")
    run_id = str(uuid4())
    folder = root / "runs" / f"contracts-{run_id}"
    raw_folder = root / "data/raw" / run_id
    folder.mkdir(parents=True)
    raw_folder.mkdir(parents=True)
    manifest = {
        "schema_version": 2,
        "selection_offset": offset,
        "run_id": run_id,
        "parent_run_id": parent_manifest["run_id"],
        "parent_manifest_sha256": parent_hash,
        "started_at": datetime.now(UTC).isoformat(),
        "status": "running",
        "selection": "round_robin_valid_locators_month_then_control_id_v2",
        "excluded_purchases": parent_manifest["contract_locator_exclusions"],
        "population": parent_manifest["quality"]["normalized_records"],
        "selected": selected,
        "requests": [],
        "contracts": [],
    }
    interrupted = False
    try:
        for index, locator in enumerate(selected):
            evidence = {
                "purchase_id": locator["purchase_id"],
                "pages": [],
                "outcome": "invalid_response",
                "contracts_count": 0,
            }
            manifest["requests"].append(evidence)
            try:
                for number in range(1, max_pages + 1):
                    url = request_url(locator, number)
                    body, status = transport(url)
                    path = raw_folder / f"request-{index:04}-page-{number:04}.json"
                    path.write_bytes(body)
                    evidence["pages"].append(
                        {
                            "url": url,
                            "http_status": status,
                            "fetched_at": datetime.now(UTC).isoformat(),
                            "relative_path": path.relative_to(root).as_posix(),
                            "body_sha256": digest(body),
                        }
                    )
                    if interval:
                        time.sleep(interval)
                    if status != 200:
                        break
                    envelope = decode(body)
                    if number >= envelope["totalPaginas"]:
                        break
                rows, outcome = replay(
                    evidence["pages"],
                    locator["purchase_id"],
                    lambda page: (root / page["relative_path"]).read_bytes(),
                )
                evidence.update(outcome=outcome, contracts_count=len(rows))
                manifest["contracts"].extend(rows)
            except (ValueError, OSError, RuntimeError) as error:
                evidence["error_type"] = type(error).__name__
    except KeyboardInterrupt:
        interrupted = True
    manifest["quality"] = quality(manifest)
    counts = manifest["quality"]
    manifest["status"] = (
        "interrupted"
        if interrupted
        else (
            "needs_review"
            if counts.get("request_failed") or counts.get("invalid_response")
            else "pilot_complete"
        )
    )
    manifest["finished_at"] = datetime.now(UTC).isoformat()
    write_json(folder / "manifest.json", manifest)
    return folder / "manifest.json"


def quality(manifest):
    return {
        "selected": len(manifest["selected"]),
        "attempted": len(manifest["requests"]),
        **dict(Counter(request["outcome"] for request in manifest["requests"])),
        "contracts": len(manifest["contracts"]),
    }


def verify(root, path):
    body = read_evidence(root, path)
    manifest = json.loads(body)
    UUID(manifest["run_id"])
    UUID(manifest["parent_run_id"])
    if manifest["status"] != "pilot_complete":
        raise ValueError("only_complete_pilots_can_be_loaded")
    if manifest["schema_version"] != 2:
        raise ValueError("unsupported_contract_manifest")
    parent = root / "runs" / f"pncp-{manifest['parent_run_id']}" / "manifest.json"
    parent_manifest, parent_hash, selected = select_purchases(
        root, parent, len(manifest["selected"]), manifest.get("selection_offset", 0)
    )
    if "excluded_purchases" in manifest and (
        manifest["excluded_purchases"] != parent_manifest["contract_locator_exclusions"]
    ):
        raise ValueError("locator_exclusions_mismatch")
    if parent_hash != manifest["parent_manifest_sha256"] or selected != manifest["selected"]:
        raise ValueError("parent_or_selection_mismatch")
    if len(manifest["requests"]) != len(selected):
        raise ValueError("incomplete_coverage")

    def read(page):
        source = (root / page["relative_path"]).resolve()
        if not source.is_relative_to((root / "data/raw" / manifest["run_id"]).resolve()):
            raise ValueError("unsafe_source_path")
        raw = source.read_bytes()
        if digest(raw) != page["body_sha256"]:
            raise ValueError("source_hash_mismatch")
        return raw

    rows = []
    for locator, request in zip(selected, manifest["requests"], strict=True):
        if request["purchase_id"] != locator["purchase_id"]:
            raise ValueError("request_locator_mismatch")
        for number, page in enumerate(request["pages"], 1):
            if page["url"] != request_url(locator, number):
                raise ValueError("request_locator_mismatch")
        parsed, outcome = replay(request["pages"], locator["purchase_id"], read)
        if outcome != request["outcome"] or outcome == "request_failed":
            raise ValueError("outcome_mismatch")
        if len(parsed) != request["contracts_count"]:
            raise ValueError("outcome_mismatch")
        rows.extend(parsed)
    if rows != manifest["contracts"]:
        raise ValueError("normalized_contracts_mismatch")
    if manifest["quality"] != quality(manifest):
        raise ValueError("quality_mismatch")
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
                    digest("".join(page["body_sha256"] for page in request["pages"]).encode()),
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
    resuming = sub.add_parser("resume")
    resuming.add_argument("parent", type=Path)
    resuming.add_argument("--max-batches", type=int, default=1)
    args = parser.parse_args()
    try:
        if args.command == "resume":
            from asktrace.contract_batches import resume

            report = resume(Path.cwd(), args.parent, args.max_batches)
            print(report)
            return 0 if json.loads(report.read_bytes())["status"] != "needs_review" else 1
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
