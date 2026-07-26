#!/usr/bin/env python3
"""Rerun matrix at HEAD, v2: map HEAD trace events to frozen per-source sessions
via the native call ledger (call_id -> source), then apply the experiment-time
answer layer (ArtifactTracker + relation_values from rq7m_exp @ 7e5464eca)."""
import json, sys, csv
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path("/home/yunwei37/workspace/agentsight-agent-nebula-research")
EXP = REPO / "docs/tmp/build-and-evaluate/step-0004-20260723T181008-0700/experiment-001"
RERUN = REPO / "docs/tmp/build-and-evaluate/rq7-error-taxonomy-20260725/rerun-at-HEAD"
sys.path.insert(0, "/tmp/rq7-repro")
import rq7m_exp as m

fz = json.loads((EXP / "private/freeze.json").read_text())
TRACE_FILES = {
    "agentsight": "agentsight.json", "ActPlane": "ActPlane.json",
    "bpf-developer-tutorial": "bpf-developer-tutorial.json",
    "eunomia.dev": "eunomia-dev.json",
    "agentskill-observability-paper": "agentskill-observability-paper.json",
    "academic-writing-skills": "academic-writing-skills.json",
}
HOME = EXP / "private/frozen-home"

frozen_rows = {}
with open(EXP / "raw/method-results.csv") as f:
    for row in csv.DictReader(f):
        frozen_rows[(row["id"], row["method"])] = row

rows = []
diagnostics = {}
for project in fz["projects"]:
    name = project["project"]
    root = Path(project["worktree"])
    target_worktree = m.worktree_id(root)
    session_order = {r["session_id"]: r["session_ordinal"] for r in project["sessions"]}
    calls = m.source_call_ids(project, HOME)   # freeze session_id -> set(call_id)
    # invert: call_id -> list of freeze session_ids
    call2sess = defaultdict(list)
    for sid, cset in calls.items():
        for cid in cset:
            call2sess[cid].append(sid)
    stem2sess = {s["source_stem"]: s["session_id"] for s in project["sources"]}
    native2sess = defaultdict(list)
    for s in project["sources"]:
        native2sess[s["native_session_id"]].append(s["session_id"])

    trace = json.loads((RERUN / "projection/raw/events" / TRACE_FILES[name]).read_text())
    tracker = m.ArtifactTracker(root)
    pedges = []
    diag = Counter()
    for event_ordinal, event in enumerate(trace.get("events") or []):
        actions = [a for a in event.get("actions") or []
                   if not a.get("scope") and a.get("worktree_id") == target_worktree]
        if not actions:
            continue
        cid = str(event.get("source_call_id") or "")
        candidates = call2sess.get(cid, [])
        if len(candidates) == 1:
            session_id = candidates[0]
        elif len(candidates) > 1:
            # disambiguate: prefer source whose stem appears in the event id/session
            ev_sid = str(event.get("session_id") or "")
            pick = [s for s in candidates if stem2sess.get(s) and stem2sess[s] in ev_sid]
            session_id = pick[0] if pick else sorted(candidates, key=lambda s: session_order[s])[0]
            diag["multi_candidate"] += 1
        else:
            diag["unmapped_call"] += 1
            continue
        for action in actions:
            path = str(action.get("path") or "")
            if not path:
                continue
            access = str(action.get("access") or "write")
            previous = str(action.get("previous_path") or "") or None
            identity = tracker.identity(path, access, previous)
            pedges.append({
                "project": name, "session_id": session_id,
                "session_ordinal": session_order[session_id],
                "call_id": cid, "event_ordinal": event_ordinal,
                "artifact_id": identity, "path": path,
                "display_path": tracker.display[identity],
                "access": access,
                "action_class": "read" if access == "read" else "mutate",
            })
    for edge in pedges:
        edge["display_path"] = tracker.display[edge["artifact_id"]]
    p0_path = project["anchors"][0]["path"]
    matches = [i for i, disp in tracker.display.items()
               if disp == p0_path or any(r["artifact_id"] == i and r["path"] == p0_path for r in pedges)]
    p0_identity = None
    if matches:
        matches.sort(key=lambda i: -sum(r["artifact_id"] == i for r in pedges))
        p0_identity = matches[0]
    rel = m.relation_values(pedges, len(project["sessions"]), p0_identity) if p0_identity else None
    diagnostics[name] = dict(diag)

    official = project["procgrep_action_atoms"]
    action_values = {
        "A1": str(sum(s.count("read_file") for s in official.values())),
        "A2": str(sum(s.count("edit") for s in official.values())),
        "A3": str(sum(s.count("run_test") for s in official.values())),
        "A4": str(m.pattern_count(official, r"read_file (?:[a-z_]+ )*edit ")),
        "A5": str(m.pattern_count(official, r"edit (?:[a-z_]+ )*run_test ")),
    }
    final_by_template = {f"D{i}": r["status"] for i, r in enumerate(project["workspace"]["paths"], start=1)}
    projected_paths = {r["display_path"] for r in pedges} | {r["path"] for r in pedges}
    for q in [q for q in fz["questions"] if q["project"] == name]:
        t, fam = q["template"], q["family"]
        vals = {
            "procgrep": m.answer("answer", action_values[t]) if fam == "A" else m.answer("abstain"),
            "counts": m.answer("answer", action_values[t]) if t in {"A1","A2","A3"} else m.answer("abstain"),
            "final_state": m.answer("answer", final_by_template[t]) if fam == "D" else m.answer("abstain"),
        }
        if fam == "A":
            vals["trajectory"] = m.answer("answer", action_values[t])
        elif fam in {"B","C"}:
            vals["trajectory"] = m.answer("answer", rel[t]) if rel else m.answer("abstain")
        else:
            path = project["workspace"]["paths"][int(t[1:]) - 1]["path"]
            vals["trajectory"] = m.answer("answer", final_by_template[t]) if path in projected_paths else m.answer("abstain")
        for method, value in vals.items():
            rows.append({
                "id": q["id"], "project": name, "family": fam, "template": t,
                "method": method, "repetition": 0, "status": value["status"],
                "answer": value["answer"], "expected": q["answer"],
                "correct": int(value["status"] == "answer" and value["answer"] == q["answer"]),
                "wrong": int(value["status"] == "answer" and value["answer"] != q["answer"]),
                "question_spec_sha256": fz["question_spec_sha256"],
            })

print("diagnostics:", json.dumps(diagnostics))
print("rows:", len(rows))
with open(RERUN / "method-results.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["id","project","family","template","method","repetition","status","answer","expected","correct","wrong","question_spec_sha256"])
    w.writeheader(); w.writerows(rows)
json.dump(rows, open(RERUN / "rerun-rows.json","w"))

diffs = []
for r in rows:
    fr = frozen_rows.get((r["id"], r["method"]))
    if fr and (str(fr["answer"]) != str(r["answer"]) or str(fr["status"]) != str(r["status"])):
        diffs.append((r["id"], r["method"], fr["status"], fr["answer"], r["status"], r["answer"], r["expected"]))
other = [d for d in diffs if d[1] != "trajectory"]
traj = [d for d in diffs if d[1] == "trajectory"]
print("non-trajectory changed:", len(other), other[:5])
print("trajectory changed:", len(traj))
for d in sorted(traj): print("  ", d)
