from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from . import __version__
from .snapshot import SnapshotError, load_snapshot, summarize_snapshot


def _summary(args: argparse.Namespace) -> int:
    try:
        snapshot = load_snapshot(args.snapshot)
        summary = summarize_snapshot(snapshot)
    except SnapshotError as exc:
        print(f"agentsight-py: error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(summary.to_dict(), indent=2, sort_keys=True))
        return 0

    print("AgentSight snapshot summary")
    print(f"  schema_version: {summary.schema_version}")
    print(f"  generated_at: {summary.generated_at}")
    print(f"  sessions: {summary.sessions}")
    print(f"  process_nodes: {summary.process_nodes}")
    print(f"  tool_calls: {summary.tool_calls}")
    print(f"  audit_events: {summary.audit_events}")
    print(f"  network_targets: {summary.network_targets}")
    print(f"  resource_samples: {summary.resource_samples}")
    print(f"  llm_calls: {summary.llm_calls}")
    print(f"  input_tokens: {summary.input_tokens}")
    print(f"  output_tokens: {summary.output_tokens}")
    print(f"  total_tokens: {summary.total_tokens}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentsight-py",
        description="Official Python helper for Eunomia AgentSight snapshots.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"agentsight-py {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    summary = subparsers.add_parser("summary", help="summarize an AgentSight JSON snapshot")
    summary.add_argument("snapshot", help="path to snapshot JSON from `agentsight report export`")
    summary.add_argument("--json", action="store_true", help="print machine-readable JSON")
    summary.set_defaults(func=_summary)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

