#!/usr/bin/env python3
"""Capture immutable metadata for the already-running local inference server."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parent
BASE_URL = "http://127.0.0.1:18185"
OUTPUT = ROOT / "toolsandbox" / "server-metadata.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def get_json(path: str) -> dict:
    with urlopen(f"{BASE_URL}{path}", timeout=10) as response:
        return json.load(response)


def find_server() -> tuple[int, list[str]]:
    matches = []
    for proc_dir in Path("/proc").glob("[0-9]*"):
        try:
            raw = (proc_dir / "cmdline").read_bytes()
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        args = [
            item.decode("utf-8", errors="replace")
            for item in raw.rstrip(b"\0").split(b"\0")
            if item
        ]
        if (
            args
            and Path(args[0]).name == "llama-server"
            and "--port" in args
            and args[args.index("--port") + 1] == "18185"
        ):
            matches.append((int(proc_dir.name), args))
    if len(matches) != 1:
        raise RuntimeError(f"expected one llama-server on port 18185, found {matches}")
    return matches[0]


def main() -> None:
    models = get_json("/v1/models")
    props = get_json("/props")
    pid, args = find_server()
    executable = Path(os.readlink(f"/proc/{pid}/exe"))
    model_path = Path(props["model_path"])
    stat = model_path.stat()
    template = props.get("chat_template", "")
    metadata = {
        "schema": "agentsight.utility.inference-server.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "base_url": BASE_URL,
        "process": {
            "pid_at_capture": pid,
            "argv": args,
            "executable": str(executable),
            "executable_sha256": sha256(executable),
        },
        "model": {
            "path": str(model_path),
            "sha256": sha256(model_path),
            "size_bytes": stat.st_size,
            "snapshot_revision": model_path.parent.name,
            "api_id": models["data"][0]["id"],
            "api_meta": models["data"][0]["meta"],
        },
        "server": {
            "build_info": props["build_info"],
            "n_ctx": props["default_generation_settings"]["n_ctx"],
            "total_slots": props["total_slots"],
            "reasoning_format": props["default_generation_settings"]["params"][
                "reasoning_format"
            ],
            "chat_template_sha256": hashlib.sha256(
                template.encode("utf-8")
            ).hexdigest(),
        },
        "registered_sampling_override": {
            "temperature": 0.2,
            "top_p": 0.95,
            "max_tokens": 2048,
            "presence_penalty": 0.0,
            "frequency_penalty": 0.0,
        },
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8") as stream:
        json.dump(metadata, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps(metadata, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
