"""Public same-origin ASGI entry point; fixed routes and a separate read-only data login."""

import asyncio
import hmac
import json
import os
import re
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.responses import Response
from psycopg.rows import dict_row

from asktrace.connections import connect
from asktrace.deployment_data import restore_database_artifact
from asktrace.evidence import read_evidence
from asktrace.providers import availability
from asktrace.query import serialize
from asktrace.runtime_state import reserve
from asktrace.web import ASSETS, Application

SECURITY_HEADERS = {
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; "
    "connect-src 'self'; img-src 'self'; frame-ancestors 'none'; "
    "base-uri 'none'; form-action 'self'",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Strict-Transport-Security": "max-age=31536000",
}


def response(status, data, mime="application/json; charset=utf-8"):
    body = (
        data
        if isinstance(data, bytes)
        else json.dumps(data, default=serialize, ensure_ascii=False).encode()
    )
    return Response(body, status_code=status, headers={**SECURITY_HEADERS, "Content-Type": mime})


def public_origin(value):
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.path
        or parsed.query
        or parsed.fragment
        or value != f"https://{parsed.netloc}"
        or not re.fullmatch(r"[a-zA-Z0-9.-]+(?::443)?", parsed.netloc)
    ):
        raise ValueError("public_https_origin_required")
    return value


def check_database(root):
    with connect(root, row_factory=dict_row) as db:
        role = db.execute(
            "SELECT rolsuper, rolcreatedb, rolcreaterole FROM pg_roles WHERE rolname=current_user"
        ).fetchone()
        allowed = db.execute(
            "SELECT has_table_privilege(current_user, 'asktrace.report_purchases', 'SELECT') "
            "AS can_read, has_table_privilege(current_user, 'asktrace.purchases', 'INSERT') "
            "AS can_insert"
        ).fetchone()
        readonly = db.execute("SHOW transaction_read_only").fetchone()["transaction_read_only"]
        if (
            any(role.values())
            or readonly != "on"
            or allowed != {"can_read": True, "can_insert": False}
        ):
            raise ValueError("read_only_database_role_required")
    with connect(root, "state", row_factory=dict_row) as db:
        role = db.execute(
            "SELECT rolsuper, rolcreatedb, rolcreaterole FROM pg_roles WHERE rolname=current_user"
        ).fetchone()
        permissions = db.execute(
            "SELECT has_table_privilege(current_user, 'asktrace.runtime_state', 'UPDATE') "
            "AS state_write, has_table_privilege(current_user, 'asktrace.purchases', 'SELECT') "
            "AS data_read, has_table_privilege(current_user, 'asktrace.purchases', 'INSERT') "
            "AS data_write"
        ).fetchone()
        if any(role.values()) or permissions != {
            "state_write": True,
            "data_read": False,
            "data_write": False,
        }:
            raise ValueError("isolated_runtime_state_role_required")


