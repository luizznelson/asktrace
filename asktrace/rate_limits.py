"""Minimized rate-limit hints; never expose error messages, IDs, keys or provider payloads."""

import json
import math
import re
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime


def duration(value):
    if not isinstance(value, str) or len(value) > 80:
        return None
    if re.fullmatch(r"\d+(?:\.\d+)?", value):
        result = float(value)
        return result if math.isfinite(result) else None
    parts = re.findall(r"(\d+(?:\.\d+)?)(ms|s|m|h|d)", value)
    if parts and "".join(number + unit for number, unit in parts) == value:
        return sum(
            float(number) * {"ms": 0.001, "s": 1, "m": 60, "h": 3600, "d": 86400}[unit]
            for number, unit in parts
        )
    return None


def hints(headers, body, now=None):
    result = {}
    now = now or datetime.now(UTC)
    retry = headers.get("Retry-After", "")
    delay = duration(retry)
    if delay is None and retry:
        try:
            date = parsedate_to_datetime(retry)
            delay = max(0, (date - now).total_seconds())
        except ValueError, TypeError, OverflowError:
            pass
    if delay is not None:
        result["retry_after_seconds"] = delay
    for category in ("requests", "tokens"):
        remaining = headers.get(f"x-ratelimit-remaining-{category}", "")
        if isinstance(remaining, str) and remaining.isdecimal():
            result[f"remaining_{category}"] = int(remaining)
        if remaining == "0":
            reset = duration(headers.get(f"x-ratelimit-reset-{category}", ""))
            if reset is not None:
                result["retry_after_seconds"] = max(result.get("retry_after_seconds", 0), reset)
    if len(body) > 65536:
        return result
    try:
        message = json.loads(body).get("error", {}).get("message", "")
    except ValueError, AttributeError, TypeError:
        return result
    if not isinstance(message, str):
        return result
    # Match quota vocabulary only; do not retain arbitrary message substrings.
    for pattern, label in (
        (r"\b(?:RPD|requests per day)\b", "requests_per_day"),
        (r"\b(?:TPD|tokens per day)\b", "tokens_per_day"),
        (r"\b(?:RPM|requests per minute)\b", "requests_per_minute"),
        (r"\b(?:TPM|tokens per minute)\b", "tokens_per_minute"),
    ):
        if re.search(pattern, message, re.I):
            result["limit_kind"] = label
            break
    match = re.search(r"try again in\s+(\d[\d.hms]*)(?:\s|[.,]|$)", message, re.I)
    if match:
        parsed = duration(match.group(1).rstrip("."))
        if parsed is not None:
            result["retry_after_seconds"] = max(result.get("retry_after_seconds", 0), parsed)
    return result
