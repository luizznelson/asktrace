"""Fixed business questions over an explicit, verified procurement snapshot."""

import argparse
import json
import os
import secrets
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from dotenv import load_dotenv, set_key
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from asktrace.connections import connect as database_connect
from asktrace.contracts import purchase_index, verify
from asktrace.evidence import read_evidence
from asktrace.ingest import digest


def connect(root, reader=True):
    return database_connect(root, "reader" if reader else "admin", row_factory=dict_row)


def setup(root):
    load_dotenv(root / ".env", override=False)
    password = os.environ.get("ASKTRACE_READER_PASSWORD") or secrets.token_urlsafe(32)
    with connect(root, reader=False) as db:
        db.execute((root / "sql/004_reporting.sql").read_text(encoding="utf-8"))
        db.execute(sql.SQL("ALTER ROLE asktrace_reader PASSWORD {}").format(sql.Literal(password)))
    # Never print or pass the generated password as a command-line argument.
    set_key(root / ".env", "ASKTRACE_READER_PASSWORD", password)


def dataset(root, report_path):
    report_bytes = read_evidence(root, report_path)
    report = json.loads(report_bytes)
    UUID(report["parent_run_id"])
    parent = root / "runs" / f"pncp-{report['parent_run_id']}" / "manifest.json"
    index = purchase_index(root, parent)
    manifest, purchases, parent_hash = index.manifest, index.purchases, index.checksum
    snapshots = []
    for reference in report["snapshots"]:
        path = (root / reference["path"]).resolve()
        if not path.is_relative_to((root / "runs").resolve()):
            raise ValueError("unsafe_snapshot_path")
        snapshot, checksum = verify(root, path, index=index)
        if (
            checksum != reference["sha256"]
            or snapshot["parent_run_id"] != manifest["run_id"]
            or snapshot["parent_manifest_sha256"] != parent_hash
        ):
            raise ValueError("snapshot_evidence_mismatch")
        snapshots.append(snapshot)
    coverage = {}
    for snapshot in sorted(snapshots, key=lambda row: (row["finished_at"], row["run_id"])):
        for request in snapshot["requests"]:
            coverage[request["purchase_id"]] = {
                "outcome": request["outcome"],
                "run_id": snapshot["run_id"],
                "contracts": [
                    row["contract_id"]
                    for row in snapshot["contracts"]
                    if row["purchase_id"] == request["purchase_id"]
                ],
            }
    if report["coverage"] != coverage or not set(coverage).issubset(
        {row["control_id"] for row in purchases}
    ):
        raise ValueError("coverage_evidence_mismatch")
    return manifest, purchases, coverage, digest(report_bytes)


@dataclass(frozen=True)
class VerifiedDataset:
    """Private in-memory copy of evidence verified during public application startup.

    Immutable bytes avoid sharing mutable query results. This is not a result cache:
    every question still queries PostgreSQL and checks coverage counts.
    """

    root: Path
    report: Path
    payload: bytes

    @classmethod
    def capture(cls, root, report, metadata):
        root, report = root.resolve(), (root / report).resolve()
        if not report.is_relative_to((root / "runs").resolve()):
            raise ValueError("unsafe_coverage_path")
        return cls(root, report, json.dumps(metadata).encode())

    def read(self, root, report):
        if root.resolve() != self.root or (root / report).resolve() != self.report:
            raise ValueError("verified_dataset_scope_mismatch")
        return json.loads(self.payload)


