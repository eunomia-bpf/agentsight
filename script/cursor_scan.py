#!/usr/bin/env python3
"""Scan local Cursor agent transcripts and report their structure.

Built while working out the Cursor session format for eunomia-bpf/agentsight#24.
Useful for building parser fixtures and for checking whether a Cursor release has
changed the on-disk shape.

Reads:
    ~/.cursor/projects/<collapsed-cwd>/agent-transcripts/<composerId>/<composerId>.jsonl
    ~/.cursor/projects/<collapsed-cwd>/agent-transcripts/<composerId>/subagents/<childId>.jsonl
    <globalStorage>/state.vscdb          (optional, --db)

Default output is structure only: record counts, tool names, and argument KEY names.
Transcripts contain real prompts and real file paths, so content stays off unless you
ask for it with --paths or --commands. Check what you're about to share.

Usage:
    python3 script/cursor_scan.py                  # summary
    python3 script/cursor_scan.py --args           # per-tool argument schemas
    python3 script/cursor_scan.py --db             # join to state.vscdb metadata
    python3 script/cursor_scan.py --paths          # include file paths (sensitive)
    python3 script/cursor_scan.py --commands       # include shell commands (sensitive)
    python3 script/cursor_scan.py --json out.json  # machine-readable dump
"""

import argparse
import collections
import glob
import json
import os
import sqlite3
import sys

PROJECTS = os.path.expanduser("~/.cursor/projects")

DB_CANDIDATES = [
    "~/Library/Application Support/Cursor/User/globalStorage/state.vscdb",  # macOS
    "~/.config/Cursor/User/globalStorage/state.vscdb",  # Linux
    os.path.join(os.environ.get("APPDATA", ""), "Cursor/User/globalStorage/state.vscdb"),
]


def find_db():
    for path in DB_CANDIDATES:
        expanded = os.path.expanduser(path)
        if expanded and os.path.exists(expanded):
            return expanded
    return None


def transcripts():
    """Yield (composer_id, parent_id_or_None, project_dir, path).

    A subagent's parent is just the directory that contains subagents/, which is the
    only link between them. The Task tool call that spawned the child does not record
    the child's id.
    """
    for path in sorted(glob.glob(f"{PROJECTS}/*/agent-transcripts/*/*.jsonl")):
        parts = path.split(os.sep)
        composer = parts[-2]
        yield composer, None, parts[-4], path
    for path in sorted(glob.glob(f"{PROJECTS}/*/agent-transcripts/*/subagents/*.jsonl")):
        parts = path.split(os.sep)
        child = os.path.basename(path)[: -len(".jsonl")]
        yield child, parts[-3], parts[-5], path


def scan_file(path):
    """Parse one transcript. Tolerates truncation since Cursor appends while running."""
    out = {
        "records": 0,
        "bad_lines": 0,
        "roles": collections.Counter(),
        "turn_status": collections.Counter(),
        "tools": collections.Counter(),
        "args": collections.defaultdict(collections.Counter),
        "paths": [],
        "commands": [],
    }
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                out["bad_lines"] += 1
                continue
            out["records"] += 1
            if rec.get("role"):
                out["roles"][rec["role"]] += 1
            if rec.get("type") == "turn_ended":
                out["turn_status"][rec.get("status", "?")] += 1
            for part in (rec.get("message") or {}).get("content") or []:
                if not isinstance(part, dict) or part.get("type") != "tool_use":
                    continue
                name = part.get("name") or "?"
                args = part.get("input") or part.get("args") or {}
                out["tools"][name] += 1
                out["args"][name].update(args.keys())
                # path is a string on most tools; ReadLints uses paths as a list
                for key in ("path", "paths"):
                    value = args.get(key)
                    if isinstance(value, str):
                        out["paths"].append(value)
                    elif isinstance(value, list):
                        out["paths"].extend(str(item) for item in value)
                if name == "Shell" and args.get("command"):
                    out["commands"].append(args["command"])
    return out


