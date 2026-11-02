"""Bounded PNCP acquisition with immutable raw pages and explicit coverage."""

import argparse
import calendar
import hashlib
import json
import time
from collections import Counter
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import uuid4

BASE = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"
MAX_BODY = 16 * 1024 * 1024


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def decode(data: bytes) -> dict[str, Any]:
    def nonfinite(value: str) -> None:
        raise ValueError("nonfinite_json")

    result = json.loads(data, parse_float=Decimal, parse_constant=nonfinite)
    if not isinstance(result, dict) or not isinstance(result.get("data"), list):
        raise ValueError("invalid_envelope")
    for key in ("totalRegistros", "totalPaginas", "numeroPagina"):
        if type(result.get(key)) is not int or result[key] < 0:
            raise ValueError("invalid_pagination")
    if result["numeroPagina"] < 1:
        raise ValueError("invalid_page_number")
    if any(not isinstance(row, dict) for row in result["data"]):
        raise ValueError("invalid_record")
    total, pages, page = (result[k] for k in ("totalRegistros", "totalPaginas", "numeroPagina"))
    if total == 0:
        if result["data"] or pages > 1:
            raise ValueError("inconsistent_empty_response")
    elif pages < 1 or page > pages or not result["data"]:
        raise ValueError("inconsistent_pagination")
    if len(result["data"]) > 50 or total < len(result["data"]):
        raise ValueError("invalid_page_size")
    return result


def fetch(params: dict[str, Any]) -> tuple[bytes, int]:
    url = BASE + "?" + urlencode(params)
    for attempt in range(3):
        try:
            request = Request(
                url, headers={"Accept": "application/json", "User-Agent": "AskTrace/0.1"}
            )
            with urlopen(request, timeout=30) as response:
                body = response.read(MAX_BODY + 1)
                if len(body) > MAX_BODY:
                    raise ValueError("response_too_large")
                return body, response.status
        except HTTPError as error:
            if error.code not in {429, 500, 502, 503, 504} or attempt == 2:
                raise RuntimeError(f"pncp_http_{error.code}") from None
            retry_after = error.headers.get("Retry-After", "")
            delay = min(30, int(retry_after)) if retry_after.isdecimal() else 2**attempt
            time.sleep(max(1, delay))
        except URLError, TimeoutError:
            if attempt == 2:
                raise RuntimeError("pncp_connection_failed") from None
            time.sleep(2**attempt)
    raise RuntimeError("pncp_request_failed")


def windows(start: date, end: date) -> list[tuple[date, date]]:
    if start > end:
        raise ValueError("start_after_end")
    result = []
    cursor = start
    while cursor <= end:
        last = min(
            date(cursor.year, cursor.month, calendar.monthrange(cursor.year, cursor.month)[1]), end
        )
        result.append((cursor, last))
        cursor = (
            date(last.year + 1, 1, 1) if last.month == 12 else date(last.year, last.month + 1, 1)
        )
    return result


def amount(value: Any) -> tuple[str | None, str | None]:
    if value is None:
        return None, "missing"
    if isinstance(value, bool) or not isinstance(value, (int, Decimal)):
        return None, "invalid"
    number = Decimal(value)
    if (
        not number.is_finite()
        or number < 0
        or number >= Decimal("1e30")
        or number.as_tuple().exponent < -8
    ):
        return None, "invalid"
    return str(number), None


