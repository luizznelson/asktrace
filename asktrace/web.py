"""Local-only AskTrace UI; fixed routes, same-origin requests and bounded execution."""

import argparse
import hmac
import json
import re
import secrets
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from asktrace.agent import run
from asktrace.evidence import read_evidence
from asktrace.providers import availability
from asktrace.query import VerifiedDataset, dataset, serialize

COVERAGE = "runs/contracts-resume-c1345679-59ea-49ad-af35-be2cc924ceab/coverage.json"
ASSETS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.css": ("app.css", "text/css; charset=utf-8"),
    "/formatters.js": ("formatters.js", "text/javascript; charset=utf-8"),
    "/presentation.js": ("presentation.js", "text/javascript; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
}


class Application:
    def __init__(self, root, runner=run, *, verified_runtime=False):
        self.root = root.resolve()
        config_path = self.root / "config/datasets.json"
        self.datasets = (
            json.loads(config_path.read_bytes())
            if config_path.exists()
            else {"default": "original", "datasets": [{"id": "original", "coverage": COVERAGE}]}
        )
        self.catalog = []
        self.verified_datasets = {}
        for item in self.datasets["datasets"]:
            manifest, purchases, covered, checksum = dataset(
                self.root, self.root / item["coverage"]
            )
            if verified_runtime:
                report = self.root / item["coverage"]
                self.verified_datasets[report.resolve()] = VerifiedDataset.capture(
                    self.root, report, (manifest, purchases, covered, checksum)
                )
            coverage_report = json.loads(read_evidence(self.root, Path(item["coverage"])))
            self.catalog.append(
                {
                    "id": item["id"],
                    "coverage": item["coverage"],
                    "start": manifest["date_start"],
                    "end": manifest["date_end"],
                    "purchases": len(purchases),
                    "covered": len(covered),
                    "contracts": len({cid for row in covered.values() for cid in row["contracts"]}),
                    "unknown_awarded": sum(row["awarded_value"] is None for row in purchases),
                    "excluded": len(coverage_report.get("excluded_purchases", [])),
                    "coverage_finished_at": coverage_report.get("finished_at"),
                    "example_purchase_id": next(
                        (
                            identifier
                            for identifier, row in covered.items()
                            if row["contracts"]
                            and re.fullmatch(r"\d{14}-1-\d{6}/\d{4}", identifier)
                        ),
                        None,
                    ),
                    "coverage_sha256": checksum,
                }
            )
        self.token = secrets.token_urlsafe(32)
        self.runner = self.run_verified if verified_runtime and runner is run else runner
        self.busy = threading.Lock()
        self.default_coverage = next(
            row["coverage"] for row in self.catalog if row["id"] == self.datasets["default"]
        )

    def run_verified(self, root, report, question, provider="baseline"):
        verified = self.verified_datasets[(root / report).resolve()]
        return run(root, report, question, provider, verified=verified)


