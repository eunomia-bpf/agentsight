#!/usr/bin/env python3
"""Preserve the official Harness Bench Codex adapter while enforcing its profile.

Harness Bench 2.0 always emits the legacy `--sandbox workspace-write` flag.
Codex 0.144.6 treats that CLI override as higher priority than the named
`default_permissions` profile. This wrapper removes only that legacy pair so
the sanitized config's stricter read/write/deny/network profile governs every
model-generated tool. All other official adapter argv and stdio are unchanged.
"""

from __future__ import annotations

import os
import sys


def main() -> None:
    real = os.environ.get("AGENT_NEBULA_CODEX_REAL", "").strip()
    if not real:
        raise SystemExit("AGENT_NEBULA_CODEX_REAL is required")
    source = sys.argv[1:]
    target: list[str] = []
    index = 0
    removed = False
    while index < len(source):
        if source[index] in ("--sandbox", "-s"):
            if removed or index + 1 >= len(source):
                raise SystemExit("unexpected Harness Bench sandbox arguments")
            if source[index + 1] != "workspace-write":
                raise SystemExit("only the registered workspace-write override may be removed")
            removed = True
            index += 2
            continue
        target.append(source[index])
        index += 1
    if not removed:
        raise SystemExit("official adapter did not supply the expected sandbox override")
    os.execv(real, [real, *target])


if __name__ == "__main__":
    main()