def normalize(
    row: dict[str, Any], start: date, end: date
) -> tuple[dict[str, Any] | None, list[str]]:
    issues = []
    identifier = row.get("numeroControlePNCP")
    org, unit = row.get("orgaoEntidade"), row.get("unidadeOrgao")
    if not isinstance(identifier, str) or not identifier.strip():
        return None, ["missing_control_id"]
    if not isinstance(org, dict) or not isinstance(unit, dict):
        return None, ["invalid_org_or_unit"]
    cnpj = org.get("cnpj")
    if not isinstance(cnpj, str) or len(cnpj) != 14 or not cnpj.isascii() or not cnpj.isdecimal():
        return None, ["invalid_org_cnpj"]
    if (
        unit.get("ufSigla") != "PI"
        or type(row.get("modalidadeId")) is not int
        or row["modalidadeId"] != 6
    ):
        return None, ["outside_state_or_modality"]
    try:
        published = datetime.fromisoformat(row["dataPublicacaoPncp"]).date()
    except KeyError, TypeError, ValueError:
        return None, ["invalid_publication_date"]
    if not start <= published <= end:
        return None, ["outside_publication_period"]
    estimated, estimated_issue = amount(row.get("valorTotalEstimado"))
    awarded, awarded_issue = amount(row.get("valorTotalHomologado"))
    for field, issue in (("estimated", estimated_issue), ("awarded", awarded_issue)):
        if issue:
            issues.append(f"{field}_{issue}")
    obj = row.get("objetoCompra")
    if not isinstance(obj, str) or not obj.strip():
        issues.append("missing_object")
        obj = None
    return {
        "control_id": identifier,
        "org_cnpj": cnpj,
        "org_name": org.get("razaoSocial") if isinstance(org.get("razaoSocial"), str) else None,
        "unit_code": str(unit.get("codigoUnidade"))
        if unit.get("codigoUnidade") is not None
        else None,
        "municipality_ibge": str(unit.get("codigoIbge"))
        if unit.get("codigoIbge") is not None
        else None,
        "municipality_name": unit.get("municipioNome")
        if isinstance(unit.get("municipioNome"), str)
        else None,
        "uf": "PI",
        "modality": 6,
        "publication_date": published.isoformat(),
        "object_text": obj,
        "estimated_value": estimated,
        "awarded_value": awarded,
    }, issues


