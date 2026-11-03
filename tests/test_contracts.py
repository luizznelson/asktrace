"""Contract relation, provenance and transactional loading checks."""

import json
import os
import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from asktrace import contracts
from asktrace.database import load as load_purchases
from asktrace.ingest import collect as collect_purchases


def snapshot(root):
    raw = {
        "numeroControlePNCP": "synthetic-purchase",
        "anoCompra": 2026,
        "sequencialCompra": 1,
        "orgaoEntidade": {"cnpj": "00000000000000"},
        "unidadeOrgao": {"ufSigla": "PI"},
        "modalidadeId": 6,
        "dataPublicacaoPncp": "2026-08-01T00:00:00",
        "objetoCompra": "synthetic",
        "valorTotalEstimado": 10,
        "valorTotalHomologado": None,
    }
    body = json.dumps(
        {"data": [raw], "totalRegistros": 1, "totalPaginas": 1, "numeroPagina": 1}
    ).encode()
    path = collect_purchases(
        root, date(2026, 8, 1), date(2026, 8, 31), transport=lambda params: (body, 200), interval=0
    )
    return path


def response(ids=("contract-1", "contract-2"), page=1, pages=1, total=None):
    data = [
        {
            "numeroControlePNCP": identifier,
            "numeroControlePNCPCompra": "synthetic-purchase",
            "valorInicial": 1,
            "valorGlobal": None,
        }
        for identifier in ids
    ]
    return json.dumps(
        {
            "data": data,
            "totalRegistros": len(data) if total is None else total,
            "numeroPagina": page,
            "totalPaginas": pages,
        }
    ).encode()


