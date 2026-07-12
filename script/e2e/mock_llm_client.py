#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 eunomia-bpf org.

import argparse
import json
import ssl
import sys
import time
import urllib.request


def payload_for(mode: str, prompt: str) -> dict:
    if mode == "responses":
        return {"model": "gpt-agentsight-mock", "input": prompt}
    if mode == "anthropic":
        return {
            "model": "claude-agentsight-mock",
            "max_tokens": 64,
            "messages": [{"role": "user", "content": prompt}],
        }
    return {
        "model": "gpt-agentsight-mock",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Send one request to script/e2e/mock_llm_server.py.")
    parser.add_argument("--url", required=True)
    parser.add_argument("--mode", choices=["chat", "responses", "anthropic"], default="chat")
    parser.add_argument("--prompt", default="agentsight mock prompt")
    parser.add_argument("--insecure", action="store_true")
    parser.add_argument("--delay", type=float, default=0.0)
    args = parser.parse_args()

    if args.delay > 0:
        time.sleep(args.delay)

    body = json.dumps(payload_for(args.mode, args.prompt)).encode("utf-8")
    request = urllib.request.Request(
        args.url,
        data=body,
        headers={
            "authorization": "Bearer agentsight-test",
            "anthropic-api-key": "agentsight-test",
            "content-type": "application/json",
        },
        method="POST",
    )
    context = ssl._create_unverified_context() if args.insecure else None
    with urllib.request.urlopen(request, context=context, timeout=30) as response:
        sys.stdout.buffer.write(response.read())
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