class Server(Application, ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        ThreadingHTTPServer.server_bind(self)

    def __init__(self, root, port=8010, runner=run):
        Application.__init__(self, root, runner)
        ThreadingHTTPServer.__init__(self, ("127.0.0.1", port), Handler)
        self.origin = f"http://127.0.0.1:{self.server_port}"


class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    def log_message(self, *_):
        pass  # Questions, payloads and credentials never enter access logs.

    def send(self, status, body, content_type="application/json; charset=utf-8"):
        if not isinstance(body, bytes):
            body = json.dumps(body, default=serialize, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; "
            "style-src 'self'; connect-src 'self'; img-src 'self'; "
            "frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
        )
        self.end_headers()
        try:
            self.wfile.write(body)
        except OSError:
            self.close_connection = True  # A disconnected tab is not a query failure.

    def valid_host(self):
        return self.headers.get("Host") == urlsplit(self.server.origin).netloc

    def availability_snapshot(self):
        try:
            return availability(self.server.root)
        except OSError, ValueError, KeyError, TypeError, RecursionError:
            # Do not erase a corrupt quota record or prevent local-rule exploration.
            return {
                "can_attempt_ai": False,
                "status": "unknown",
                "database_checked": False,
                "candidates": [],
            }

    def do_GET(self):
        try:
            self.get_resource()
        except OSError, ValueError, KeyError, TypeError, RecursionError:
            self.send(503, {"error": "resource_unavailable"})

    def get_resource(self):
        if not self.valid_host():
            self.send(403, {"error": "invalid_host"})
            return
        path = urlsplit(self.path).path
        if path in ASSETS:
            name, mime = ASSETS[path]
            self.send(200, (self.server.root / "web" / name).read_bytes(), mime)
        elif path == "/api/session":
            self.send(
                200,
                {
                    "token": self.server.token,
                    "mode": "local",
                    "coverage": self.server.default_coverage,
                    "datasets": self.server.catalog,
                    "default_dataset": self.server.datasets["default"],
                    "providers": ["baseline", "fallback"],
                    "availability": self.availability_snapshot(),
                },
            )
        elif path == "/api/availability":
            snapshot = self.availability_snapshot()
            self.send(503 if snapshot.get("status") == "unknown" else 200, snapshot)
        elif path == "/api/evidence":
            # No arbitrary local files, raw responses or .env can be downloaded.
            identifier = parse_qs(urlsplit(self.path).query).get("dataset", [None])[0]
            selected = next((row for row in self.server.catalog if row["id"] == identifier), None)
            if identifier and selected is None:
                self.send(404, {"error": "unknown_dataset"})
                return
            self.send(
                200,
                read_evidence(
                    self.server.root,
                    Path(selected["coverage"] if selected else self.server.default_coverage),
                ),
            )
        else:
            self.send(404, {"error": "not_found"})

    def do_POST(self):
        token = self.headers.get("X-AskTrace-Token", "")
        if (
            not token.isascii()
            or not self.valid_host()
            or self.headers.get("Origin") != self.server.origin
            or not hmac.compare_digest(token, self.server.token)
        ):
            self.send(403, {"error": "invalid_session"})
            return
        if self.path != "/api/ask":
            self.send(404, {"error": "not_found"})
            return
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            self.send(415, {"error": "json_required"})
            return
        try:
            if (
                self.headers.get("Transfer-Encoding") is not None
                or len(self.headers.get_all("Content-Length", [])) != 1
            ):
                raise ValueError("ambiguous_body_framing")
            length = int(self.headers.get("Content-Length", "0"))
            if not 1 <= length <= 8192:
                raise ValueError("invalid_body_size")
            self.connection.settimeout(5)
            data = json.loads(self.rfile.read(length))
            if (
                not isinstance(data, dict)
                or set(data) not in ({"question", "provider"}, {"question", "provider", "dataset"})
                or data["provider"] not in {"baseline", "fallback"}
                or not isinstance(data["question"], str)
                or not 1 <= len(data["question"].strip()) <= 1000
            ):
                raise ValueError("invalid_question")
        except ValueError, TypeError, OSError, RecursionError:
            self.send(400, {"error": "invalid_request"})
            return
        selected = next(
            (row for row in self.server.catalog if row["id"] == data.get("dataset")), None
        )
        if "dataset" in data and selected is None:
            self.send(400, {"error": "unknown_dataset"})
            return
        if not self.server.busy.acquire(blocking=False):
            self.send(429, {"error": "busy"})
            return
        try:
            result = self.server.runner(
                self.server.root,
                Path(selected["coverage"] if selected else self.server.default_coverage),
                data["question"],
                data["provider"],
            )
            self.send(200, result)
        except Exception:
            self.send(503, {"error": "query_unavailable"})
        finally:
            self.server.busy.release()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8010)
    args = parser.parse_args()
    server = Server(Path.cwd(), args.port)
    print(f"AskTrace local: {server.origin}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