def create_app(root=None, application=None, reserver=reserve, checker=check_database):
    root = (root or Path.cwd()).resolve()
    origin = public_origin(
        os.environ.get("ASKTRACE_PUBLIC_ORIGIN") or os.environ.get("RENDER_EXTERNAL_URL", "")
    )
    ai_enabled = os.environ.get("ASKTRACE_PUBLIC_AI", "false").lower() == "true"
    daily_limit = int(os.environ.get("ASKTRACE_DAILY_AI_LIMIT", "10"))
    if not 1 <= daily_limit <= 100:
        raise ValueError("invalid_public_ai_limit")

    @asynccontextmanager
    async def lifespan(app):
        try:
            if application is None:
                os.environ.setdefault("ASKTRACE_PUBLIC_ORIGIN", origin)
                if os.environ.get("ASKTRACE_ADMIN_DATABASE_URL"):
                    raise ValueError("maintenance_credentials_forbidden_in_public_runtime")
                checker(root)
                restore_database_artifact(root, os.environ.get("ASKTRACE_DATA_SHA256", ""))
            else:
                checker(root)
            app.state.context = application or Application(root, verified_runtime=True)
        except Exception:
            raise RuntimeError("public_startup_verification_failed") from None
        yield

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware("http")
    async def boundary(request, call_next):
        if request.headers.getlist("host") != [urlsplit(origin).netloc]:
            return response(403, {"error": "invalid_host"})
        try:
            result = await call_next(request)
        except Exception:
            return response(503, {"error": "service_unavailable"})
        result.headers.update(SECURITY_HEADERS)
        return result

    @app.get("/healthz")
    async def health():
        try:
            await asyncio.to_thread(checker, root)
            return response(200, {"status": "ok"})
        except Exception:
            return response(503, {"status": "unavailable"})

    def availability_snapshot():
        if not ai_enabled:
            return {
                "can_attempt_ai": False,
                "status": "disabled",
                "database_checked": False,
                "candidates": [],
            }
        try:
            return availability(root)
        except Exception:
            return {
                "can_attempt_ai": False,
                "status": "unknown",
                "database_checked": False,
                "candidates": [],
            }

    @app.get("/api/session")
    async def session():
        context = app.state.context
        return response(
            200,
            {
                "token": context.token,
                "mode": "public",
                "datasets": context.catalog,
                "coverage": context.default_coverage,
                "default_dataset": context.datasets["default"],
                "providers": ["baseline", "fallback"] if ai_enabled else ["baseline"],
                "availability": await asyncio.to_thread(availability_snapshot),
            },
        )

    @app.get("/api/availability")
    async def provider_availability():
        data = await asyncio.to_thread(availability_snapshot)
        return response(503 if data.get("status") == "unknown" else 200, data)

    @app.get("/api/evidence")
    async def evidence(request: Request):
        context = app.state.context
        identifier = request.query_params.get("dataset", context.datasets["default"])
        item = next((row for row in context.catalog if row["id"] == identifier), None)
        if item is None:
            return response(404, {"error": "unknown_dataset"})
        return response(200, read_evidence(root, Path(item["coverage"])))

    @app.post("/api/ask")
    async def ask(request: Request):
        context = app.state.context
        tokens = request.headers.getlist("x-asktrace-token")
        if (
            request.headers.getlist("origin") != [origin]
            or len(tokens) != 1
            or not tokens[0].isascii()
            or not hmac.compare_digest(tokens[0], context.token)
        ):
            return response(403, {"error": "invalid_session"})
        if request.headers.get("content-type", "").split(";")[0] != "application/json":
            return response(415, {"error": "json_required"})
        if request.headers.get("content-encoding", "identity") != "identity":
            return response(400, {"error": "invalid_request"})
        try:
            lengths = request.headers.getlist("content-length")
            if len(lengths) != 1 or not 1 <= int(lengths[0]) <= 8192:
                raise ValueError("invalid_body_size")
            if request.headers.get("transfer-encoding"):
                raise ValueError("ambiguous_body_framing")
            body = bytearray()
            async with asyncio.timeout(5):
                async for part in request.stream():
                    body.extend(part)
                    if len(body) > 8192:
                        raise ValueError("body_too_large")
            if len(body) != int(lengths[0]):
                raise ValueError("body_size_mismatch")
            data = json.loads(body)
            if (
                not isinstance(data, dict)
                or set(data) not in ({"question", "provider"}, {"question", "provider", "dataset"})
                or not isinstance(data["question"], str)
                or not 1 <= len(data["question"].strip()) <= 1000
                or data["provider"] not in {"baseline", "fallback"}
            ):
                raise ValueError("invalid_question")
        except ValueError, TypeError, KeyError, RecursionError, TimeoutError:
            return response(400, {"error": "invalid_request"})
        identifier = data.get("dataset", context.datasets["default"])
        selected = next((row for row in context.catalog if row["id"] == identifier), None)
        if selected is None:
            return response(400, {"error": "unknown_dataset"})
        if data["provider"] == "fallback" and not ai_enabled:
            return response(503, {"error": "ai_disabled"})
        if not context.busy.acquire(blocking=False):
            return response(429, {"error": "busy"})

        def execute():
            # Release only after the thread ends, including when the HTTP client disconnects.
            try:
                if not reserver(root, data["provider"] == "fallback", daily_limit):
                    return response(429, {"error": "demo_limit"})
                result = context.runner(
                    root, Path(selected["coverage"]), data["question"], data["provider"]
                )
                return response(200, result)
            except Exception:
                return response(503, {"error": "query_unavailable"})
            finally:
                context.busy.release()

        return await asyncio.to_thread(execute)

    @app.get("/{path:path}")
    async def asset(path: str):
        item = ASSETS.get("/" + path)
        if item is None:
            return response(404, {"error": "not_found"})
        name, mime = item
        return response(200, (root / "web" / name).read_bytes(), mime)

    return app
