"""Opt-in PostgreSQL tests against asktrace_test, never the project data database."""

import json
import os
import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from asktrace.database import load
from asktrace.ingest import collect, digest


@unittest.skipUnless(
    os.environ.get("ASKTRACE_TEST_DATABASE") == "1", "PostgreSQL integration opt-in"
)
class DatabaseIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from dotenv import load_dotenv

        load_dotenv(Path(__file__).parents[1] / ".env", override=False)
        import psycopg

        with psycopg.connect(
            host="127.0.0.1",
            port=15432,
            dbname="asktrace_test",
            user="asktrace",
            password=os.environ["POSTGRES_PASSWORD"],
        ) as connection:
            for name in ("001_schema.sql", "002_purchases.sql"):
                connection.execute(
                    (Path(__file__).parents[1] / "sql" / name).read_text(encoding="utf-8")
                )

    def snapshot(self, root):
        (root / "sql").mkdir()
        for name in ("001_schema.sql", "002_purchases.sql"):
            shutil.copyfile(Path(__file__).parents[1] / "sql" / name, root / "sql" / name)
        row = {
            "numeroControlePNCP": "synthetic-db-test",
            "orgaoEntidade": {"cnpj": "00000000000000"},
            "unidadeOrgao": {"ufSigla": "PI"},
            "modalidadeId": 6,
            "dataPublicacaoPncp": "2026-08-01T00:00:00",
            "objetoCompra": "synthetic SQL test",
            "valorTotalEstimado": 10,
            "valorTotalHomologado": None,
        }
        sample = root / "sample.json"
        sample.write_text(
            json.dumps({"data": [row], "totalRegistros": 1, "totalPaginas": 1, "numeroPagina": 1})
        )
        return collect(root, date(2026, 8, 1), date(2026, 8, 31), sample=sample)

    def connect(self):
        import psycopg

        return psycopg.connect(
            host="127.0.0.1",
            port=15432,
            dbname="asktrace_test",
            user="asktrace",
            password=os.environ["POSTGRES_PASSWORD"],
            connect_timeout=5,
        )

    def test_idempotent_load_and_sample_separation(self):
        with (
            tempfile.TemporaryDirectory() as folder,
            patch.dict(os.environ, {"ASKTRACE_DATABASE_NAME": "asktrace_test"}),
        ):
            root = Path(folder)
            manifest = self.snapshot(root)
            self.assertEqual(load(root, manifest, True), "loaded")
            self.assertEqual(load(root, manifest, True), "already_loaded")
            run_id = json.loads(manifest.read_text())["run_id"]
            with self.connect() as connection:
                self.assertEqual(
                    connection.execute(
                        "SELECT count(*) FROM asktrace.purchases WHERE run_id=%s", (run_id,)
                    ).fetchone()[0],
                    1,
                )
                self.assertEqual(
                    connection.execute(
                        "SELECT count(*) FROM asktrace.live_purchases WHERE run_id=%s", (run_id,)
                    ).fetchone()[0],
                    0,
                )

    def test_constraint_failure_rolls_back_entire_run(self):
        import psycopg

        with (
            tempfile.TemporaryDirectory() as folder,
            patch.dict(os.environ, {"ASKTRACE_DATABASE_NAME": "asktrace_test"}),
        ):
            root = Path(folder)
            path = self.snapshot(root)
            manifest = json.loads(path.read_text())
            processed = root / manifest["normalized"]["relative_path"]
            rows = json.loads(processed.read_text())
            rows[0]["uf"] = "SP"  # Intentional SQL check failure in isolated synthetic fixture.
            processed.write_text(json.dumps(rows))
            manifest["normalized"]["sha256"] = digest(processed.read_bytes())
            path.write_text(json.dumps(manifest))
            with self.assertRaises(psycopg.errors.CheckViolation):
                load(root, path, True)
            with self.connect() as connection:
                self.assertEqual(
                    connection.execute(
                        "SELECT count(*) FROM asktrace.ingestion_runs WHERE run_id=%s",
                        (manifest["run_id"],),
                    ).fetchone()[0],
                    0,
                )
