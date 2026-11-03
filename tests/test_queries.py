"""Business totals, provenance, parameterization and database privileges."""

import json
import os
import shutil
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from test_contracts import response, snapshot

from asktrace import contract_batches, contracts, query
from asktrace.database import load


class QueryCatalogTests(unittest.TestCase):
    def test_arbitrary_sql_and_missing_identifier_rejected_before_connection(self):
        with patch.object(query, "connect") as connection:
            for question, identifier in (("DROP TABLE purchases", None), ("purchase", None)):
                with self.assertRaises(ValueError):
                    query.answer(Path.cwd(), Path("unused"), question, identifier)
            connection.assert_not_called()


@unittest.skipUnless(os.environ.get("ASKTRACE_TEST_DATABASE") == "1", "PostgreSQL opt-in")
class BusinessQueryTests(unittest.TestCase):
    def setUp(self):
        from dotenv import load_dotenv

        load_dotenv(Path(__file__).parents[1] / ".env", override=False)
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copytree(Path(__file__).parents[1] / "sql", self.root / "sql")
        self.environment = patch.dict(os.environ, {"ASKTRACE_DATABASE_NAME": "asktrace_test"})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        parent = snapshot(self.root)
        load(self.root, parent)
        path = contracts.collect(self.root, parent, 1, lambda url: (response(), 200), 0)
        contracts.load(self.root, path)
        self.report = contract_batches.resume(self.root, parent)
        query.setup(self.root)

    def test_totals_unknowns_and_no_multiplication_by_contracts(self):
        summary = query.answer(self.root, self.report, "summary")
        self.assertEqual(summary["coverage"]["purchases"], 1)
        self.assertEqual(summary["coverage"]["contracts"], 2)
        self.assertEqual(summary["coverage"]["unknown_awarded_values"], 1)
        municipalities = query.answer(self.root, self.report, "municipalities")
        self.assertEqual(municipalities["result"][0]["estimated_value"], Decimal(10))
        self.assertEqual(municipalities["result"][0]["purchases"], 1)

    def test_trace_and_injection_is_a_literal_identifier(self):
        trace = query.answer(self.root, self.report, "purchase", "synthetic-purchase")
        self.assertEqual(len(trace["result"][0]["contracts"]), 2)
        self.assertEqual(len(trace["result"][0]["source_body_sha256"]), 64)
        self.assertEqual(trace["status"], "answered")
        injected = query.answer(self.root, self.report, "purchase", "' OR true; --")
        self.assertEqual(injected["status"], "not_found_in_scope")
        self.assertEqual(injected["result"], [])

    def test_database_denies_writes_even_if_read_only_default_is_disabled(self):
        import psycopg

        with query.connect(self.root) as db:
            role = db.execute(
                "SELECT rolsuper,rolcreatedb,rolcreaterole FROM pg_roles WHERE rolname=current_user"
            ).fetchone()
            self.assertEqual(list(role.values()), [False, False, False])
        with query.connect(self.root) as db:
            self.assertFalse(
                db.execute(
                    "SELECT has_table_privilege(current_user, "
                    "'asktrace.purchases', 'INSERT,UPDATE,DELETE') AS allowed"
                ).fetchone()["allowed"]
            )
        for statement in (
            "DELETE FROM asktrace.purchases",
            "DELETE FROM asktrace.report_purchases",
            "CREATE TABLE asktrace.must_not_exist (id integer)",
        ):
            with self.assertRaises(
                (psycopg.errors.InsufficientPrivilege, psycopg.errors.ObjectNotInPrerequisiteState)
            ):
                with query.connect(self.root) as db:
                    db.execute("SET TRANSACTION READ WRITE")
                    db.execute(statement)

    def test_changed_coverage_is_rejected(self):
        report = json.loads(self.report.read_bytes())
        report["coverage"]["synthetic-purchase"]["outcome"] = "none_returned"
        self.report.write_text(json.dumps(report))
        with self.assertRaisesRegex(ValueError, "coverage_evidence_mismatch"):
            query.answer(self.root, self.report, "summary")
