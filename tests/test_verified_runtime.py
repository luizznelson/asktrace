"""Evidence reuse must preserve scope, isolation and fresh database validation."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from test_contracts import response, snapshot

from asktrace import agent, contract_batches, contracts, query


class VerifiedRuntimeTests(unittest.TestCase):
    def fixture(self, root):
        parent = snapshot(root)
        for _ in range(2):
            contracts.collect(root, parent, 1, lambda url: (response(), 200), 0)
        report = contract_batches.resume(root, parent, loader=Mock())
        return parent, report

    def test_parent_verified_once_and_rechecked_on_next_operation(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            parent, report = self.fixture(root)
            with patch.object(
                contracts, "verified_snapshot", wraps=contracts.verified_snapshot
            ) as verify:
                result = query.dataset(root, report)
                self.assertEqual(verify.call_count, 1)
                self.assertEqual(len(result[2]), 1)
            manifest = json.loads(parent.read_bytes())
            raw = root / manifest["pages"][0]["relative_path"]
            raw.write_bytes(b"changed source")
            with self.assertRaisesRegex(ValueError, "integrity verification failed"):
                query.dataset(root, report)

    def test_reused_parent_does_not_skip_contract_page_hashes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            _, report = self.fixture(root)
            query.dataset(root, report)
            coverage = json.loads(report.read_bytes())
            batch = json.loads((root / coverage["snapshots"][0]["path"]).read_bytes())
            page = root / batch["requests"][0]["pages"][0]["relative_path"]
            page.write_bytes(b"changed contract")
            with self.assertRaisesRegex(ValueError, "source_hash_mismatch"):
                query.dataset(root, report)

    def test_public_copy_is_immutable_and_bound_to_root_and_report(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            _, report = self.fixture(root)
            metadata = query.dataset(root, report)
            verified = query.VerifiedDataset.capture(root, report, metadata)
            first = verified.read(root, report)
            first[0]["scope"]["uf"] = "XX"
            first[2].clear()
            second = verified.read(root, report)
            self.assertEqual(second[0]["scope"]["uf"], "PI")
            self.assertEqual(len(second[2]), 1)
            for other_root, other_report in (
                (root, report.with_name("other.json")),
                (root / "other", report),
            ):
                with self.assertRaisesRegex(ValueError, "verified_dataset_scope_mismatch"):
                    verified.read(other_root, other_report)

    def test_agent_uses_same_verified_scope_for_ai_and_tool(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            _, report = self.fixture(root)
            verified = query.VerifiedDataset.capture(root, report, query.dataset(root, report))
            tool = Mock(side_effect=RuntimeError("stop before database"))
            with (
                patch.object(
                    query, "dataset", side_effect=AssertionError("unexpected file replay")
                ),
                patch.object(
                    agent, "select", return_value={"action": "summary", "purchase_id": None}
                ),
            ):
                result = agent.run(
                    root,
                    report,
                    "Qual é o resumo da cobertura?",
                    "fallback",
                    tool=tool,
                    verified=verified,
                )
            tool.assert_called_once_with(root, report, "summary", None, verified=verified)
            self.assertEqual(result["status"], "error")
            self.assertNotIn("stop before database", str(result))
