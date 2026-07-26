#!/usr/bin/env python3
"""For M-shell(sed*) missing edges, show command + trace event actions."""
import pickle, json, sys
from pathlib import Path
REPO = Path("/home/yunwei37/workspace/agentsight-agent-nebula-research")
EXP = REPO / "docs/tmp/build-and-evaluate/step-0004-20260723T181008-0700/experiment-001"
sys.path.insert(0, "/tmp/rq7-repro")
import rq7m_exp as m
fz = json.loads((EXP / "private/freeze.json").read_text())
B = pickle.load(open("/tmp/rq7-repro/buckets.pkl","rb"))
HOME = EXP / "private/frozen-home"
TRACE_FILES = {"bpf-developer-tutorial":"bpf-developer-tutorial.json","eunomia.dev":"eunomia-dev.json",
               "agentskill-observability-paper":"agentskill-observability-paper.json",
               "academic-writing-skills":"academic-writing-skills.json","ActPlane":"ActPlane.json"}
for name, tf in TRACE_FILES.items():
    project=[p for p in fz["projects"] if p["project"]==name][0]
    trace=json.loads((EXP/"private/deterministic/projection/raw/events"/tf).read_text())
    tev={}
    for e in trace["events"]:
        sid=str(e.get("session_id") or ""); stem=sid.split(":",1)[1] if ":" in sid else sid
        tev[(stem,str(e.get("source_call_id") or ""))]=e
    stem_of={s["session_id"]:s["source_stem"] for s in project["sources"]}
    native={}
    for source in project["sources"]:
        for ev in m.native_events(source["vendor"], HOME/source["home_relative"], source):
            if ev.get("kind")=="tool":
                args=ev.get("args") or {}
                native[(source["session_id"],str(ev.get("call_id")))]=(ev.get("tool"), args.get("command") or args.get("cmd") or "")
    print(f"===== {name}")
    for key,b in B[name]["missing_by_key"].items():
        if b.startswith("M-shell"):
            sess,cid,path,access=key
            tool,cmd=native.get((sess,cid),(None,None))
            te=tev.get((stem_of.get(sess,""),cid))
            acts=te["actions"] if te else "NO-EVENT"
            print(f"  [{b}] {path} ({access})")
            print(f"    cmd: {str(cmd)[:160]!r}")
            print(f"    trace actions: {str(acts)[:200]}")
