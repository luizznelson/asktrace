"""Resumption uses verified snapshots and never sums overlapping coverage."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from test_contracts import response, snapshot

from asktrace import contract_batches as batches
from asktrace import contracts


class BatchTests(unittest.TestCase):
    def test_next_batch_stops_at_covered_gap_and_caps_size(self):
        self.assertEqual(batches.next_batch(["a", "b", "c"], {"b": {}}), (0, 1))
        self.assertEqual(batches.next_batch(["a", "b", "c"], {"a": {}}), (1, 2))
        self.assertEqual(batches.next_batch(list(range(120)), {}), (0, 100))
        self.assertIsNone(batches.next_batch(["a"], {"a": {}}))

    def test_overlap_counts_once_and_completed_work_is_not_requested(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            parent = snapshot(root)
            for _ in range(2):
                contracts.collect(root, parent, 1, lambda url: (response(), 200), 0)
            loader, collector = Mock(return_value="already_loaded"), Mock()
            path = batches.resume(root, parent, collector=collector, loader=loader)
            report = json.loads(path.read_bytes())
            collector.assert_not_called()
            self.assertEqual(report["covered_distinct_purchases"], 1)
            self.assertEqual(report["distinct_contracts"], 2)
            self.assertEqual(len(report["snapshots"]), 2)

    def test_failure_stops_run_and_remains_pending(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            parent = snapshot(root)

            def collector(root, parent, limit, offset):
                return contracts.collect(
                    root, parent, limit, transport=lambda url: (b"", 503), interval=0, offset=offset
                )

            report = json.loads(
                batches.resume(
                    root, parent, max_batches=2, collector=collector, loader=Mock()
                ).read_bytes()
            )
            self.assertEqual(report["status"], "needs_review")
            self.assertEqual(len(report["events"]), 1)
            self.assertEqual(report["remaining_eligible"], 1)

    def test_tampered_snapshot_cannot_skip_a_purchase(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            parent = snapshot(root)
            path = contracts.collect(root, parent, 1, lambda url: (response(), 200), 0)
            manifest = json.loads(path.read_bytes())
            manifest["contracts"][0]["global_value"] = "123"
            path.write_text(json.dumps(manifest))
            with self.assertRaises(ValueError):
                batches.inventory(root, parent, loader=Mock())

    def test_offset_is_validated_and_bound_to_selection(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            parent = snapshot(root)
            with self.assertRaises(ValueError):
                contracts.select_purchases(root, parent, 1, -1)
            path = contracts.collect(root, parent, 1, lambda url: (response(), 200), 0)
            manifest = json.loads(path.read_bytes())
            manifest["selection_offset"] = 1
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "parent_or_selection_mismatch"):
                contracts.verify(root, path)
