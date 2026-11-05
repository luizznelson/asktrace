"""Private, hash-pinned source artifact stored in PostgreSQL, restored without PNCP calls."""

import hashlib
import io
import json
import re
import stat
from pathlib import Path, PurePosixPath
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from asktrace.connections import connect
from asktrace.evidence import read_evidence
from asktrace.query import dataset

MAX_ARCHIVE = 32 * 1024 * 1024
MAX_EXPANDED = 64 * 1024 * 1024


def safe_name(name):
    path = PurePosixPath(name)
    if (
        not isinstance(name, str)
        or "\\" in name
        or path.is_absolute()
        or ".." in path.parts
        or path.as_posix() != name
        or len(path.parts) < 4
        or path.parts[:2] not in {("data", "raw"), ("data", "processed")}
        or ":" in name
    ):
        raise ValueError("invalid_artifact_member")
    return path


def target_path(root, name):
    relative = safe_name(name)
    root = root.resolve()
    candidate = root
    for part in relative.parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise ValueError("artifact_symlink_target")
    resolved = candidate.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError("unsafe_artifact_target")
    return resolved


def source_files(root):
    config = json.loads((root / "config/datasets.json").read_bytes())
    paths = set()

    def visit(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key == "relative_path" and isinstance(item, str) and item.startswith("data/"):
                    safe_name(item)
                    paths.add(item)
                else:
                    visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    for item in config["datasets"]:
        dataset(root, root / item["coverage"])  # Verify all manifests before building.
        report = json.loads(read_evidence(root, Path(item["coverage"])))
        parent = Path("runs") / ("pncp-" + report["parent_run_id"]) / "manifest.json"
        visit(json.loads(read_evidence(root, parent)))
        for snapshot in report["snapshots"]:
            visit(json.loads(read_evidence(root, Path(snapshot["path"]))))
    return sorted(paths)


def build(root):
    stream = io.BytesIO()
    total = 0
    with ZipFile(stream, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for name in source_files(root):
            path = target_path(root, name)
            body = path.read_bytes()
            total += len(body)
            if total > MAX_EXPANDED:
                raise ValueError("artifact_too_large")
            info = ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, body)
    body = stream.getvalue()
    if len(body) > MAX_ARCHIVE:
        raise ValueError("artifact_too_large")
    return body, hashlib.sha256(body).hexdigest()


def restore(root, body, expected):
    if (
        not re.fullmatch(r"[0-9a-f]{64}", expected)
        or len(body) > MAX_ARCHIVE
        or hashlib.sha256(body).hexdigest() != expected
    ):
        raise ValueError("artifact_hash_mismatch")
    with ZipFile(io.BytesIO(body)) as archive:
        members = archive.infolist()
        if len(members) > 10000 or len({item.filename for item in members}) != len(members):
            raise ValueError("invalid_artifact_members")
        if sum(item.file_size for item in members) > MAX_EXPANDED:
            raise ValueError("artifact_expansion_limit")
        # Validate the entire manifest before any write. No extractall, links or arbitrary paths.
        for item in members:
            safe_name(item.orig_filename)
            safe_name(item.filename)
            if item.is_dir() or stat.S_ISLNK(item.external_attr >> 16):
                raise ValueError("invalid_artifact_type")
            target_path(root, item.filename)
        for item in members:
            path = target_path(root, item.filename)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(archive.read(item))


def restore_database_artifact(root, expected):
    if not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError("artifact_hash_required")
    with connect(root) as db:
        row = db.execute(
            "SELECT body FROM asktrace.deployment_artifacts WHERE sha256=%s", (expected,)
        ).fetchone()
    if not row:
        raise ValueError("deployment_artifact_missing")
    restore(root, bytes(row[0]), expected)