def db_metadata(db_path, composer_ids):
    """Pull header, model, and token totals for the given composers. Read only."""
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    meta = {}
    tables = {r[0] for r in con.execute("select name from sqlite_master where type='table'")}
    for cid in composer_ids:
        row = {}
        if "composerHeaders" in tables:
            header = con.execute(
                "select createdAt, lastUpdatedAt, isSubagent, isArchived, workspaceId"
                " from composerHeaders where composerId = ?",
                (cid,),
            ).fetchone()
            if header:
                row.update(
                    created=header[0],
                    updated=header[1],
                    is_subagent=header[2],
                    archived=header[3],
                    workspace=header[4],
                )
        blob = con.execute(
            "select value from cursorDiskKV where key = ?", (f"composerData:{cid}",)
        ).fetchone()
        if blob:
            try:
                data = json.loads(blob[0])
                model = (data.get("modelConfig") or {}).get("modelName")
                # the literal string "default" means the user never pinned a model
                row["model"] = None if model == "default" else model
                ident = (data.get("workspaceIdentifier") or {}).get("uri") or {}
                row["fs_path"] = ident.get("fsPath")
                row["newly_created"] = len(data.get("newlyCreatedFiles") or [])
            except (json.JSONDecodeError, AttributeError, TypeError):
                pass
        tokens_in = tokens_out = bubbles = 0
        for (value,) in con.execute(
            "select value from cursorDiskKV where key >= ? and key < ?",
            (f"bubbleId:{cid}:", f"bubbleId:{cid};"),
        ):
            bubbles += 1
            try:
                counts = json.loads(value).get("tokenCount") or {}
            except (json.JSONDecodeError, AttributeError):
                continue
            tokens_in += counts.get("inputTokens") or 0
            tokens_out += counts.get("outputTokens") or 0
        row.update(bubbles=bubbles, input_tokens=tokens_in, output_tokens=tokens_out)
        meta[cid] = row
    con.close()
    return meta


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--args", action="store_true", help="per-tool argument key schemas")
    ap.add_argument("--db", action="store_true", help="join to state.vscdb metadata")
    ap.add_argument("--paths", action="store_true", help="include file paths (sensitive)")
    ap.add_argument("--commands", action="store_true", help="include shell commands (sensitive)")
    ap.add_argument("--json", metavar="FILE", help="write the full result as JSON")
    opts = ap.parse_args()

    if not os.path.isdir(PROJECTS):
        sys.exit(f"no Cursor projects directory at {PROJECTS}")

    found = list(transcripts())
    if not found:
        sys.exit("no transcripts found under agent-transcripts/")

    sessions = {}
    totals = collections.Counter()
    all_args = collections.defaultdict(collections.Counter)
    parents = collections.Counter()
    children = collections.Counter()

    for composer, parent, project, path in found:
        data = scan_file(path)
        sessions[path] = dict(data, composer=composer, parent=parent, project=project)
        totals.update(data["tools"])
        for name, keys in data["args"].items():
            all_args[name].update(keys)
        (children if parent else parents).update(data["tools"])

    print(f"transcripts: {len(found)}  "
          f"({sum(1 for _, p, _, _ in found if not p)} parent, "
          f"{sum(1 for _, p, _, _ in found if p)} subagent)")
    print()
    for path, s in sessions.items():
        kind = "SUB" if s["parent"] else "PAR"
        note = f"  parent={s['parent'][:8]}" if s["parent"] else ""
        bad = f"  bad_lines={s['bad_lines']}" if s["bad_lines"] else ""
        print(f"{kind}  {s['composer'][:8]}  {s['records']:4} rec  "
              f"turns={dict(s['turn_status'])}  {dict(s['tools'])}{note}{bad}")

    print()
    print(f"tools, all transcripts : {dict(totals.most_common())}")
    print(f"tools, parents only    : {dict(parents.most_common())}")
    print(f"tools, subagents only  : {dict(children.most_common())}")

    if opts.args:
        print("\nargument keys per tool (a key missing from some calls is optional):")
        for name in sorted(all_args):
            keys = dict(all_args[name])
            flags = [k for k in keys if k.startswith("-")]
            print(f"  {name}: {keys}")
            if flags:
                print(f"      flag-shaped keys, not data: {flags}")

    if opts.paths:
        seen = sorted({p for s in sessions.values() for p in s["paths"]})
        print(f"\npaths ({len(seen)}):")
        for p in seen:
            print(f"  {p}")

    if opts.commands:
        print("\nshell commands:")
        for s in sessions.values():
            for c in s["commands"]:
                print(f"  {c}")

    if opts.db:
        db_path = find_db()
        if not db_path:
            print("\nno state.vscdb found")
        else:
            print(f"\nstate.vscdb: {db_path}")
            meta = db_metadata(db_path, [s["composer"] for s in sessions.values()])
            for cid, row in meta.items():
                print(f"  {cid[:8]}  {row}")

    if opts.json:
        payload = {
            "sessions": [
                {k: (dict(v) if isinstance(v, collections.Counter) else
                     {kk: dict(vv) for kk, vv in v.items()} if isinstance(v, dict) and k == "args"
                     else v)
                 for k, v in s.items()
                 if k not in (() if opts.paths else ("paths",)) + (() if opts.commands else ("commands",))}
                for s in sessions.values()
            ],
            "tool_totals": dict(totals),
            "arg_keys": {k: dict(v) for k, v in all_args.items()},
        }
        with open(opts.json, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, default=str)
        print(f"\nwrote {opts.json}")


if __name__ == "__main__":
    main()
