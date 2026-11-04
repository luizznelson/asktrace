"""A coverage update must not select an unverified or mismatched database report."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.publish_contract_coverage import publish


class CoveragePublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "runs").mkdir()
        (self.root / "config").mkdir()
        self.config = self.root / "config/datasets.json"
        self.before = json.dumps(
            {
                "version": 1,
                "default": "expanded",
                "datasets": [
                    {"id": "expanded", "coverage": "runs/old.json"},
                    {"id": "original", "coverage": "runs/original.json"},
                ],
            }
        ).encode()
        self.config.write_bytes(self.before)
        self.report = self.root / "runs/coverage.json"
        self.report.write_text(
            json.dumps(
                {
                    "parent_run_id": "74d68096-1e27-451d-b423-f8cded554d54",
                    "covered_distinct_purchases": 1,
                    "distinct_contracts": 0,
                    "purchases_with_contracts": 0,
                    "purchases_none_returned": 1,
                    "population": 2,
                    "eligible": 1,
                    "remaining_eligible": 0,
                    "excluded_purchases": [{"purchase_id": "excluded"}],
                    "snapshots": [{"path": "runs/manifest.json"}],
                    "coverage": {"purchase": {"outcome": "none_returned", "contracts": []}},
                }
            )
        )
        self.counts = {
            "covered_purchases": 1,
            "contracts": 0,
            "purchases_with_contracts": 0,
            "none_returned": 1,
            "purchases": 2,
        }
        self.summary = {"coverage": self.counts, "coverage_report_sha256": "a" * 64}

    def test_verified_and_idempotent_coverage_is_selected_atomically(self):
        with (
            patch(
                "scripts.publish_contract_coverage.query.answer",
                side_effect=[
                    self.summary,
                    {"result": [{"outcome": "none_returned", "contracts": None}]},
                ],
            ),
            patch(
                "scripts.publish_contract_coverage.contracts.load", return_value="already_loaded"
            ),
        ):
            result = publish(self.root, self.report)
        self.assertTrue(result.exists())
        datasets = json.loads(self.config.read_bytes())["datasets"]
        self.assertEqual(datasets[0]["coverage"], "runs/coverage.json")
        self.assertEqual(datasets[1]["coverage"], "runs/original.json")

    def test_database_mismatch_never_changes_active_dataset(self):
        self.counts["covered_purchases"] = 0
        with (
            patch("scripts.publish_contract_coverage.query.answer", return_value=self.summary),
            patch("scripts.publish_contract_coverage.contracts.load") as load,
        ):
            with self.assertRaisesRegex(ValueError, "coverage_totals"):
                publish(self.root, self.report)
        self.assertEqual(self.config.read_bytes(), self.before)
        load.assert_not_called()

    def test_unexpected_load_prevents_publication(self):
        with (
            patch("scripts.publish_contract_coverage.query.answer", return_value=self.summary),
            patch("scripts.publish_contract_coverage.contracts.load", return_value="loaded"),
        ):
            with self.assertRaisesRegex(ValueError, "non_idempotent"):
                publish(self.root, self.report)
        self.assertEqual(self.config.read_bytes(), self.before)

    def test_unverified_snapshot_never_changes_active_dataset(self):
        with patch(
            "scripts.publish_contract_coverage.query.answer",
            side_effect=ValueError("source_hash_mismatch"),
        ):
            with self.assertRaisesRegex(ValueError, "source_hash"):
                publish(self.root, self.report)
        self.assertEqual(self.config.read_bytes(), self.before)
