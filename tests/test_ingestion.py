import json
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from asktrace.database import verified_snapshot
from asktrace.ingest import amount, collect, decode, normalize, windows


def record(identifier="synthetic-1"):
    return {
        "numeroControlePNCP": identifier,
        "orgaoEntidade": {"cnpj": "00000000000000", "razaoSocial": "SYNTHETIC"},
        "unidadeOrgao": {"ufSigla": "PI", "codigoIbge": "2208007"},
        "modalidadeId": 6,
        "dataPublicacaoPncp": "2026-08-02T12:00:00",
        "objetoCompra": "synthetic coffee",
        "valorTotalEstimado": 10,
        "valorTotalHomologado": None,
    }


def page(records, number=1, total=None, pages=1):
    return json.dumps(
        {
            "data": records,
            "numeroPagina": number,
            "totalRegistros": len(records) if total is None else total,
            "totalPaginas": pages,
        }
    ).encode()


class IngestionTests(unittest.TestCase):
    def test_month_windows_cover_dates_exactly(self):
        self.assertEqual(
            windows(date(2026, 8, 1), date(2026, 10, 31)),
            [
                (date(2026, 8, 1), date(2026, 8, 31)),
                (date(2026, 9, 1), date(2026, 9, 30)),
                (date(2026, 10, 1), date(2026, 10, 31)),
            ],
        )

    def test_values_are_exact_and_missing_is_not_zero(self):
        body = decode(
            page([record()]).replace(b'"valorTotalEstimado": 10', b'"valorTotalEstimado": 0.10')
        )
        self.assertEqual(body["data"][0]["valorTotalEstimado"], Decimal("0.10"))
        self.assertEqual(amount(None), (None, "missing"))
        self.assertEqual(amount(Decimal("-1")), (None, "invalid"))
        self.assertEqual(amount(True), (None, "invalid"))

    def test_invalid_json_or_pagination_rejected(self):
        for body in [
            b"",
            b"null",
            b'{"data":[],"totalRegistros":true}',
            page([], total=4, pages=0),
        ]:
            with self.assertRaises(ValueError):
                decode(body)

    def test_filters_and_dates_are_verified_again(self):
        for change in [
            {"modalidadeId": 7},
            {"unidadeOrgao": {"ufSigla": "SP"}},
            {"dataPublicacaoPncp": "2025-08-01T00:00:00"},
        ]:
            value = {**record(), **change}
            result, issues = normalize(value, date(2026, 8, 1), date(2026, 8, 31))
            self.assertIsNone(result)
            self.assertTrue(issues)

    def test_complete_pagination_and_tamper_detection(self):
        def transport(params):
            n = params["pagina"]
            return page([record(str(n))], number=n, total=2, pages=2), 200

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = collect(
                root, date(2026, 8, 1), date(2026, 8, 31), transport=transport, interval=0
            )
            manifest, rows, _ = verified_snapshot(root, path)
            self.assertEqual(manifest["status"], "complete")
            self.assertEqual(len(rows), 2)
            (root / manifest["pages"][0]["relative_path"]).write_bytes(b"tampered")
            with self.assertRaises(ValueError):
                verified_snapshot(root, path)

    def test_network_failure_is_a_failed_run_with_manifest(self):
        def transport(params):
            raise RuntimeError("pncp_connection_failed")

        with tempfile.TemporaryDirectory() as folder:
            path = collect(
                Path(folder), date(2026, 8, 1), date(2026, 8, 31), transport=transport, interval=0
            )
            self.assertEqual(json.loads(path.read_text())["status"], "failed")

    def test_changing_total_does_not_claim_complete(self):
        def transport(params):
            n = params["pagina"]
            return page([record(str(n))], number=n, total=2 if n == 1 else 3, pages=2), 200

        with tempfile.TemporaryDirectory() as folder:
            path = collect(
                Path(folder), date(2026, 8, 1), date(2026, 8, 31), transport=transport, interval=0
            )
            self.assertEqual(json.loads(path.read_text())["status"], "failed")

    def test_repeated_ids_require_review_not_silent_success(self):
        def transport(params):
            return page([record()], number=params["pagina"], total=2, pages=2), 200

        with tempfile.TemporaryDirectory() as folder:
            path = collect(
                Path(folder), date(2026, 8, 1), date(2026, 8, 31), transport=transport, interval=0
            )
            self.assertEqual(json.loads(path.read_text())["status"], "needs_review")

    def test_page_budget_and_empty_success(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = collect(
                root,
                date(2026, 8, 1),
                date(2026, 8, 31),
                transport=lambda _: (page([], total=0, pages=0), 200),
                interval=0,
            )
            self.assertEqual(json.loads(path.read_text())["status"], "complete")
            path = collect(
                root,
                date(2026, 8, 1),
                date(2026, 8, 31),
                transport=lambda _: (page([record()], total=2, pages=2), 200),
                interval=0,
                max_pages=1,
            )
            self.assertEqual(json.loads(path.read_text())["status"], "failed")

    def test_sample_requires_explicit_database_permission(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            sample = root / "sample.json"
            sample.write_bytes(page([record()]))
            path = collect(root, date(2026, 8, 1), date(2026, 8, 31), sample=sample)
            with self.assertRaises(ValueError):
                verified_snapshot(root, path)
            self.assertEqual(len(verified_snapshot(root, path, True)[1]), 1)

    def test_manifest_cannot_redirect_outside_raw_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = collect(
                root,
                date(2026, 8, 1),
                date(2026, 8, 31),
                transport=lambda _: (page([record()]), 200),
                interval=0,
            )
            manifest = json.loads(path.read_text())
            manifest["pages"][0]["relative_path"] = "../../other.json"
            path.write_text(json.dumps(manifest))
            with self.assertRaises(ValueError):
                verified_snapshot(root, path)

    def test_interruption_keeps_a_manifest_and_cannot_be_loaded(self):
        def transport(params):
            raise KeyboardInterrupt

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = collect(root, date(2026, 8, 1), date(2026, 8, 31), transport=transport)
            self.assertEqual(json.loads(path.read_text())["status"], "interrupted")
            with self.assertRaises(ValueError):
                verified_snapshot(root, path)