class ContractTests(unittest.TestCase):
    def test_multi_page_collection_and_missing_page(self):
        from urllib.parse import parse_qs, urlparse

        def transport(url):
            query = parse_qs(urlparse(url).query)
            self.assertEqual(query["tamanhoPagina"], ["50"])
            number = int(query["pagina"][0])
            return response((f"contract-{number}",), number, 2, 2), 200

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            parent = snapshot(root)
            path = contracts.collect(root, parent, 1, transport, 0)
            manifest, _ = contracts.verify(root, path)
            self.assertEqual(len(manifest["requests"][0]["pages"]), 2)
            self.assertEqual([row["source_record_index"] for row in manifest["contracts"]], [0, 1])
            limited = contracts.collect(root, parent, 1, transport, 0, max_pages=1)
            with self.assertRaisesRegex(ValueError, "only_complete"):
                contracts.verify(root, limited)

    def test_pagination_changes_and_duplicates_are_rejected(self):
        for second in (
            response(("b",), 2, 2, 3),
            response(("a",), 2, 2, 2),
            response(("b",), 1, 2, 2),
        ):
            pages = [
                {"http_status": 200, "body": response(("a",), 1, 2, 2)},
                {"http_status": 200, "body": second},
            ]
            with self.assertRaises(ValueError):
                contracts.replay(pages, "synthetic-purchase", lambda page: page["body"])

    def test_explicit_unpublished_message_is_distinct_from_generic_404(self):
        body = json.dumps(
            {"status": "404", "message": "Não há contrato publicado no PNCP para esta contratação."}
        ).encode()
        self.assertEqual(contracts.parse(body, 404, "x"), ([], "none_returned"))
        self.assertEqual(
            contracts.replay([{"http_status": 404}], "x", lambda page: body), ([], "none_returned")
        )
        generic = json.dumps({"status": "404", "message": "Not found"}).encode()
        self.assertEqual(contracts.parse(generic, 404, "x"), ([], "request_failed"))
        self.assertEqual(contracts.parse(body, 503, "x"), ([], "request_failed"))

    def test_one_to_many_and_unknown_amount(self):
        rows, status = contracts.parse(response(), 200, "synthetic-purchase")
        self.assertEqual(status, "with_contracts")
        self.assertEqual(len(rows), 2)
        self.assertIsNone(rows[0]["global_value"])

    def test_empty_is_not_failed(self):
        self.assertEqual(contracts.parse(response(()), 200, "x"), ([], "none_returned"))
        self.assertEqual(contracts.parse(b"", 204, "x"), ([], "none_returned"))
        for code in (404, 429, 503, 0):
            self.assertEqual(contracts.parse(b"", code, "x"), ([], "request_failed"))

    def test_bad_link_duplicate_and_nonfinite_rejected(self):
        for body in (response(), response(("a", "a")), b"[NaN]", b"{}"):
            with self.assertRaises(ValueError):
                contracts.parse(body, 200, "other-purchase")
        with self.assertRaises(ValueError):
            contracts.parse(response(("a", "a")), 200, "synthetic-purchase")

    def test_integrity_and_derived_data_verified(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            parent = snapshot(root)
            path = contracts.collect(root, parent, 1, lambda url: (response(), 200), 0)
            manifest, _ = contracts.verify(root, path)
            self.assertEqual(manifest["quality"]["contracts"], 2)
            manifest["contracts"][0]["global_value"] = "999"
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "normalized_contracts_mismatch"):
                contracts.verify(root, path)

    def test_failed_and_interrupted_not_loadable(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            parent = snapshot(root)
            for transport in (
                lambda url: (b"", 503),
                lambda url: (_ for _ in ()).throw(KeyboardInterrupt()),
            ):
                path = contracts.collect(root, parent, 1, transport, 0)
                with self.assertRaisesRegex(ValueError, "only_complete"):
                    contracts.verify(root, path)

    def test_invalid_amount_and_uppercase_alias(self):
        raw = json.loads(response(("a",)))
        for value in (-1, True, "12", 1e40):
            raw["data"][0]["valorInicial"] = value
            with self.assertRaisesRegex(ValueError, "invalid_contract_amount"):
                contracts.parse(json.dumps(raw).encode(), 200, "synthetic-purchase")

    def test_failed_requests_retried_without_sleeping_in_tests(self):
        from urllib.error import HTTPError

        error = HTTPError("https://pncp.gov.br", 503, "Unavailable", {}, None)
        with patch.object(contracts, "urlopen", side_effect=error) as request:
            with patch.object(contracts.time, "sleep"):
                _, code = contracts.fetch("https://pncp.gov.br")
        self.assertEqual(code, 503)
        self.assertEqual(request.call_count, 3)

    def test_source_tampering(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = contracts.collect(root, snapshot(root), 1, lambda url: (response(()), 200), 0)
            manifest = json.loads(path.read_bytes())
            (root / manifest["requests"][0]["pages"][0]["relative_path"]).write_bytes(b"[{}]")
            with self.assertRaisesRegex(ValueError, "source_hash_mismatch"):
                contracts.verify(root, path)


@unittest.skipUnless(os.environ.get("ASKTRACE_TEST_DATABASE") == "1", "PostgreSQL opt-in")
class ContractDatabaseTests(unittest.TestCase):
    def test_load_idempotency_and_rollback(self):
        import psycopg
        from dotenv import load_dotenv

        load_dotenv(Path(__file__).parents[1] / ".env", override=False)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            shutil.copytree(Path(__file__).parents[1] / "sql", root / "sql")
            parent = snapshot(root)
            with patch.dict(os.environ, {"ASKTRACE_DATABASE_NAME": "asktrace_test"}):
                load_purchases(root, parent)
                path = contracts.collect(root, parent, 1, lambda url: (response(), 200), 0)
                self.assertEqual(contracts.load(root, path), "loaded")
                self.assertEqual(contracts.load(root, path), "already_loaded")
                failed = contracts.collect(root, parent, 1, lambda url: (response(), 200), 0)
                # Inject an error after coverage INSERTs, inside the transaction.
                original = contracts.verify

                def invalid(*args):
                    manifest, checksum = original(*args)
                    manifest["contracts"][0]["initial_value"] = "-1"
                    return manifest, checksum

                with patch.object(contracts, "verify", side_effect=invalid):
                    with self.assertRaises(psycopg.errors.CheckViolation):
                        contracts.load(root, failed)
                with psycopg.connect(
                    host="127.0.0.1",
                    port=15432,
                    dbname="asktrace_test",
                    user="asktrace",
                    password=os.environ["POSTGRES_PASSWORD"],
                ) as db:
                    run_id = json.loads(failed.read_bytes())["run_id"]
                    self.assertEqual(
                        db.execute(
                            "SELECT count(*) FROM asktrace.contract_runs WHERE run_id=%s", (run_id,)
                        ).fetchone()[0],
                        0,
                    )


if __name__ == "__main__":
    unittest.main()
