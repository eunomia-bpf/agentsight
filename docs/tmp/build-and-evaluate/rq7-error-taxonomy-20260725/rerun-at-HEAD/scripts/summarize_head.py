#!/usr/bin/env python3
"""Summary tables + edge-level diff of remaining wrong trajectory rows at HEAD."""
import json, sys, csv
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path("/home/yunwei37/workspace/agentsight-agent-nebula-research")
EXP = REPO / "docs/tmp/build-and-evaluate/step-0004-20260723T181008-0700/experiment-001"
RERUN = REPO / "docs/tmp/build-and-evaluate/rq7-error-taxonomy-20260725/rerun-at-HEAD"
sys.path.insert(0, "/tmp/rq7-repro")
import rq7m_exp as m

rows = json.load(open(RERUN / "rerun-rows.json"))
fz = json.loads((EXP / "private/freeze.json").read_text())

print("| Method | Family | Correct | Wrong | Abstain | Correct coverage | Conditional accuracy |")
print("|---|---:|---:|---:|---:|---:|---:|")
for method in ("final_state","counts","procgrep","trajectory"):
    for fam in "ABCD":
        sel = [r for r in rows if r["method"]==method and r["family"]==fam]
        c = sum(r["correct"] for r in sel); w = sum(r["wrong"] for r in sel)
        a = sum(r["status"]=="abstain" for r in sel); ans = 30 - a
        print(f"| {method} | {fam} | {c} | {w} | {a} | {c/30:.3f} | {c/max(ans,1):.3f} |")

wrong_bc = [r for r in rows if r["method"]=="trajectory" and r["family"] in {"B","C"} and r["wrong"]]
print("\nstill-wrong trajectory B/C:", len(wrong_bc))
for r in wrong_bc: print("  ", r["id"], r["answer"], "vs", r["expected"])

print("\nper-project trajectory B+C conditional accuracy:")
projects = [p["project"] for p in fz["projects"]]
contrast = 0
for p in projects:
    sel = [r for r in rows if r["method"]=="trajectory" and r["family"] in {"B","C"} and r["project"]==p]
    c = sum(r["correct"] for r in sel); ans = sum(r["status"]=="answer" for r in sel)
    pg = [r for r in rows if r["method"]=="procgrep" and r["family"] in {"B","C"} and r["project"]==p]
    pgc = sum(r["correct"] for r in pg)
    contrast += c/30 - pgc/30
    print(f"  {p}: {c}/30 answered={ans} acc={c/max(ans,1):.3f}")
bc = [r for r in rows if r["method"]=="trajectory" and r["family"] in {"B","C"}]
print(f"Trajectory B+C: {sum(r['correct'] for r in bc)}/60 correct, {sum(r['wrong'] for r in bc)}/60 wrong, {sum(r['status']=='answer' for r in bc)}/60 answered")
print(f"Trajectory-ProcGrep B+C coverage contrast: {contrast/6:.3f}")

# --- edge-level diff for remaining wrong rows ---
TRACE_FILES = {
    "agentsight": "agentsight.json", "ActPlane": "ActPlane.json",
    "bpf-developer-tutorial": "bpf-developer-tutorial.json",
    "eunomia.dev": "eunomia-dev.json",
    "agentskill-observability-paper": "agentskill-observability-paper.json",
    "academic-writing-skills": "academic-writing-skills.json",
}
HOME = EXP / "private/frozen-home"
diff_out = {}
for project in fz["projects"]:
    name = project["project"]
    if name not in {r["project"] for r in wrong_bc}: continue
    root = Path(project["worktree"]); twt = m.worktree_id(root)
    session_order = {r["session_id"]: r["session_ordinal"] for r in project["sessions"]}
    calls = m.source_call_ids(project, HOME)
    call2sess = defaultdict(list)
    for sid, cs in calls.items():
        for cid in cs: call2sess[cid].append(sid)
    trace = json.loads((RERUN / "projection/raw/events" / TRACE_FILES[name]).read_text())
    tracker = m.ArtifactTracker(root)
    pedges = []
    for eo, event in enumerate(trace.get("events") or []):
        acts = [a for a in event.get("actions") or [] if not a.get("scope") and a.get("worktree_id")==twt]
        if not acts: continue
        cid = str(event.get("source_call_id") or "")
        cand = call2sess.get(cid, [])
        if not cand: continue
        sid = cand[0] if len(cand)==1 else sorted(cand, key=lambda s: session_order[s])[0]
        for a in acts:
            path = str(a.get("path") or "")
            if not path: continue
            access = str(a.get("access") or "write")
            prev = str(a.get("previous_path") or "") or None
            ident = tracker.identity(path, access, prev)
            pedges.append({"session_id": sid, "session_ordinal": session_order[sid], "call_id": cid,
                           "event_ordinal": eo, "artifact_id": ident, "path": path,
                           "access": access, "action_class": "read" if access=="read" else "mutate"})
    oedges = project["oracle_edges"]
    okey = Counter((e["session_id"], e["call_id"], e["path"], e["access"]) for e in oedges)
    pkey = Counter((e["session_id"], e["call_id"], e["path"], e["access"]) for e in pedges)
    missing = okey - pkey; extra = pkey - okey
    diff_out[name] = {"missing": missing, "extra": extra, "pedges": pedges, "oedges": oedges}
    print(f"\n== {name}: missing={sum(missing.values())} extra={sum(extra.values())}")
    print("   missing:", list(missing.items())[:12])
    print("   extra top:", Counter((k[2],k[3]) for k in extra.elements()).most_common(10))

import pickle
pickle.dump(diff_out, open("/tmp/rq7-repro/head_diff.pkl","wb"))
