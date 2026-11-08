"""Loopback HTTP adapter for the Lambda handler; requires a DynamoDB endpoint."""

import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from src.app import lambda_handler


class Handler(BaseHTTPRequestHandler):
    def do_request(self):
        url = urlsplit(self.path)
        size = int(self.headers.get("Content-Length", "0"))
        if size > 16384:
            self.send_response(413)
            self.end_headers()
            return
        body = self.rfile.read(size).decode("utf-8", errors="replace")
        result = lambda_handler(
            {
                "rawPath": url.path,
                "headers": dict(self.headers),
                "body": body,
                "queryStringParameters": {k: v[-1] for k, v in parse_qs(url.query).items()},
                "requestContext": {"http": {"method": self.command}},
            },
            None,
        )
        self.send_response(result["statusCode"])
        for key, value in result["headers"].items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(result["body"].encode())

    do_GET = do_POST = do_PATCH = do_DELETE = do_OPTIONS = do_PUT = do_request

    def log_message(self, *_):
        pass  # Do not log request bodies or query strings.


if __name__ == "__main__":
    if len(os.environ.get("DEMO_TOKEN", "")) < 32:
        raise SystemExit("Set DEMO_TOKEN to at least 32 characters")
    print("Local API: http://127.0.0.1:8001", flush=True)
    ThreadingHTTPServer(("127.0.0.1", 8001), Handler).serve_forever()
