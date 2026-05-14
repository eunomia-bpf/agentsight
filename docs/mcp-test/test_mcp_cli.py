#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 eunomia-bpf org.
"""Minimal MCP client that exercises the test server over stdio or HTTP."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

SERVER_SCRIPT = Path(__file__).with_name("test_mcp_server.py")


def json_rpc(request_id: int | None, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
    if request_id is not None:
        payload["id"] = request_id
    if params is not None:
        payload["params"] = params
    return payload


def extract_text(result: dict[str, Any]) -> str:
    content = result.get("content") or []
    if not content:
        return ""
    first = content[0]
    if not isinstance(first, dict):
        return ""
    return str(first.get("text", ""))


def assert_no_error(response: dict[str, Any]) -> None:
    if "error" in response:
        raise RuntimeError(f"server returned error: {response['error']}")


class StdioClient:
    def __init__(self) -> None:
        self.proc = subprocess.Popen(
            [sys.executable, str(SERVER_SCRIPT), "--transport", "stdio"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

    def request(self, payload: dict[str, Any]) -> dict[str, Any]:
        assert self.proc.stdin is not None
        assert self.proc.stdout is not None
        self.proc.stdin.write(json.dumps(payload) + "\n")
        self.proc.stdin.flush()

        if "id" not in payload:
            return {}

        line = self.proc.stdout.readline()
        if not line:
            stderr = ""
            if self.proc.stderr is not None:
                stderr = self.proc.stderr.read()
            raise RuntimeError(f"stdio server closed unexpectedly: {stderr.strip()}")
        return json.loads(line)

    def close(self) -> None:
        if self.proc.stdin is not None:
            self.proc.stdin.close()
        self.proc.terminate()
        try:
            self.proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=2)


class HttpClient:
    def __init__(self, url: str) -> None:
        self.url = url

    def request(self, payload: dict[str, Any]) -> dict[str, Any]:
        raw = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.url,
            data=raw,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                body = resp.read()
        except urllib.error.URLError as exc:
            raise RuntimeError(f"http request failed: {exc}") from exc

        if "id" not in payload:
            return {}
        return json.loads(body.decode("utf-8"))


def run_sequence(client: Any, *, transport: str) -> dict[str, Any]:
    steps: list[dict[str, Any]] = []

    init_resp = client.request(
        json_rpc(
            1,
            "initialize",
            {
                "protocolVersion": "2025-03-26",
                "clientInfo": {"name": "agentsight-mcp-test-cli", "version": "0.1.0"},
                "capabilities": {},
            },
        )
    )
    assert_no_error(init_resp)
    steps.append({"step": "initialize", "result": init_resp["result"]})

    client.request(json_rpc(None, "notifications/initialized", {}))
    steps.append({"step": "notifications/initialized", "result": "sent"})

    ping_resp = client.request(json_rpc(2, "ping", {}))
    assert_no_error(ping_resp)
    steps.append({"step": "ping", "result": ping_resp["result"]})

    list_resp = client.request(json_rpc(3, "tools/list", {}))
    assert_no_error(list_resp)
    tool_names = [tool["name"] for tool in list_resp["result"]["tools"]]
    steps.append({"step": "tools/list", "result": tool_names})

    echo_resp = client.request(
        json_rpc(4, "tools/call", {"name": "echo", "arguments": {"text": f"{transport}-hello"}})
    )
    assert_no_error(echo_resp)
    steps.append({"step": "tools/call echo", "result": extract_text(echo_resp["result"])})

    sum_resp = client.request(
        json_rpc(5, "tools/call", {"name": "sum_numbers", "arguments": {"numbers": [1, 2, 3, 4.5]}})
    )
    assert_no_error(sum_resp)
    steps.append({"step": "tools/call sum_numbers", "result": extract_text(sum_resp["result"])})

    fixture_resp = client.request(
        json_rpc(6, "tools/call", {"name": "read_fixture", "arguments": {}})
    )
    assert_no_error(fixture_resp)
    steps.append({"step": "tools/call read_fixture", "result": extract_text(fixture_resp["result"])})

    return {"transport": transport, "steps": steps}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--transport",
        choices=("stdio", "http"),
        default="stdio",
        help="Transport to use.",
    )
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8765/messages",
        help="HTTP endpoint for HTTP mode.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.transport == "stdio":
        client = StdioClient()
        try:
            result = run_sequence(client, transport="stdio")
        finally:
            client.close()
    else:
        client = HttpClient(args.url)
        result = run_sequence(client, transport="http")

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
