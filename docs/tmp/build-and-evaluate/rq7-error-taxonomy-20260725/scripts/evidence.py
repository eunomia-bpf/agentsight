#!/usr/bin/env python3
"""Evidence samples: M-fail rows, ActPlane P0 extra rows, academic C1 driver."""
import pickle, json, sys
from pathlib import Path
REPO = Path("/home/yunwei37/workspace/agentsight-agent-nebula-research")
EXP = REPO / "docs/tmp/build-and-evaluate/step-0004-20260723T181008-0700/experiment-001"
sys.path.insert(0, "/tmp/rq7-repro")
import rq7m_exp as m
fz = json.loads((EXP / "private/freeze.json").read_text())
B = pickle.load(open("/tmp/rq7-repro/buckets.pkl","rb"))
HOME = EXP / "private/frozen-home"
TRACE_FILES = {"agentskill-observability-paper":"agentskill-observability-paper.json",
               "ActPlane":"ActPlane.json","academic-writing-skills":"academic-writing-skills.json"}

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
                native[(source["session_id"],str(ev.get("call_id")))]=(ev.get("tool"), args.get("command") or args.get("cmd") or "", str(args)[:200])
    print(f"===== {name}")
    shown=Counter=0
    for key,b in B[name]["missing_by_key"].items():
        if b=="M-failed-call-dropped" and shown<2:
            sess,cid,path,access=key
            tool,cmd,args=native.get((sess,cid),(None,None,None))
            te=tev.get((stem_of.get(sess,""),cid))
            print(f"  M-fail: {path} ({access}) tool={tool} trace_status={te.get('status') if te else '?'} trace_actions={te['actions'] if te else '?'}")
            print(f"    cmd/args: {(cmd or args)[:150]!r}")
            shown+=1
    if name=="ActPlane":
        p0="docs/papers/sections/01-introduction.tex"
        for key,b in B[name]["extra_by_key"].items():
            sess,cid,path,access=key
            if path==p0:
                tool,cmd,args=native.get((sess,cid),(None,None,None))
                print(f"  P0-extra[{b}]: {access} cmd: {(cmd or args)[:130]!r}")
