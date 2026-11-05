import hashlib
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile, ZipInfo

from asktrace.connections import options
from asktrace.deployment_data import restore


class DeploymentDataTests(unittest.TestCase):
    def archive(self, names):
        stream = io.BytesIO()
        with ZipFile(stream, "w") as archive:
            for name in names:
                info = ZipInfo("placeholder")
                info.filename = name  # Preserve untrusted POSIX ZIP names on Windows too.
                archive.writestr(info, b"source")
        body = stream.getvalue()
        return body, hashlib.sha256(body).hexdigest()

    def test_private_artifact_roundtrip_and_tampering(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            body, checksum = self.archive(["data/raw/test/page.json"])
            restore(root, body, checksum)
            self.assertEqual((root / "data/raw/test/page.json").read_bytes(), b"source")
            with self.assertRaises(ValueError):
                restore(root, body + b"changed", checksum)

    def test_all_paths_validated_before_first_write(self):
        for name in (
            "../.env",
            "data/raw/../../.env",
            "data/raw/test/../page.json",
            "web/app.js",
            "C:/private",
            "data\\raw\\test\\page.json",
        ):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as folder:
                body, checksum = self.archive(["data/raw/test/valid.json", name])
                with self.assertRaises(ValueError):
                    restore(Path(folder), body, checksum)
                self.assertFalse((Path(folder) / "data").exists())

    def test_duplicate_archive_member_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertWarns(UserWarning):
                body, checksum = self.archive(["data/raw/test/x.json", "data/raw/test/x.json"])
            with self.assertRaises(ValueError):
                restore(Path(folder), body, checksum)

    def test_remote_credentials_force_hostname_and_certificate_verification(self):
        with (
            tempfile.TemporaryDirectory() as folder,
            patch.dict(
                os.environ,
                {
                    "ASKTRACE_DATABASE_URL": "postgresql://reader:private@db.example/db?sslmode=disable"
                },
                clear=True,
            ),
        ):
            result = options(Path(folder))
            self.assertEqual(result["sslmode"], "verify-full")
            self.assertTrue(Path(result["sslrootcert"]).is_file())

    def test_public_mode_never_falls_back_to_local_database(self):
        with (
            tempfile.TemporaryDirectory() as folder,
            patch.dict(os.environ, {"ASKTRACE_PUBLIC_ORIGIN": "https://example.com"}, clear=True),
        ):
            with self.assertRaises(ValueError):
                options(Path(folder))
            os.environ["ASKTRACE_DATABASE_URL"] = "postgresql://u:p@127.0.0.1/db"
            with self.assertRaises(ValueError):
                options(Path(folder))
