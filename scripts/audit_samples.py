"""Audit local PNCP pages without publishing individual supplier records."""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def reject_constant(value: str) -> None:
    raise ValueError("nonfinite_json")


def inspect(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"file": path.name, "complete_dataset": False}
    try:
        content = path.read_bytes()
        result["sha256"] = hashlib.sha256(content).hexdigest()
        body = json.loads(content, parse_constant=reject_constant)
        if not isinstance(body, dict) or not isinstance(body.get("data"), list):
            raise ValueError("invalid_envelope")
        total, pages, page = (
            body.get(key) for key in ("totalRegistros", "totalPaginas", "numeroPagina")
        )
        if any(type(value) is not int for value in (total, pages, page)):
            raise ValueError("invalid_pagination")
        if total < 0 or pages < 0 or page < 1:
            raise ValueError("invalid_pagination")
        records = body["data"]
        if any(not isinstance(row, dict) for row in records):
            raise ValueError("invalid_record")
        if total < len(records) or (pages > 0 and page > pages):
            raise ValueError("inconsistent_pagination")
        if (total == 0 and (records or pages > 1)) or (total > 0 and (pages == 0 or not records)):
            raise ValueError("inconsistent_pagination")
        if body.get("empty", not records) is not (not records):
            raise ValueError("inconsistent_empty_flag")
        remaining = body.get("paginasRestantes")
        if remaining is not None and (
            type(remaining) is not int or remaining != max(0, pages - page)
        ):
            raise ValueError("inconsistent_remaining_pages")
        states: set[str] = set()
        missing_states = 0
        for row in records:
            unit = row.get("unidadeOrgao")
            if unit is not None and not isinstance(unit, dict):
                raise ValueError("invalid_unit")
            state = (unit or {}).get("ufSigla")
            if state is None:
                missing_states += 1
            elif not isinstance(state, str) or len(state) != 2 or not state.isalpha():
                raise ValueError("invalid_state")
            else:
                states.add(state.upper())
        ids = [row.get("numeroControlePNCP") for row in records]
        known_ids = [value for value in ids if isinstance(value, str) and value.strip()]
        result.update(
            status="valid_page",
            downloaded_records=len(records),
            reported_total=total,
            reported_pages=pages,
            page=page,
            complete_dataset=pages <= 1 and total == len(records),
            missing_ids=len(ids) - len(known_ids),
            duplicate_ids=len(known_ids) - len(set(known_ids)),
            states=sorted(states),
            missing_states=missing_states,
        )
    except OSError:
        result.update(status="unreadable_file", error="file_read_failed")
    except (ValueError, TypeError) as error:
        code = str(error)
        known_codes = {
            "invalid_envelope",
            "invalid_pagination",
            "invalid_record",
            "invalid_unit",
            "invalid_state",
            "inconsistent_pagination",
            "inconsistent_empty_flag",
            "inconsistent_remaining_pages",
            "nonfinite_json",
        }
        result.update(status="invalid_page", error=code if code in known_codes else "invalid_json")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.directory.is_dir():
        parser.error("Input must be an existing directory")
    files = sorted(args.directory.glob("*.json"))
    if not files:
        parser.error("No JSON sample files found")
    if args.output.resolve().is_relative_to(args.directory.resolve()):
        parser.error("Store the report outside the input directory")
    if args.output.exists():
        parser.error("Output already exists; choose a new report path")
    results = [inspect(path) for path in files]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation prevents silently overwriting an existing report.
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(
            {"scope": "local samples, not full ingestion", "files": results}, stream, indent=2
        )
        stream.write("\n")
    invalid = sum(row["status"] != "valid_page" for row in results)
    print(f"Audited {len(results)} files; invalid: {invalid}")
    return 1 if invalid else 0


if __name__ == "__main__":
    raise SystemExit(main())
