#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 eunomia-bpf org.

import argparse
import json
import ssl
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


REDACTED_HEADERS = {
    "authorization",
    "cookie",
    "x-api-key",
    "anthropic-api-key",
    "openai-api-key",
}


def redact_headers(headers: Any) -> dict[str, str]:
    result: dict[str, str] = {}
    for key, value in headers.items():
        if key.lower() in REDACTED_HEADERS:
            result[key] = "<redacted>"
        else:
            result[key] = value
    return result


def first_prompt(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = [first_prompt(item) for item in value]
        return " ".join(part for part in parts if part)
    if not isinstance(value, dict):
        return ""

    if "messages" in value:
        return first_prompt(value["messages"])
    if "input" in value:
        return first_prompt(value["input"])
    if "content" in value:
        return first_prompt(value["content"])
    if "text" in value:
        return first_prompt(value["text"])
    if "prompt" in value:
        return first_prompt(value["prompt"])

    return " ".join(first_prompt(item) for item in value.values())


def contains_type(value: Any, expected: str) -> bool:
    if isinstance(value, list):
        return any(contains_type(item, expected) for item in value)
    if not isinstance(value, dict):
        return False
    return value.get("type") == expected or any(
        contains_type(item, expected) for item in value.values()
    )


class MockLlmHandler(BaseHTTPRequestHandler):
    server_version = "AgentSightMockLLM/1.0"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args: Any) -> None:
        if self.server.quiet:  # type: ignore[attr-defined]
            return
        super().log_message(fmt, *args)

    def do_GET(self) -> None:
        if urlparse(self.path).path == "/health":
            self.write_json({"ok": True, "server": "agentsight-mock-llm"})
            return
        self.send_error(404, "not found")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        body = self.read_body()
        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except json.JSONDecodeError:
            payload = {"raw": body.decode("utf-8", errors="replace")}

        self.log_request_body(parsed.path, payload, body)

        if parsed.path.endswith("/chat/completions"):
            self.respond_openai_chat(payload)
        elif parsed.path.endswith("/responses"):
            self.respond_openai_responses(payload)
        elif parsed.path.endswith("/messages"):
            self.respond_anthropic_messages(payload)
        else:
            self.write_json({"ok": True, "path": parsed.path})

    def read_body(self) -> bytes:
        transfer_encoding = self.headers.get("transfer-encoding", "").lower()
        if "chunked" in transfer_encoding:
            chunks: list[bytes] = []
            while True:
                size_line = self.rfile.readline().split(b";", 1)[0].strip()
                if not size_line:
                    break
                size = int(size_line, 16)
                if size == 0:
                    self.rfile.readline()
                    break
                chunks.append(self.rfile.read(size))
                self.rfile.read(2)
            return b"".join(chunks)

        length = int(self.headers.get("content-length", "0"))
        return self.rfile.read(length) if length else b""

    def log_request_body(self, path: str, payload: Any, raw_body: bytes) -> None:
        entry = {
            "ts": time.time(),
            "method": self.command,
            "path": path,
            "headers": redact_headers(self.headers),
            "prompt": first_prompt(payload),
            "json": payload,
            "raw_body": raw_body.decode("utf-8", errors="replace"),
        }
        log_path: Path = self.server.request_log_path  # type: ignore[attr-defined]
        with log_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(entry, sort_keys=True) + "\n")

    def respond_openai_chat(self, payload: dict[str, Any]) -> None:
        model = payload.get("model", "gpt-agentsight-mock")
        content = "agentsight mock response"
        if payload.get("stream"):
            chunks = [
                {
                    "id": "chatcmpl-agentsight",
                    "object": "chat.completion.chunk",
                    "choices": [{"index": 0, "delta": {"content": content}, "finish_reason": None}],
                    "model": model,
                },
                {
                    "id": "chatcmpl-agentsight",
                    "object": "chat.completion.chunk",
                    "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                    "model": model,
                },
            ]
            self.respond_sse(chunks)
            return

        self.write_json(
            {
                "id": "chatcmpl-agentsight",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": content},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 11, "completion_tokens": 4, "total_tokens": 15},
            }
        )

    def respond_openai_responses(self, payload: dict[str, Any]) -> None:
        model = payload.get("model", "gpt-agentsight-mock")
        content = "agentsight mock response"
        if payload.get("stream"):
            tool_sleep = self.server.responses_tool_sleep  # type: ignore[attr-defined]
            if tool_sleep and contains_type(payload, "function_call_output"):
                time.sleep(tool_sleep)
            if tool_sleep and not contains_type(payload, "function_call_output"):
                arguments = json.dumps(
                    {"cmd": f"sleep {tool_sleep}", "yield_time_ms": 250}
                )
                item = {
                    "id": "fc_agentsight",
                    "type": "function_call",
                    "status": "completed",
                    "call_id": "call_agentsight",
                    "name": "exec_command",
                    "arguments": arguments,
                }
                response = {
                    "id": "resp_agentsight",
                    "model": model,
                    "status": "completed",
                    "output": [item],
                    "usage": {"input_tokens": 11, "output_tokens": 4, "total_tokens": 15},
                }
                self.respond_sse(
                    [
                        {"type": "response.created", "response": response},
                        {"type": "response.output_item.added", "output_index": 0, "item": item},
                        {
                            "type": "response.function_call_arguments.done",
                            "item_id": item["id"],
                            "output_index": 0,
                            "arguments": arguments,
                        },
                        {"type": "response.output_item.done", "output_index": 0, "item": item},
                        {"type": "response.completed", "response": response},
                    ]
                )
                return
            self.respond_sse(
                [
                    {"type": "response.created", "response": {"id": "resp_agentsight", "model": model}},
                    {"type": "response.output_text.delta", "delta": content},
                    {
                        "type": "response.completed",
                        "response": {
                            "id": "resp_agentsight",
                            "model": model,
                            "usage": {"input_tokens": 11, "output_tokens": 4, "total_tokens": 15},
                        },
                    },
                ]
            )
            return

        self.write_json(
            {
                "id": "resp_agentsight",
                "object": "response",
                "created_at": int(time.time()),
                "model": model,
                "output_text": content,
                "output": [
                    {
                        "id": "msg_agentsight",
                        "type": "message",
                        "role": "assistant",
                        "content": [{"type": "output_text", "text": content}],
                    }
                ],
                "usage": {"input_tokens": 11, "output_tokens": 4, "total_tokens": 15},
            }
        )

    def respond_anthropic_messages(self, payload: dict[str, Any]) -> None:
        model = payload.get("model", "claude-agentsight-mock")
        self.write_json(
            {
                "id": "msg_agentsight",
                "type": "message",
                "role": "assistant",
                "model": model,
                "content": [{"type": "text", "text": "agentsight mock response"}],
                "stop_reason": "end_turn",
                "stop_sequence": None,
                "usage": {"input_tokens": 11, "output_tokens": 4},
            }
        )

    def respond_sse(self, chunks: list[dict[str, Any]]) -> None:
        self.send_response(200)
        self.send_header("content-type", "text/event-stream")
        self.send_header("cache-control", "no-cache")
        self.send_header("connection", "close")
        self.end_headers()
        for chunk in chunks:
            self.wfile.write(b"data: ")
            self.wfile.write(json.dumps(chunk, sort_keys=True).encode("utf-8"))
            self.wfile.write(b"\n\n")
        self.wfile.write(b"data: [DONE]\n\n")
        self.close_connection = True

    def write_json(self, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> int:
    parser = argparse.ArgumentParser(description="OpenAI/Anthropic-compatible mock LLM server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18080)
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--tls-cert", type=Path)
    parser.add_argument("--tls-key", type=Path)
    parser.add_argument("--responses-tool-sleep", type=int, default=0)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    args.log.parent.mkdir(parents=True, exist_ok=True)
    args.log.touch()

    server = ThreadingHTTPServer((args.host, args.port), MockLlmHandler)
    server.request_log_path = args.log  # type: ignore[attr-defined]
    server.quiet = args.quiet  # type: ignore[attr-defined]
    server.responses_tool_sleep = max(args.responses_tool_sleep, 0)  # type: ignore[attr-defined]

    if args.tls_cert or args.tls_key:
        if not args.tls_cert or not args.tls_key:
            parser.error("--tls-cert and --tls-key must be provided together")
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(args.tls_cert, args.tls_key)
        server.socket = context.wrap_socket(server.socket, server_side=True)

    scheme = "https" if args.tls_cert else "http"
    print(f"{scheme}://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
