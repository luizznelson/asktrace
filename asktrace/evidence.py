"""Resolve exact execution bytes for legacy JSON whose Git line endings were normalized."""

import argparse
import json
from pathlib import Path

from asktrace.ingest import digest


def read_evidence(root, path):
    root = root.resolve()
    path = (root / path).resolve()
    if not path.is_relative_to(root):
        raise ValueError("evidence_outside_project")
    published = path.read_bytes()
    name = path.relative_to(root).as_posix()
    for crosswalk in sorted((root / "runs").glob("evidence-byte-provenance-*/manifest.json")):
        for item in json.loads(crosswalk.read_bytes())["sources"]:
            if item["source"] != name or item["published_sha256"] != digest(published):
                continue
            archive = (root / item["execution_snapshot"]).resolve()
            if not archive.is_relative_to((root / "runs/evidence-source-bytes").resolve()):
                raise ValueError("unsafe_execution_snapshot_path")
            original = archive.read_bytes()
            if digest(original) != item["execution_bytes_sha256"] or original.replace(
                b"\r\n", b"\n"
            ) != published.replace(b"\r\n", b"\n"):
                raise ValueError("execution_snapshot_integrity_failure")
            return original
    return published


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    try:
        original = read_evidence(Path.cwd(), args.path)
        published = args.path.read_bytes()
        print(
            json.dumps(
                {
                    "execution_sha256": digest(original),
                    "published_sha256": digest(published),
                    "legacy_execution_snapshot_used": original != published,
                }
            )
        )
        return 0
    except Exception as error:
        print(f"Evidence verification failed: {type(error).__name__}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
