#!/usr/bin/env python3
"""Trajectory answer-layer replay over the workdir-fix projection, scored
against the corrected v4 oracle answers (all 120 rows)."""
import json, sys, csv
from collections import defaultdict, Counter
from pathlib import Path

REPO = Path("/home/yunwei37/workspace/agentsight-agent-nebula-research")
EXP = REPO / "docs/tmp/build-and-evaluate/step-0004-20260723T181008-0700/experiment-001"
W = REPO / "docs/tmp/build-and-evaluate/rq7-error-taxonomy-20260725/workdir-fix"
V4 = REPO / "docs/tmp/build-and-evaluate/rq7-error-taxonomy-20260725/corrected-oracle/corrected-answers.csv"
sys.path.insert(0, "/tmp/rq7-repro")
import rq7m_exp as m

fz = json.loads((EXP / "private/freeze.json").read_text())
HOME = EXP / "private/frozen-home"
TRACE_FILES = {
    "agentsight": "agentsight.json", "ActPlane": "ActPlane.json",
    "bpf-developer-tutorial": "bpf-developer-tutorial.json",
    "eunomia.dev": "eunomia-dev.json",
    "agentskill-observability-paper": "agentskill-observability-paper.json",
    "academic-writing-skills": "academic-writing-skills.json",
}
v4 = {}
frozen_expected = {}
with open(V4) as f:
    for row in csv.DictReader(f):
        v4[row["id"]] = row["corrected_expected"]
        frozen_expected[row["id"]] = row["frozen_expected"]

# previous HEAD answers (pre-workdir-fix) for regression comparison
prev = {r["id"]: r for r in json.load(open(REPO/"docs/tmp/build-and-evaluate/rq7-error-taxonomy-20260725/rerun-at-HEAD/rerun-rows.json")) if r["method"]=="trajectory"}

rows = []
diag = {}
for project in fz["projects"]:
    name = project["project"]
    root = Path(project["worktree"]); twt = m.worktree_id(root)
    session_order = {r["session_id"]: r["session_ordinal"] for r in project["sessions"]}
    calls = m.source_call_ids(project, HOME)
    call2sess = defaultdict(list)
    for sid, cs in calls.items():
        for cid in cs: call2sess[cid].append(sid)
    trace = json.loads((W / "projection/raw/events" / TRACE_FILES[name]).read_text())
    tracker = m.ArtifactTracker(root)
    pedges = []
    d = Counter()
    for eo, event in enumerate(trace.get("events") or []):
        acts = [a for a in event.get("actions") or [] if not a.get("scope") and a.get("worktree_id") == twt]
        if not acts: continue
        cid = str(event.get("source_call_id") or "")
        cand = call2sess.get(cid, [])
        if not cand:
            d["unmapped"] += 1; continue
        sid = cand[0] if len(cand) == 1 else sorted(cand, key=lambda s: session_order[s])[0]
        for a in acts:
            path = str(a.get("path") or "")
            if not path: continue
            access = str(a.get("access") or "write")
            prev_p = str(a.get("previous_path") or "") or None
            ident = tracker.identity(path, access, prev_p)
            pedges.append({"session_id": sid, "session_ordinal": session_order[sid], "call_id": cid,
                           "event_ordinal": eo, "artifact_id": ident, "path": path,
                           "access": access, "action_class": "read" if access == "read" else "mutate"})
    for e in pedges: e["display_path"] = tracker.display[e["artifact_id"]]
    diag[name] = dict(d)
    p0_path = project["anchors"][0]["path"]
    matches = [i for i, disp in tracker.display.items()
               if disp == p0_path or any(r["artifact_id"] == i and r["path"] == p0_path for r in pedges)]
    p0_identity = None
    if matches:
        matches.sort(key=lambda i: -sum(r["artifact_id"] == i for r in pedges))
        p0_identity = matches[0]
    rel = m.relation_values(pedges, len(project["sessions"]), p0_identity) if p0_identity else None
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
        if fam == "A":
            ans = m.answer("answer", action_values[t])
        elif fam in {"B", "C"}:
            ans = m.answer("answer", rel[t]) if rel else m.answer("abstain")
        else:
            path = project["workspace"]["paths"][int(t[1:]) - 1]["path"]
            ans = m.answer("answer", final_by_template[t]) if path in projected_paths else m.answer("abstain")
        qid = q["id"]
        exp = v4[qid]
        rows.append({"id": qid, "project": name, "family": fam, "template": t,
                     "status": ans["status"], "answer": ans["answer"], "expected": exp,
                     "frozen_expected": frozen_expected[qid],
                     "correct": int(ans["status"] == "answer" and ans["answer"] == exp),
                     "wrong": int(ans["status"] == "answer" and ans["answer"] != exp)})

print("join diagnostics:", json.dumps(diag))
with open(W / "trajectory-vs-v4.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)

print("\nper-family totals vs v4 (trajectory):")
for fam in "ABCD":
    sel = [r for r in rows if r["family"] == fam]
    c = sum(r["correct"] for r in sel); w_ = sum(r["wrong"] for r in sel)
    a = sum(r["status"] == "abstain" for r in sel)
    print(f"  {fam}: correct={c} wrong={w_} abstain={a} / 30")
bc = [r for r in rows if r["family"] in {"B", "C"}]
print(f"B+C: {sum(r['correct'] for r in bc)}/60 correct, {sum(r['wrong'] for r in bc)} wrong, {sum(r['status']=='abstain' for r in bc)} abstain")
wrong = [r for r in rows if r["wrong"]]
print("\nwrong rows:", [(r["id"], r["answer"], r["expected"]) for r in wrong])

print("\nchanges vs pre-fix HEAD run (trajectory answers):")
for r in rows:
    p = prev.get(r["id"])
    if p and (p["answer"] != r["answer"] or p["status"] != r["status"]):
        print(f"  {r['id']}: {p['answer']} -> {r['answer']} (v4 expected {r['expected']}, frozen expected {r['frozen_expected']})")

# targeted evidence: the agentsight call must now resolve off P0
t = json.loads((W / "projection/raw/events/agentsight.json").read_text())
for e in t["events"]:
    if str(e.get("source_call_id")) == "toolu_01QdMaxMofN8AJdpWurjqbnR":
        print("\nevidence event actions:", json.dumps(e["actions"]))
