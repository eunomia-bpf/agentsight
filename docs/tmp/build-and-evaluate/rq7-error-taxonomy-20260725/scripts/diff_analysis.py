#!/usr/bin/env python3
"""Per-edge diff of trajectory (production) projection vs source-direct oracle,
using the experiment-time rq7_measurement code (rev 7e5464eca)."""
import json, sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path("/home/yunwei37/workspace/agentsight-agent-nebula-research")
EXP = REPO / "docs/tmp/build-and-evaluate/step-0004-20260723T181008-0700/experiment-001"
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

out = {}
for project in fz["projects"]:
    name = project["project"]
    trace = json.loads((EXP / "private/deterministic/projection/raw/events" / TRACE_FILES[name]).read_text())
    pedges, p0_identity, err = m.proposed_edges(project, trace, EXP / "private/frozen-home")
    if err:
        print(name, "JOIN ERROR:", err); continue
    rel = m.relation_values(pedges, len(project["sessions"]), p0_identity) if p0_identity else None
    expected = {q["template"]: q["answer"] for q in fz["questions"] if q["project"] == name}
    wrong = {t: (rel.get(t), expected[t]) for t in ["B1","B2","B3","B4","B5","C1","C2","C3","C4","C5"]
             if rel and rel.get(t) != expected[t]}
    # session_id (freeze) -> semantic
    sem = {s["session_id"]: f"{s['vendor']}:{s['native_session_id']}" for s in project["sessions"]}
    oedges = project["oracle_edges"]
    okey = Counter((e["session_id"], e["call_id"], e["path"], e["access"]) for e in oedges)
    pkey = Counter((e["session_id"], e["call_id"], e["path"], e["access"]) for e in pedges)
    missing = okey - pkey
    extra = pkey - okey
    out[name] = {"wrong": wrong, "pedges": pedges, "oedges": oedges,
                 "missing": missing, "extra": extra, "rel": rel, "sem": sem}
    print(f"== {name}: wrong={wrong}")
    print(f"   pedges={len(pedges)} oedges={len(oedges)} missing={sum(missing.values())} extra={sum(extra.values())}")

import pickle
with open("/tmp/rq7-repro/diff.pkl","wb") as f:
    pickle.dump(out, f)
print("saved")
