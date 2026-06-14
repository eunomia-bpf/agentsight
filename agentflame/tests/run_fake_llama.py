#!/usr/bin/env python3
"""Tiny local fake llama.cpp-compatible server for end-to-end CLI tests."""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        _ = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        if self.path == "/completion":
            payload = {"content": "debug"}
        else:
            payload = {"choices": [{"message": {"content": "debug"}}]}
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


def main() -> int:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 18080
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
