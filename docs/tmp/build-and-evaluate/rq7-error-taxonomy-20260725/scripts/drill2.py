#!/usr/bin/env python3
"""Drill into specific ambiguous mechanism cases."""
import pickle, json, sys, re
from collections import Counter
from pathlib import Path

REPO = Path("/home/yunwei37/workspace/agentsight-agent-nebula-research")
EXP = REPO / "docs/tmp/build-and-evaluate/step-0004-20260723T181008-0700/experiment-001"
sys.path.insert(0, "/tmp/rq7-repro")
import rq7m_exp as m

fz = json.loads((EXP / "private/freeze.json").read_text())
d = pickle.load(open("/tmp/rq7-repro/diff.pkl","rb"))
B = pickle.load(open("/tmp/rq7-repro/buckets.pkl","rb"))
HOME = EXP / "private/frozen-home"

def show_native(project, sess, cid, maxlen=500):
    for source in project["sources"]:
        if source["session_id"] != sess: continue
        rows = json.loads((HOME/source["home_relative"]).read_text()) if source["home_relative"].endswith(".json") else None
        for ev in m.native_events(source["vendor"], HOME/source["home_relative"], source):
            if ev.get("kind")=="tool" and str(ev.get("call_id"))==cid:
                args = ev.get("args") or {}
                cmd = args.get("command") or args.get("cmd") or ""
                print(f"   tool={ev.get('tool')} record={ev.get('record_index')} call={ev.get('call_index')}")
                if cmd: print(f"   cmd: {cmd[:maxlen]!r}")
                else: print(f"   args keys: {list(args.keys())} -> {str(args)[:maxlen]}")
                return
    print("   (native row not found)")

# 1. eunomia M-shell(sed) cases
name="eunomia.dev"; project=[p for p in fz["projects"] if p["project"]==name][0]
print("### eunomia.dev M-shell(sed) samples")
shown=0
for key,b in B[name]["missing_by_key"].items():
    if b.startswith("M-shell(sed") and shown<3:
        sess,cid,path,access=key
        print(f"  edge: {path} {access} sess={sess[:12]}")
        show_native(project,sess,cid)
        shown+=1

# 2. sed-program-as-path oracle edges (ActPlane + bpf)
for name in ["ActPlane","bpf-developer-tutorial"]:
    project=[p for p in fz["projects"] if p["project"]==name][0]
    print(f"### {name} oracle sed-program-path edges")
    for key,b in B[name]["missing_by_key"].items():
        sess,cid,path,access=key
        if path.startswith("s#"):
            print(f"  edge: {path[:60]} {access}")
            show_native(project,sess,cid,700)
            break

# 3. ActPlane E-patch-in-exec-wrapper sample
name="ActPlane"; project=[p for p in fz["projects"] if p["project"]==name][0]
print("### ActPlane E-patch-in-exec-wrapper sample")
for key,b in B[name]["extra_by_key"].items():
    if b=="E-patch-in-exec-wrapper":
        sess,cid,path,access=key
        print(f"  edge: {path} {access}")
        show_native(project,sess,cid,700)
        break

# 4. agentskill M-session-dropped: which sessions
name="agentskill-observability-paper"; project=[p for p in fz["projects"] if p["project"]==name][0]
print("### agentskill M-session-dropped keys")
for key,b in B[name]["missing_by_key"].items():
    if b=="M-session-dropped(candidate-bug)":
        sess,cid,path,access=key
        stem=[s["source_stem"] for s in project["sources"] if s["session_id"]==sess]
        print(f"  {sess[:30]} stem={stem} {path} {access}")

# 5. agentskill E-tool(write)/M-tool(write) access drift
print("### agentskill write drift")
for key,b in B[name]["extra_by_key"].items():
    if b=="E-tool(write)":
        print("  extra:", key)
for key,b in B[name]["missing_by_key"].items():
    if b=="M-tool(write)":
        print("  miss :", key)
