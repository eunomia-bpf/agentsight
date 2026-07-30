#!/usr/bin/env python3
"""Build one standard pprof profile from BEFORE ToolSandbox pilot traces."""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess

import run_pairs


HERE = Path(__file__).resolve().parent
OPERATIONS = HERE / "before-profile-operations.jsonl"
PROFILE = HERE / "before-profile.pb.gz"
SUMMARY = HERE / "before-profile-summary.json"
IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def result_class(content: str) -> str:
    lowered = content.lower()
    if "syntaxerror: invalid decimal literal" in lowered:
        return "invalid-call-id"
    if any(word in lowered for word in ("error", "exception", "traceback")):
        return "other-error"
    return "completed"


def main() -> int:
    rows = []
    for index, scenario in enumerate(run_pairs.PILOT):
        seed = run_pairs.seed_for("pilot", index)
        conversation = (
            run_pairs.episode_path("no-policy", seed, scenario).parent
            / "trajectories"
            / scenario
            / "conversation.json"
        )
        messages = json.loads(conversation.read_text(encoding="utf-8"))
        previous_signature = None
        pending = []
        ordinal = 0
        for message in messages:
            if message.get("role") == "assistant" and message.get("tool_calls"):
                for call in message["tool_calls"]:
                    function = call["function"]
                    arguments = json.loads(function["arguments"])
                    signature = (
                        str(function["name"]),
                        json.dumps(arguments, ensure_ascii=False, sort_keys=True),
                    )
                    pending.append(
                        {
                            "signature": signature,
                            "tool": signature[0],
                            "arguments": signature[1],
                            "repeat_state": (
                                "exact-repeat"
                                if signature == previous_signature
                                else "single"
                            ),
                            "call_id_valid": (
                                "valid"
                                if IDENTIFIER.fullmatch(str(call["id"]))
                                else "invalid"
                            ),
                            "ordinal": ordinal,
                        }
                    )
                    previous_signature = signature
                    ordinal += 1
            elif message.get("role") == "tool" and pending:
                operation = pending.pop(0)
                rows.append(
                    {
                        "fields": {
                            "scenario": scenario,
                            "tool": operation["tool"],
                            "arguments": operation["arguments"],
                            "result": result_class(str(message.get("content") or "")),
                            "repeat_state": operation["repeat_state"],
                            "call_id": operation["call_id_valid"],
                            "source_session": f"toolsandbox-before-{seed}-{scenario}",
                            "evidence_id": f"{scenario}:tool-{operation['ordinal']:04d}",
                        },
                        "value": 1,
                    }
                )
    with OPERATIONS.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    result = subprocess.run(
        [
            str(run_pairs.REPO / "agentpprof/target/release/agentpprof"),
            "--operation-file",
            str(OPERATIONS),
            "--view",
            "operations",
            "--stack",
            "scenario,tool,result,repeat_state,call_id",
            "--deterministic-output",
            "--output",
            str(PROFILE),
        ],
        cwd=run_pairs.REPO,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stderr)
    readback = subprocess.run(
        ["go", "tool", "pprof", "-top", str(PROFILE)],
        cwd=run_pairs.REPO,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=True,
    )
    counts = {}
    for key in ("result", "repeat_state", "call_id"):
        values = {}
        for row in rows:
            value = row["fields"][key]
            values[value] = values.get(value, 0) + 1
        counts[key] = values
    summary = {
        "schema": "agentsight.toolsandbox-before-profile.v1",
        "scenarios": len(run_pairs.PILOT),
        "tool_operations": len(rows),
        "counts": counts,
        "product_profile": str(PROFILE.relative_to(HERE)),
        "operations_input": str(OPERATIONS.relative_to(HERE)),
        "agentpprof_stdout": result.stdout,
        "pprof_top": readback.stdout,
    }
    SUMMARY.write_text(
        json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
