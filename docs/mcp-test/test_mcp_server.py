#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 eunomia-bpf org.
"""Minimal MCP test server supporting stdio and HTTP transports."""

from __future__ import annotations

import argparse
import json
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Optional

PROTOCOL_VERSION = "2025-03-26"
SERVER_NAME = "agentsight-mcp-test-server"
FIXTURE_PATH = Path(__file__).with_name("fixture_note.txt")


def build_tool_definitions() -> list[dict[str, Any]]:
    return [
        {
            "name": "echo",
            "description": "Echo back the provided text.",
            "inputSchema": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        },
        {
            "name": "sum_numbers",
            "description": "Return the sum of a list of numbers.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "numbers": {
                        "type": "array",
                        "items": {"type": "number"},
                    }
                },
                "required": ["numbers"],
            },
        },
        {
            "name": "read_fixture",
            "description": "Read the local fixture file used for MCP testing.",
            "inputSchema": {
                "type": "object",
                "properties": {},
            },
        },
    ]


def make_response(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def make_error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


def tool_result(text: str, *, is_error: bool = False) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": text}],
        "isError": is_error,
    }


def handle_initialize() -> dict[str, Any]:
    return {
        "protocolVersion": PROTOCOL_VERSION,
        "serverInfo": {"name": SERVER_NAME, "version": "0.1.0"},
        "capabilities": {"tools": {}},
    }


def handle_tool_call(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "echo":
        text = str(arguments.get("text", ""))
        return tool_result(f"echo:{text}")

    if name == "sum_numbers":
        raw_numbers = arguments.get("numbers", [])
        if not isinstance(raw_numbers, list):
            return tool_result("numbers must be a list", is_error=True)
        try:
            total = sum(float(item) for item in raw_numbers)
        except (TypeError, ValueError):
            return tool_result("numbers must contain only numeric values", is_error=True)
        return tool_result(f"sum:{total:g}")

    if name == "read_fixture":
        fixture_text = FIXTURE_PATH.read_text(encoding="utf-8").strip()
        return tool_result(f"fixture:{fixture_text}")

    return tool_result(f"unknown tool:{name}", is_error=True)


def handle_request(payload: dict[str, Any]) -> Optional[dict[str, Any]]:
    if not isinstance(payload, dict):
        return make_error(None, -32600, "invalid request")

    request_id = payload.get("id")
    method = payload.get("method")
    params = payload.get("params") or {}

    if method == "initialize":
        return make_response(request_id, handle_initialize())

    if method == "notifications/initialized":
        return None

    if method == "ping":
        return make_response(request_id, {})

    if method == "tools/list":
        return make_response(request_id, {"tools": build_tool_definitions()})

    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if not isinstance(name, str):
            return make_error(request_id, -32602, "tools/call requires a tool name")
        if not isinstance(arguments, dict):
            return make_error(request_id, -32602, "tools/call arguments must be an object")
        return make_response(request_id, handle_tool_call(name, arguments))

    return make_error(request_id, -32601, f"method not found: {method}")


class MCPRequestHandler(BaseHTTPRequestHandler):
    server_version = SERVER_NAME
    protocol_version = "HTTP/1.1"

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send_json({"status": "ok"})
            return
        self.send_error(HTTPStatus.NOT_FOUND, "not found")

    def do_POST(self) -> None:
        if self.path not in ("/messages", "/mcp"):
            self.send_error(HTTPStatus.NOT_FOUND, "not found")
            return

        length_header = self.headers.get("Content-Length")
        if not length_header:
            self.send_error(HTTPStatus.LENGTH_REQUIRED, "content-length required")
            return

        try:
            content_length = int(length_header)
            raw_body = self.rfile.read(content_length)
            payload = json.loads(raw_body.decode("utf-8"))
        except (ValueError, json.JSONDecodeError):
            self._send_json(make_error(None, -32700, "parse error"), status=HTTPStatus.BAD_REQUEST)
            return

        response = handle_request(payload)
        if response is None:
            self.send_response(HTTPStatus.ACCEPTED)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        self._send_json(response)

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[http] {format % args}", file=sys.stderr)

    def _send_json(self, payload: Any, *, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_stdio_server() -> int:
    print("[stdio] MCP test server started", file=sys.stderr)
    for line in sys.stdin:
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            response = make_error(None, -32700, "parse error")
        else:
            response = handle_request(payload)

        if response is not None:
            print(json.dumps(response), flush=True)
    return 0


def run_http_server(host: str, port: int) -> int:
    server = ThreadingHTTPServer((host, port), MCPRequestHandler)
    print(f"[http] MCP test server listening on http://{host}:{port}", file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("[http] shutting down", file=sys.stderr)
    finally:
        server.server_close()
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--transport",
        choices=("stdio", "http"),
        default="stdio",
        help="Transport to expose.",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Listen host for HTTP transport.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Listen port for HTTP transport.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.transport == "stdio":
        return run_stdio_server()
    return run_http_server(args.host, args.port)


if __name__ == "__main__":
    raise SystemExit(main())
