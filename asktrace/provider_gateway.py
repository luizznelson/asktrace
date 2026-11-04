"""Bounded JSON-plan adapters with fixed destinations and no automatic SDK retries."""

import hashlib
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from asktrace.gemini import ProviderFailure
from asktrace.gemini import plan as gemini_plan
from asktrace.planning import current_prompt

KEYS = {"groq": "GROQ_API_KEY", "openrouter": "OPENROUTER_API_KEY", "gemini": "GEMINI_API_KEY"}
URLS = {
    "groq": "https://api.groq.com/openai/v1/chat/completions",
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
    "ollama": "http://127.0.0.1:11434/api/chat",
}
SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": ["summary", "municipalities", "purchase", "refuse"]},
        "purchase_id": {"type": ["string", "null"]},
    },
    "required": ["action", "purchase_id"],
    "additionalProperties": False,
}


def payload(candidate, question):
    system_prompt = current_prompt()
    if candidate["model"] == "google/gemma-4-26b-a4b-it:free":
        system_prompt += "\nRetorne apenas JSON com duas chaves: action e purchase_id."
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": question}]
    provider = candidate["provider"]
    if provider == "ollama":
        return {
            "model": candidate["model"],
            "messages": messages,
            "stream": False,
            "format": SCHEMA,
            "options": {"temperature": 0, "num_predict": 1024},
        }
    data = {
        "model": candidate["model"],
        "messages": messages,
        "temperature": 0,
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "asktrace_plan", "strict": True, "schema": SCHEMA},
        },
    }
    data["max_completion_tokens" if provider == "groq" else "max_tokens"] = 1024
    if candidate["model"] == "google/gemma-4-26b-a4b-it:free":
        data["response_format"] = {"type": "json_object"}
    if provider == "openrouter":
        if candidate["model"] in {
            "nvidia/nemotron-3.5-super-vl:free",
            "xingchen-agi/xing4.0-29b-a4b:free",
        }:
            data["reasoning"] = {"enabled": False}
        # Explicit free model plus zero-price provider filter; no automatic model substitution.
        data["provider"] = {
            "require_parameters": True,
            "max_price": {"prompt": 0, "completion": 0, "request": 0},
        }
    return data


def call(root, candidate, question, timeout):
    provider = candidate["provider"]
    if provider == "gemini":
        return gemini_plan(root, question, model=candidate["model"], timeout=timeout)
    data = payload(candidate, question)
    headers = {"Content-Type": "application/json", "User-Agent": "AskTrace/0.1"}
    if provider != "ollama":
        headers["Authorization"] = "Bearer " + os.environ[KEYS[provider]]
    request = Request(
        URLS[provider], data=json.dumps(data).encode(), headers=headers, method="POST"
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read(128 * 1024 + 1)
    except HTTPError as error:
        retry = error.headers.get("Retry-After", "")
        limits = {"retry_after_seconds": float(retry)} if retry.isdecimal() else {}
        raise ProviderFailure(error.code, limits) from None
    except URLError, TimeoutError, ConnectionError:
        raise ProviderFailure(0) from None
    if len(body) > 128 * 1024:
        raise ValueError("provider_response_too_large")
    parsed = json.loads(body)
    if provider == "ollama":
        if parsed.get("done") is not True:
            raise ValueError("incomplete_provider_plan")
        text = parsed["message"]["content"]
        usage = {key: parsed[key] for key in ("prompt_eval_count", "eval_count") if key in parsed}
    else:
        choices = parsed.get("choices", [])
        if len(choices) != 1 or choices[0].get("finish_reason") != "stop":
            raise ValueError("incomplete_provider_plan")
        text = choices[0]["message"]["content"]
        # Preserve numeric usage, not arbitrary provider metadata or message content.
        usage = {
            key: value
            for key, value in parsed.get("usage", {}).items()
            if key in {"prompt_tokens", "completion_tokens", "total_tokens"}
            and type(value) is int
            and value >= 0
        }
    return json.loads(text), {
        "provider": provider,
        "model": candidate["model"],
        "prompt_sha256": hashlib.sha256(data["messages"][0]["content"].encode()).hexdigest(),
        **usage,
    }
