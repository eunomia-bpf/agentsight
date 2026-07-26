#!/usr/bin/env python3
"""Bucket HEAD residual extra/missing edges by command for the 4 remaining-wrong projects."""
import pickle, json, sys, re, shlex
from collections import Counter
from pathlib import Path
REPO = Path("/home/yunwei37/workspace/agentsight-agent-nebula-research")
EXP = REPO / "docs/tmp/build-and-evaluate/step-0004-20260723T181008-0700/experiment-001"
sys.path.insert(0, "/tmp/rq7-repro")
import rq7m_exp as m
fz = json.loads((EXP / "private/freeze.json").read_text())
D = pickle.load(open("/tmp/rq7-repro/head_diff.pkl","rb"))
HOME = EXP / "private/frozen-home"

def idx_for(project):
    idx = {}
    for source in project["sources"]:
        for ev in m.native_events(source["vendor"], HOME/source["home_relative"], source):
            if ev.get("kind")=="tool":
                args = ev.get("args") or {}
                idx[(source["session_id"], str(ev.get("call_id")))] = (ev.get("tool"), args.get("command") or args.get("cmd") or "", str(args)[:250])
    return idx

def bucket(cmd, tool):
    t = str(tool).lower()
    if "*** begin patch" in cmd.lower(): return "patch-in-exec-wrapper"
    if t in ("bash","exec","exec_command","shell_command","run_shell_command","shell"):
        if re.search(r"(^|\s|;|&|\|)(git|gh)\b", cmd): return "git"
        if "<<" in cmd or re.search(r"(?<![<>|&])>(?![>&])|(?<![<>])<(?![<=])", cmd): return "redir"
        try: first = shlex.split(cmd.strip().splitlines()[0])[0].rsplit("/",1)[-1].lower()
        except Exception: first = "?"
        return f"shell({first})"
    return f"tool({t})"

for name in ["agentsight","ActPlane","bpf-developer-tutorial","academic-writing-skills"]:
    project = [p for p in fz["projects"] if p["project"]==name][0]
    idx = idx_for(project)
    eb, mb = Counter(), Counter()
    samples = {}
    for key, n in D[name]["extra"].items():
        sess,cid,path,access = key
        tool,cmd,args = idx.get((sess,cid),(None,"",""))
        b = bucket(cmd, tool); eb[b]+=n
        samples.setdefault(("E",b),(path,access,(cmd or args)[:150]))
    for key, n in D[name]["missing"].items():
        sess,cid,path,access = key
        tool,cmd,args = idx.get((sess,cid),(None,"",""))
        b = bucket(cmd, tool); mb[b]+=n
        samples.setdefault(("M",b),(path,access,(cmd or args)[:150]))
    print(f"== {name}\n  EXTRA: {dict(eb.most_common())}\n  MISS : {dict(mb.most_common())}")
    for (side,b),s in sorted(samples.items()):
        if side=="E" or name in ("agentsight","academic-writing-skills","bpf-developer-tutorial"):
            print(f"   {side} {b}: {s}")