def write_json(path: Path, data: Any) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def collect(
    root: Path,
    start: date,
    end: date,
    *,
    transport=fetch,
    interval: float = 1,
    max_pages: int = 2000,
    sample: Path | None = None,
) -> Path:
    run_id = str(uuid4())
    directory = root / "runs" / f"pncp-{run_id}"
    raw = root / "data/raw" / run_id
    processed = root / "data/processed" / run_id
    for folder in (directory, raw, processed):
        folder.mkdir(parents=True, exist_ok=False)
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "run_id": run_id,
        "started_at": datetime.now(UTC).isoformat(),
        "source": BASE,
        "date_start": str(start),
        "date_end": str(end),
        "scope": {"uf": "PI", "modality": 6, "date_basis": "publication", "resource": "purchases"},
        "mode": "sample" if sample else "live",
        "status": "running",
        "pages": [],
        "windows": [],
    }
    counters: Counter[str] = Counter()
    seen: dict[str, str] = {}
    normalized = []
    try:
        for first, last in windows(start, end):
            if sample and manifest["pages"]:
                break
            expected = None
            count = 0
            page = 1
            while True:
                if len(manifest["pages"]) >= max_pages:
                    raise ValueError("page_budget_exceeded")
                params = {
                    "dataInicial": first.strftime("%Y%m%d"),
                    "dataFinal": last.strftime("%Y%m%d"),
                    "codigoModalidadeContratacao": 6,
                    "uf": "PI",
                    "pagina": page,
                    "tamanhoPagina": 50,
                }
                if sample:
                    body, status = sample.read_bytes(), 200
                else:
                    if manifest["pages"]:
                        time.sleep(interval)
                    body, status = transport(params)
                # An empty HTTP response is not evidence of an empty dataset.
                if status != 200:
                    raise ValueError(f"unexpected_http_status_{status}")
                filename = f"{first:%Y%m}-page-{page:05d}.json"
                (raw / filename).write_bytes(body)
                query = {key: value for key, value in params.items() if key != "pagina"}
                meta = {
                    "params": params,
                    "request_sha256": digest(json.dumps(query, sort_keys=True).encode()),
                    "body_sha256": digest(body),
                    "relative_path": (raw / filename).relative_to(root).as_posix(),
                    "fetched_at": datetime.now(UTC).isoformat(),
                    "http_status": status,
                    "page": page,
                }
                manifest["pages"].append(meta)
                document = decode(body)
                meta["records_count"] = len(document["data"])
                pagination = document["totalRegistros"], document["totalPaginas"]
                if document["numeroPagina"] != page or (
                    expected is not None and expected != pagination
                ):
                    raise ValueError("pagination_changed_during_collection")
                expected = pagination
                count += len(document["data"])
                counters["source_records"] += len(document["data"])
                for index, row in enumerate(document["data"]):
                    item, issues = normalize(row, first, last)
                    counters.update(issues)
                    if item is None:
                        counters["rejected_records"] += 1
                        continue
                    control = item["control_id"]
                    record_hash = digest(json.dumps(row, sort_keys=True, default=str).encode())
                    if control in seen:
                        counters["duplicate_ids"] += 1
                        if seen[control] != record_hash:
                            raise ValueError("conflicting_duplicate_id")
                        continue
                    seen[control] = record_hash
                    item.update(source_body_sha256=meta["body_sha256"], source_record_index=index)
                    normalized.append(item)
                if sample or page >= max(1, document["totalPaginas"]):
                    break
                page += 1
            complete = count == expected[0] and page >= expected[1]
            manifest["windows"].append(
                {
                    "start": str(first),
                    "end": str(last),
                    "reported_total": expected[0],
                    "downloaded_records": count,
                    "pagination_complete": complete,
                }
            )
            if not sample and not complete:
                raise ValueError("record_count_drift")
        manifest["status"] = "sample_only" if sample else "complete"
        if counters["rejected_records"] or counters["duplicate_ids"]:
            manifest["status"] = "needs_review"
    except KeyboardInterrupt:
        manifest.update(status="interrupted", error_code="user_interrupted")
    except (OSError, ValueError, RuntimeError) as error:
        manifest.update(status="failed", error_type=type(error).__name__)
        # Only controlled errors, never a response body or provider message.
        manifest["error_code"] = (
            "invalid_json"
            if isinstance(error, (json.JSONDecodeError, UnicodeDecodeError))
            else str(error)
            if type(error) in (ValueError, RuntimeError)
            else "filesystem_error"
        )
    manifest["ended_at"] = datetime.now(UTC).isoformat()
    manifest["quality"] = {**counters, "normalized_records": len(normalized)}
    normalized_path = processed / "purchases.json"
    write_json(normalized_path, normalized)
    manifest["normalized"] = {
        "relative_path": normalized_path.relative_to(root).as_posix(),
        "sha256": digest(normalized_path.read_bytes()),
    }
    write_json(directory / "manifest.json", manifest)
    write_json(
        directory / "quality.json",
        {
            "run_id": run_id,
            "mode": manifest["mode"],
            "status": manifest["status"],
            "scope": manifest["scope"],
            "counts": manifest["quality"],
            "windows": manifest["windows"],
            "limitations": [
                "Not all procurement modalities",
                "Publication period, not signature or payment period",
                "Counts do not prove source completeness or absence of later corrections",
            ],
        },
    )
    return directory / "manifest.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end", type=date.fromisoformat, required=True)
    parser.add_argument("--sample", type=Path)
    parser.add_argument("--max-pages", type=int, default=2000)
    parser.add_argument("--interval", type=float, default=1)
    args = parser.parse_args()
    if args.max_pages < 1 or args.interval < 0 or args.start > args.end:
        parser.error("Invalid date, interval or page budget")
    manifest = collect(
        Path.cwd(),
        args.start,
        args.end,
        sample=args.sample,
        max_pages=args.max_pages,
        interval=args.interval,
    )
    status = json.loads(manifest.read_text(encoding="utf-8"))["status"]
    print(f"{status}: {manifest.relative_to(Path.cwd())}")
    return 0 if status in {"complete", "sample_only"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
