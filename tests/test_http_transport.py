"""Real loopback redirect must not receive a forwarded authorization header."""

import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request

from asktrace.http_transport import urlopen


class RedirectTests(unittest.TestCase):
    def test_redirect_never_forwards_credentials(self):
        received = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_GET(self):
                received.append(self.path)
                self.send_response(302)
                self.send_header("Location", "/must-not-follow")
                self.end_headers()

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            request = Request(
                f"http://127.0.0.1:{server.server_port}/initial",
                headers={"Authorization": "Bearer fixture-secret"},
            )
            with self.assertRaises(HTTPError) as caught:
                urlopen(request, timeout=2)
            self.assertEqual(caught.exception.code, 302)
            caught.exception.close()
            self.assertEqual(received, ["/initial"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