CTE = """WITH selected AS (
 SELECT key AS purchase_id, (value->>'run_id')::uuid AS contract_run_id
 FROM jsonb_each(%s::jsonb)
), p AS (SELECT * FROM asktrace.report_purchases WHERE run_id=%s::uuid),
c AS (SELECT c.* FROM asktrace.report_coverage c JOIN selected s
 ON c.purchase_id=s.purchase_id AND c.run_id=s.contract_run_id
 WHERE c.parent_run_id=%s::uuid),
k AS (SELECT k.* FROM asktrace.report_contracts k JOIN selected s
 ON k.purchase_id=s.purchase_id AND k.run_id=s.contract_run_id
 WHERE k.parent_run_id=%s::uuid)
"""
QUERIES = {
    "summary": """SELECT (SELECT count(*) FROM p) AS purchases,
      (SELECT count(*) FROM c) AS covered_purchases,
      (SELECT count(*) FROM c WHERE outcome='with_contracts') AS purchases_with_contracts,
      (SELECT count(*) FROM c WHERE outcome='none_returned') AS none_returned,
      (SELECT count(*) FROM k) AS contracts,
      (SELECT count(*) FROM p WHERE awarded_value IS NULL) AS unknown_awarded_values""",
    "municipalities": """SELECT municipality_ibge, municipality_name, count(*) AS purchases,
      count(*) FILTER (WHERE estimated_value IS NULL) AS unknown_estimates,
      sum(estimated_value) AS estimated_value,
      count(*) FILTER (WHERE awarded_value IS NULL) AS unknown_awarded_values
      FROM p GROUP BY municipality_ibge,municipality_name
      ORDER BY purchases DESC,municipality_ibge NULLS LAST,municipality_name NULLS LAST LIMIT 20""",
    "monthly": """SELECT to_char(publication_date, 'YYYY-MM') AS publication_month,
      count(*) AS purchases, sum(estimated_value) AS estimated_value,
      count(*) FILTER (WHERE estimated_value IS NULL) AS unknown_estimates,
      count(*) FILTER (WHERE awarded_value IS NULL) AS unknown_awarded_values
      FROM p GROUP BY to_char(publication_date, 'YYYY-MM') ORDER BY publication_month""",
    "organizations": """SELECT org_cnpj, min(nullif(trim(org_name), '')) AS org_name,
      count(*) AS purchases,
      sum(estimated_value) AS estimated_value,
      count(*) FILTER (WHERE estimated_value IS NULL) AS unknown_estimates,
      count(*) FILTER (WHERE awarded_value IS NULL) AS unknown_awarded_values
      FROM p GROUP BY org_cnpj
      ORDER BY purchases DESC, org_cnpj, org_name NULLS LAST LIMIT 20""",
    "quality": """SELECT count(*) AS purchases,
      count(*) FILTER (WHERE estimated_value IS NULL) AS unknown_estimates,
      count(*) FILTER (WHERE estimated_value = 0) AS zero_estimates,
      count(*) FILTER (WHERE awarded_value IS NULL) AS unknown_awarded_values,
      count(*) FILTER (WHERE awarded_value = 0) AS zero_awarded_values,
      count(*) FILTER (WHERE nullif(trim(municipality_ibge),'') IS NULL
        OR nullif(trim(municipality_name),'') IS NULL) AS unknown_municipalities,
      count(*) FILTER (WHERE nullif(trim(org_name),'') IS NULL) AS unknown_org_names FROM p""",
    "purchase": """SELECT p.control_id,p.org_name,p.municipality_name,p.publication_date,
      p.object_text,p.estimated_value,p.awarded_value,p.source_body_sha256,p.source_record_index,
      c.outcome,c.run_id AS contract_run_id,c.body_sha256 AS contract_pages_sha256,
      (SELECT jsonb_agg(jsonb_build_object('contract_id',k.contract_id,
       'initial_value',k.initial_value::text,'global_value',k.global_value::text,
       'source_record_index',k.source_record_index) ORDER BY k.contract_id)
       FROM k WHERE k.purchase_id=p.control_id) AS contracts
      FROM p LEFT JOIN c ON c.purchase_id=p.control_id WHERE p.control_id=%s""",
}


def answer(root, report, question, purchase_id=None, *, verified=None):
    if question not in QUERIES or (
        question == "purchase"
        and (not isinstance(purchase_id, str) or not 1 <= len(purchase_id) <= 100)
    ):
        raise ValueError("unsupported_question_or_identifier")
    report = (root / report).resolve()
    if not report.is_relative_to((root / "runs").resolve()):
        raise ValueError("unsafe_coverage_path")
    manifest, purchases, coverage, checksum = (
        verified.read(root, report) if verified is not None else dataset(root, report)
    )
    parent = manifest["run_id"]
    params = [Jsonb(coverage), parent, parent, parent]
    if question == "purchase":
        params.append(purchase_id)
    with connect(root) as db:
        db.execute("SET TRANSACTION READ ONLY")
        # Never accept SQL supplied by users or generated by an LLM.
        rows = db.execute(CTE + QUERIES[question], params).fetchall()
        expected = Counter(row["outcome"] for row in coverage.values())
        counts = db.execute(CTE + QUERIES["summary"], params[:4]).fetchone()
        if (
            counts["purchases"] != len(purchases)
            or counts["covered_purchases"] != len(coverage)
            or counts["purchases_with_contracts"] != expected["with_contracts"]
            or counts["none_returned"] != expected["none_returned"]
            or counts["contracts"] != sum(len(row["contracts"]) for row in coverage.values())
        ):
            raise ValueError("database_coverage_mismatch")
    return {
        "question": question,
        "purchase_id": purchase_id,
        "status": "not_found_in_scope" if question == "purchase" and not rows else "answered",
        "scope": {
            "purchase_run_id": parent,
            "date_start": manifest["date_start"],
            "date_end": manifest["date_end"],
            **manifest["scope"],
        },
        "coverage": counts,
        "coverage_report_sha256": checksum,
        "sources": {
            "coverage_report": report.relative_to(root).as_posix(),
            "purchase_manifest": f"runs/pncp-{parent}/manifest.json",
        },
        "limitations": [
            "Publication is not payment or financial execution.",
            "No returned publication does not establish absence of a contract.",
            "Unknown amounts are not zero; snapshots may have different dates.",
        ],
        "result": rows,
    }


def serialize(value):
    if isinstance(value, (Decimal, UUID)):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    raise TypeError(type(value).__name__)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question", choices=["setup-reader", *QUERIES])
    parser.add_argument("--coverage", type=Path)
    parser.add_argument("--purchase-id")
    args = parser.parse_args()
    try:
        if args.question == "setup-reader":
            setup(Path.cwd())
            print("Read-only login configured; password stored only in ignored .env")
        else:
            if args.coverage is None:
                raise ValueError("coverage_report_required")
            print(
                json.dumps(
                    answer(Path.cwd(), args.coverage, args.question, args.purchase_id),
                    default=serialize,
                    ensure_ascii=False,
                    indent=2,
                )
            )
        return 0
    except Exception as error:
        print(f"Query operation failed: {type(error).__name__}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
