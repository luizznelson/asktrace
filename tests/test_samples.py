import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "audit_samples", Path(__file__).parents[1] / "scripts/audit_samples.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SampleTests(unittest.TestCase):
    def check_page(self, body):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "page.json"
            path.write_bytes(body if isinstance(body, bytes) else json.dumps(body).encode())
            return module.inspect(path)

    def test_empty_file_is_not_success(self):
        self.assertEqual(self.check_page(b"")["status"], "invalid_page")

    def test_partial_page_is_not_complete_dataset(self):
        row = self.check_page(
            {
                "data": [{"numeroControlePNCP": "a"}],
                "totalRegistros": 454,
                "totalPaginas": 10,
                "numeroPagina": 1,
            }
        )
        self.assertFalse(row["complete_dataset"])

    def test_duplicate_and_missing_ids(self):
        row = self.check_page(
            {
                "data": [{"numeroControlePNCP": "a"}, {"numeroControlePNCP": "a"}, {}],
                "totalRegistros": 3,
                "totalPaginas": 1,
                "numeroPagina": 1,
            }
        )
        self.assertEqual((row["duplicate_ids"], row["missing_ids"]), (1, 1))

    def test_bad_pagination_rejected(self):
        row = self.check_page(
            {"data": [], "totalRegistros": 10, "totalPaginas": 2, "numeroPagina": 3}
        )
        self.assertEqual(row["status"], "invalid_page")

    def test_boolean_pagination_rejected(self):
        row = self.check_page(
            {"data": [], "totalRegistros": False, "totalPaginas": 0, "numeroPagina": 0}
        )
        self.assertEqual(row["status"], "invalid_page")

    def test_invalid_unit_is_reported_without_crashing(self):
        row = self.check_page(
            {
                "data": [{"unidadeOrgao": "bad"}],
                "totalRegistros": 1,
                "totalPaginas": 1,
                "numeroPagina": 1,
            }
        )
        self.assertEqual(row["error"], "invalid_unit")

    def test_positive_total_without_pages_rejected(self):
        row = self.check_page(
            {"data": [], "totalRegistros": 10, "totalPaginas": 0, "numeroPagina": 1}
        )
        self.assertEqual(row["status"], "invalid_page")

    def test_nonfinite_json_rejected(self):
        row = self.check_page(b'{"data":[],"totalRegistros":NaN}')
        self.assertEqual(row["error"], "nonfinite_json")

    def test_empty_response_can_be_valid_without_being_failure(self):
        row = self.check_page(
            {"data": [], "totalRegistros": 0, "totalPaginas": 0, "numeroPagina": 1, "empty": True}
        )
        self.assertEqual(row["status"], "valid_page")
        self.assertTrue(row["complete_dataset"])

    def test_inconsistent_remaining_pages_rejected(self):
        row = self.check_page(
            {
                "data": [{}],
                "totalRegistros": 2,
                "totalPaginas": 2,
                "numeroPagina": 1,
                "paginasRestantes": 0,
            }
        )
        self.assertEqual(row["error"], "inconsistent_remaining_pages")

    def test_missing_file_is_reported_without_exposing_path(self):
        row = module.inspect(Path("nonexistent-sample.json"))
        self.assertEqual(row["status"], "unreadable_file")
        self.assertNotIn("sha256", row)

    def test_cli_cannot_overwrite_input_page(self):
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            page = directory / "page.json"
            original = b'{"data": []}'
            page.write_bytes(original)
            with patch("sys.argv", ["audit_samples", str(directory), "--output", str(page)]):
                with self.assertRaises(SystemExit) as failure:
                    module.main()
            self.assertEqual(failure.exception.code, 2)
            self.assertEqual(page.read_bytes(), original)

    def test_cli_cannot_overwrite_previous_report(self):
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder) / "samples"
            directory.mkdir()
            (directory / "page.json").write_text('{"data": []}', encoding="utf-8")
            output = Path(folder) / "report.json"
            output.write_text("preserved", encoding="utf-8")
            with patch("sys.argv", ["audit_samples", str(directory), "--output", str(output)]):
                with self.assertRaises(SystemExit):
                    module.main()
            self.assertEqual(output.read_text(encoding="utf-8"), "preserved")
