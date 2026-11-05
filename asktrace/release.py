"""Build private evidence; provision a target database explicitly, never at app startup."""

import argparse
import hashlib
import json
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from psycopg import sql
from psycopg.conninfo import make_conninfo

from asktrace.connections import connect, options
from asktrace.contracts import load as load_contracts
from asktrace.database import load as load_purchases
from asktrace.deployment_data import build
from asktrace.evidence import read_evidence


def build_artifact(root):
    body, checksum = build(root)
    folder = root / "data/deploy"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "sources.zip").write_bytes(body)
    (folder / "artifact.json").write_text(
        json.dumps({"sha256": checksum, "bytes": len(body)}, indent=2) + "\n", encoding="utf-8"
    )
    return body, checksum


def load_target(root):
    load_dotenv(root / ".env", override=False)
    if not os.environ.get("ASKTRACE_ADMIN_DATABASE_URL"):
        raise ValueError("explicit_target_database_required")
    if os.environ.get("ASKTRACE_PUBLIC_ORIGIN"):
        raise ValueError("maintenance_must_run_outside_public_runtime")
    body, checksum = build_artifact(root)
    config = json.loads((root / "config/datasets.json").read_bytes())
    for item in config["datasets"]:
        coverage = json.loads(read_evidence(root, Path(item["coverage"])))
        parent = root / "runs" / ("pncp-" + coverage["parent_run_id"]) / "manifest.json"
        load_purchases(root, parent)
        for snapshot in coverage["snapshots"]:
            load_contracts(root, root / snapshot["path"])
    reader_password, service_password = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    with connect(root, "admin") as db:
        db.execute((root / "sql/004_reporting.sql").read_text(encoding="utf-8"))
        db.execute((root / "sql/005_deployment.sql").read_text(encoding="utf-8"))
        for role, password in (
            ("asktrace_reader", reader_password),
            ("asktrace_service", service_password),
        ):
            db.execute(
                sql.SQL("ALTER ROLE {} PASSWORD {}").format(
                    sql.Identifier(role), sql.Literal(password)
                )
            )
        existing = db.execute(
            "SELECT body FROM asktrace.deployment_artifacts WHERE sha256=%s", (checksum,)
        ).fetchone()
        if existing and hashlib.sha256(bytes(existing[0])).hexdigest() != checksum:
            raise ValueError("existing_artifact_changed")
        db.execute(
            "INSERT INTO asktrace.deployment_artifacts VALUES (%s,%s) "
            "ON CONFLICT (sha256) DO NOTHING",
            (checksum, body),
        )
    base = options(root, "admin")
    generated = {}
    for key, role, password in (
        ("ASKTRACE_DATABASE_URL", "asktrace_reader", reader_password),
        ("ASKTRACE_STATE_DATABASE_URL", "asktrace_service", service_password),
    ):
        configured = {**base, "user": role, "password": password}
        configured.pop("sslrootcert", None)
        generated[key] = make_conninfo(**configured)
    previous = {key: os.environ.get(key) for key in generated}
    try:
        os.environ.update(generated)
        from asktrace.public import check_database
        from asktrace.query import answer

        check_database(root)
        for item in config["datasets"]:
            coverage = json.loads(read_evidence(root, Path(item["coverage"])))
            result = answer(root, root / item["coverage"], "summary")
            if (
                result["coverage"]["purchases"] != coverage["population"]
                or result["coverage"]["contracts"] != coverage["distinct_contracts"]
            ):
                raise ValueError("target_database_totals_mismatch")
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    runtime = root / "data/deploy/runtime.env"
    # A private ignored output for transfer to the hosting secret settings. Never print contents.
    text = f"ASKTRACE_DATA_SHA256={checksum}\n"
    for key, value in generated.items():
        text += key + "=" + json.dumps(value) + "\n"
    runtime.write_text(text, encoding="utf-8")
    try:
        runtime.chmod(0o600)
    except OSError:
        pass  # Windows relies on the user's existing directory ACL, not Unix mode bits.
    return checksum


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "load"))
    args = parser.parse_args()
    try:
        root = Path.cwd()
        if args.action == "build":
            body, checksum = build_artifact(root)
            print(json.dumps({"artifact_sha256": checksum, "compressed_bytes": len(body)}))
        else:
            checksum = load_target(root)
            print(
                json.dumps(
                    {
                        "loaded": True,
                        "artifact_sha256": checksum,
                        "private_runtime_settings": "data/deploy/runtime.env",
                    }
                )
            )
        return 0
    except Exception as error:
        print(json.dumps({"error_type": type(error).__name__, "action": args.action}))
        return 1  # Database exceptions may contain credentials; never print their messages.


if __name__ == "__main__":
    raise SystemExit(main())
