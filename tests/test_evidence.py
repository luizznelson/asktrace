"""Line-ending recovery must never accept changed JSON data or archive traversal."""

import json
import tempfile
import unittest
from pathlib import Path

from asktrace.evidence import read_evidence
from asktrace.ingest import digest


class EvidenceTests(unittest.TestCase):
    def fixture(self, root):
        path = root / "runs/source.json"
        path.parent.mkdir()
        published = b'{\n "count": 1\n}\n'
        original = published.replace(b"\n", b"\r\n")
        path.write_bytes(published)
        archive = root / "runs/evidence-source-bytes/original.json"
        archive.parent.mkdir()
        archive.write_bytes(original)
        folder = root / "runs/evidence-byte-provenance-test"
        folder.mkdir()
        entry = {
            "source": "runs/source.json",
            "published_sha256": digest(published),
            "execution_bytes_sha256": digest(original),
            "execution_snapshot": "runs/evidence-source-bytes/original.json",
        }
        (folder / "manifest.json").write_text(json.dumps({"sources": [entry]}))
        return path, archive, original

    def test_exact_crlf_bytes_recovered_without_changing_published_file(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path, _, original = self.fixture(root)
            self.assertEqual(read_evidence(root, path), original)
            self.assertNotIn(b"\r\n", path.read_bytes())

    def test_changed_archive_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path, archive, _ = self.fixture(root)
            archive.write_bytes(b'{"count": 999}')
            with self.assertRaises(ValueError):
                read_evidence(root, path)

    def test_archive_outside_designated_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path, _, _ = self.fixture(root)
            crosswalk = root / "runs/evidence-byte-provenance-test/manifest.json"
            data = json.loads(crosswalk.read_bytes())
            data["sources"][0]["execution_snapshot"] = "../outside.json"
            crosswalk.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "unsafe_execution_snapshot_path"):
                read_evidence(root, path)
