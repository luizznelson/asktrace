"""Optional Gemini routing; procurement records and SQL never leave the application."""

import hashlib
import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv

from asktrace.planning import PROMPT

SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "action": {"type": "STRING", "enum": ["summary", "municipalities", "purchase", "refuse"]},
        "purchase_id": {"type": "STRING", "nullable": True},
    },
    "required": ["action", "purchase_id"],
}


class ProviderFailure(RuntimeError):
    def __init__(self, status, limits=None):
        self.http_status = status
        self.limits = limits or {}
        super().__init__("gemini_request_failed")


def quota_details(body):
    """Extract only public quota names/counts and retry time; never messages or project IDs."""
    if len(body) > 65536:
        return {}
    try:
        details = json.loads(body).get("error", {}).get("details", [])
    except ValueError, AttributeError, TypeError:
        return {}
    result = {}
    if not isinstance(details, list):
        return result
    quotas = []
    for detail in details[:10]:
        if not isinstance(detail, dict):
            continue
        if detail.get("@type") == "type.googleapis.com/google.rpc.RetryInfo":
            retry = detail.get("retryDelay", "")
            if isinstance(retry, str) and re.fullmatch(r"[0-9]{1,7}(?:\.[0-9]{1,9})?s", retry):
                result["retry_after_seconds"] = float(retry[:-1])
        if detail.get("@type") == "type.googleapis.com/google.rpc.QuotaFailure":
            violations = detail.get("violations", [])
            if not isinstance(violations, list):
                continue
            for violation in violations[:5]:
                if not isinstance(violation, dict):
                    continue
                fields = {}
                for key in ("quotaMetric", "quotaId", "quotaValue"):
                    value = violation.get(key)
                    if isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_./-]{1,200}", value):
                        fields[key] = value
                if fields:
                    quotas.append(fields)
    if quotas:
        result["quotas"] = quotas
    return result


def plan(root, question, model=None, timeout=30):
    load_dotenv(root / ".env", override=False)
    key = os.environ.get("GEMINI_API_KEY")
    model = model or os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    if not key or not re.fullmatch(r"gemini-[a-zA-Z0-9.\-]+", model):
        raise ValueError("configure_gemini_key_and_valid_model")
    payload = {
        "systemInstruction": {"parts": [{"text": PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": question}]}],
        "generationConfig": {
            "temperature": 0,
            "maxOutputTokens": 1024,
            "responseMimeType": "application/json",
            "responseSchema": SCHEMA,
        },
    }
    request = Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read(128 * 1024 + 1)
            if len(body) > 128 * 1024:
                raise ValueError("provider_response_too_large")
    except HTTPError as error:
        try:
            limits = quota_details(error.read(65537)) if error.code == 429 else {}
        except OSError, AttributeError, TypeError:
            limits = {}
        raise ProviderFailure(error.code, limits) from None
    except URLError, TimeoutError:
        raise ProviderFailure(0) from None
    data = json.loads(body)
    candidates = data.get("candidates", [])
    if len(candidates) != 1 or candidates[0].get("finishReason") != "STOP":
        raise ValueError("incomplete_provider_plan")
    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(part.get("text", "") for part in parts if not part.get("thought"))
    return json.loads(text), {
        "model": model,
        "prompt_sha256": hashlib.sha256(PROMPT.encode()).hexdigest(),
        **data.get("usageMetadata", {}),
    }
