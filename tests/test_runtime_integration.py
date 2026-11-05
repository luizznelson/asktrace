"""Opt-in tests: runtime state is isolated to asktrace_test, never the real data database."""

import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from dotenv import load_dotenv
from psycopg.conninfo import make_conninfo

from asktrace.connections import connect, options
from asktrace.runtime_state import read_health, reserve, write_health


@unittest.skipUnless(os.environ.get("ASKTRACE_TEST_DATABASE") == "1", "PostgreSQL opt-in")
class RuntimeIntegrationTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).parents[1]
        load_dotenv(root / ".env", override=False)
        self.environment = patch.dict(os.environ, {"ASKTRACE_DATABASE_NAME": "asktrace_test"})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        with connect(self.root, "admin") as db:
            self.assertEqual(db.info.dbname, "asktrace_test")
            db.execute((root / "sql/005_deployment.sql").read_text(encoding="utf-8"))
            db.execute("DELETE FROM asktrace.runtime_state")
        # Administrative login used only by tests; public startup verifies a narrower state role.
        os.environ["ASKTRACE_STATE_DATABASE_URL"] = make_conninfo(**options(self.root, "admin"))

    def test_budget_is_atomic_across_connections_and_survives_recreation(self):
        with ThreadPoolExecutor(max_workers=8) as pool:
            admitted = list(pool.map(lambda _: reserve(self.root, True, 5, now=1000), range(12)))
        self.assertEqual(sum(admitted), 5)
        self.assertFalse(reserve(Path(self.temporary.name), True, 5, now=1060))
        self.assertTrue(reserve(self.root, False, 5, now=1060))
        self.assertTrue(reserve(self.root, True, 5, now=1000 + 86400))

    def test_global_minute_limit_and_monotonic_provider_wait(self):
        self.assertEqual(sum(reserve(self.root, False, 5, now=2000) for _ in range(40)), 30)
        write_health(self.root, {"provider:groq": {"not_before": 5000, "reason": "http_429"}})
        write_health(self.root, {"provider:groq": {"not_before": 4000, "reason": "http_503"}})
        self.assertEqual(read_health(self.root)["provider:groq"]["not_before"], 5000)
        with connect(self.root, "admin") as db:
            self.assertFalse(
                db.execute(
                    "SELECT has_table_privilege('asktrace_service', 'asktrace.purchases', 'INSERT')"
                ).fetchone()[0]
            )
            self.assertFalse(
                db.execute(
                    "SELECT has_table_privilege('asktrace_reader', "
                    "'asktrace.runtime_state', 'UPDATE')"
                ).fetchone()[0]
            )

    def test_state_role_can_update_its_table_but_cannot_read_business_records(self):
        import psycopg

        with connect(self.root, "admin") as db:
            db.execute("SET LOCAL ROLE asktrace_service")
            db.execute("INSERT INTO asktrace.runtime_state VALUES ('public-budget', '{}'::jsonb)")
            db.execute(
                "UPDATE asktrace.runtime_state SET value='{\"day\": 1}'::jsonb "
                "WHERE name='public-budget'"
            )
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            with connect(self.root, "admin") as db:
                db.execute("SET LOCAL ROLE asktrace_service")
                db.execute("SELECT * FROM asktrace.purchases LIMIT 1")
