"""Local-only AskTrace UI; fixed routes, same-origin requests and bounded execution."""

import argparse
import hmac
import json
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from asktrace.agent import run
from asktrace.query import serialize

COVERAGE = "runs/contracts-resume-c1345679-59ea-49ad-af35-be2cc924ceab/coverage.json"
ASSETS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.css": ("app.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
}


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, root, port=8010, runner=run):
        self.root = root.resolve()
        self.token = secrets.token_urlsafe(32)
        self.runner = runner
        self.busy = threading.Lock()
        super().__init__(("127.0.0.1", port), Handler)
        self.origin = f"http://127.0.0.1:{self.server_port}"


class Handler(BaseHTTPRequestHandler):
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
        self.wfile.write(body)

    def valid_host(self):
        return self.headers.get("Host") == urlsplit(self.server.origin).netloc

    def do_GET(self):
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
                    "coverage": COVERAGE,
                    "providers": ["baseline", "fallback"],
                },
            )
        elif path == "/api/evidence":
            # No arbitrary local files, raw responses or .env can be downloaded.
            from asktrace.evidence import read_evidence

            self.send(200, read_evidence(self.server.root, Path(COVERAGE)))
        else:
            self.send(404, {"error": "not_found"})

    def do_POST(self):
        if (
            not self.valid_host()
            or self.headers.get("Origin") != self.server.origin
            or not hmac.compare_digest(self.headers.get("X-AskTrace-Token", ""), self.server.token)
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
            length = int(self.headers.get("Content-Length", "0"))
            if not 1 <= length <= 8192:
                raise ValueError("invalid_body_size")
            self.connection.settimeout(5)
            data = json.loads(self.rfile.read(length))
            if (
                not isinstance(data, dict)
                or set(data) != {"question", "provider"}
                or data["provider"] not in {"baseline", "fallback"}
                or not isinstance(data["question"], str)
                or not 1 <= len(data["question"].strip()) <= 1000
            ):
                raise ValueError("invalid_question")
        except ValueError, TypeError, OSError:
            self.send(400, {"error": "invalid_request"})
            return
        if not self.server.busy.acquire(blocking=False):
            self.send(429, {"error": "busy"})
            return
        try:
            result = self.server.runner(
                self.server.root, Path(COVERAGE), data["question"], data["provider"]
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
