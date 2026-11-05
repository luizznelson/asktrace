"""Separate maintenance, query and runtime-state credentials; verify remote TLS."""

import os

import certifi
import psycopg
from dotenv import load_dotenv
from psycopg.conninfo import conninfo_to_dict

VARIABLES = {
    "reader": "ASKTRACE_DATABASE_URL",
    "admin": "ASKTRACE_ADMIN_DATABASE_URL",
    "state": "ASKTRACE_STATE_DATABASE_URL",
}


def options(root, role="reader"):
    load_dotenv(root / ".env", override=False)
    value = os.environ.get(VARIABLES[role])
    if value:
        try:
            result = conninfo_to_dict(value)
        except Exception:
            raise ValueError("invalid_database_configuration") from None
        if not all(result.get(key) for key in ("host", "dbname", "user", "password")):
            raise ValueError("incomplete_database_configuration")
        if "," in result["host"] or result.get("hostaddr"):
            raise ValueError("single_database_hostname_required")
        if result["host"] not in {"127.0.0.1", "localhost", "::1"}:
            result.update(sslmode="verify-full", sslrootcert=certifi.where())
        elif os.environ.get("ASKTRACE_PUBLIC_ORIGIN"):
            raise ValueError("public_database_requires_remote_tls")
    else:
        if role == "state" or os.environ.get("ASKTRACE_PUBLIC_ORIGIN"):
            raise ValueError("missing_database_configuration")
        result = {
            "host": "127.0.0.1",
            "port": 15432,
            "user": "asktrace_reader" if role == "reader" else "asktrace",
            "password": os.environ[
                "ASKTRACE_READER_PASSWORD" if role == "reader" else "POSTGRES_PASSWORD"
            ],
            "dbname": os.environ.get("ASKTRACE_DATABASE_NAME", "asktrace"),
        }
    result.update(connect_timeout=10, application_name="asktrace-" + role)
    return result


def connect(root, role="reader", **kwargs):
    return psycopg.connect(**options(root, role), **kwargs)
