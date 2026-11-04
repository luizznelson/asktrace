"""Verify a collected snapshot, then load it in one PostgreSQL transaction."""

import argparse
import json
import os
from pathlib import Path
from uuid import UUID

from asktrace.evidence import read_evidence
from asktrace.ingest import digest


def verified_snapshot(root: Path, manifest_path: Path, allow_sample: bool = False):
    manifest_bytes = read_evidence(root, manifest_path)
    manifest = json.loads(manifest_bytes)
    UUID(manifest["run_id"])
    allowed = {"complete", "sample_only"} if allow_sample else {"complete"}
    if manifest["status"] not in allowed:
        raise ValueError("Only complete live runs (or explicitly enabled samples) can be loaded")
    expected_raw = (root / "data/raw" / manifest["run_id"]).resolve()
    for page in manifest["pages"]:
        path = (root / page["relative_path"]).resolve()
        if (
            not path.is_relative_to(expected_raw)
            or digest(path.read_bytes()) != page["body_sha256"]
        ):
            raise ValueError("Raw page integrity verification failed")
    path = (root / manifest["normalized"]["relative_path"]).resolve()
    if not path.is_relative_to((root / "data/processed" / manifest["run_id"]).resolve()):
        raise ValueError("Normalized file outside its run directory")
    body = path.read_bytes()
    if digest(body) != manifest["normalized"]["sha256"]:
        raise ValueError("Normalized file integrity verification failed")
    rows = json.loads(body)
    if len(rows) != manifest["quality"]["normalized_records"]:
        raise ValueError("Normalized record count mismatch")
    if len({row["control_id"] for row in rows}) != len(rows):
        raise ValueError("Normalized records have duplicate identifiers")
    return manifest, rows, digest(manifest_bytes)


def load(root: Path, manifest_path: Path, allow_sample: bool = False) -> str:
    manifest, rows, manifest_hash = verified_snapshot(root, manifest_path, allow_sample)
    import psycopg
    from dotenv import load_dotenv
    from psycopg.types.json import Jsonb

    load_dotenv(root / ".env", override=False)
    password = os.environ.get("POSTGRES_PASSWORD")
    if not password:
        raise ValueError("Configure POSTGRES_PASSWORD in the ignored .env")
    # Never format credentials into a URL, command argument or log.
    with psycopg.connect(
        host="127.0.0.1",
        port=15432,
        user="asktrace",
        dbname=os.environ.get("ASKTRACE_DATABASE_NAME", "asktrace"),
        password=password,
        connect_timeout=10,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(717426001)")
            for name in ("001_schema.sql", "002_purchases.sql"):
                cursor.execute((root / "sql" / name).read_text(encoding="utf-8"))
            cursor.execute(
                "SELECT manifest_sha256 FROM asktrace.ingestion_runs WHERE run_id=%s",
                (manifest["run_id"],),
            )
            existing = cursor.fetchone()
            if existing:
                if existing[0] != manifest_hash:
                    raise ValueError("Run already exists with different evidence")
                return "already_loaded"
            scope = {
                **manifest["scope"],
                "mode": manifest["mode"],
                "normalization_version": "purchases-1",
            }
            cursor.execute(
                """INSERT INTO asktrace.ingestion_runs
                (run_id,source,date_start,date_end,scope,status,manifest_sha256)
                VALUES (%s,'pncp',%s,%s,%s,'running',%s)""",
                (
                    manifest["run_id"],
                    manifest["date_start"],
                    manifest["date_end"],
                    Jsonb(scope),
                    manifest_hash,
                ),
            )
            for page in manifest["pages"]:
                cursor.execute(
                    """INSERT INTO asktrace.source_pages
                    (run_id,resource,request_sha256,page_number,fetched_at,body_sha256,relative_path,records_count)
                    VALUES (%s,'purchases',%s,%s,%s,%s,%s,%s)""",
                    (
                        manifest["run_id"],
                        page["request_sha256"],
                        page["page"],
                        page["fetched_at"],
                        page["body_sha256"],
                        page["relative_path"],
                        page["records_count"],
                    ),
                )
            for row in rows:
                cursor.execute(
                    """INSERT INTO asktrace.organizations (run_id,cnpj,name)
                    VALUES (%s,%s,%s) ON CONFLICT (run_id,cnpj) DO NOTHING""",
                    (manifest["run_id"], row["org_cnpj"], row["org_name"]),
                )
                columns = (
                    "control_id",
                    "org_cnpj",
                    "org_name",
                    "unit_code",
                    "municipality_ibge",
                    "municipality_name",
                    "uf",
                    "modality",
                    "publication_date",
                    "object_text",
                    "estimated_value",
                    "awarded_value",
                    "source_body_sha256",
                    "source_record_index",
                )
                # Identifiers above are fixed application code; all source values use parameters.
                cursor.execute(
                    """INSERT INTO asktrace.purchases
                    (run_id,control_id,org_cnpj,org_name,unit_code,municipality_ibge,municipality_name,
                     uf,modality,publication_date,object_text,estimated_value,awarded_value,
                     source_body_sha256,source_record_index)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (manifest["run_id"], *(row[column] for column in columns)),
                )
            cursor.execute(
                "UPDATE asktrace.ingestion_runs SET status='complete' WHERE run_id=%s",
                (manifest["run_id"],),
            )
    return "loaded"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--allow-sample", action="store_true")
    args = parser.parse_args()
    try:
        result = load(Path.cwd(), args.manifest, args.allow_sample)
        print(result)
        return 0
    except Exception as error:
        # Driver errors may contain connection details: print the class, never the message.
        print(f"Load failed: {type(error).__name__}; database transaction was not committed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
