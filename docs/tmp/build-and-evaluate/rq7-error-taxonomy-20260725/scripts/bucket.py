#!/usr/bin/env python3
"""Bucket every extra/missing edge by mechanism, v2."""
import pickle, json, sys, re, shlex
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path("/home/yunwei37/workspace/agentsight-agent-nebula-research")
EXP = REPO / "docs/tmp/build-and-evaluate/step-0004-20260723T181008-0700/experiment-001"
sys.path.insert(0, "/tmp/rq7-repro")
import rq7m_exp as m

fz = json.loads((EXP / "private/freeze.json").read_text())
d = pickle.load(open("/tmp/rq7-repro/diff.pkl","rb"))
HOME = EXP / "private/frozen-home"
SPEC_CMDS = {"cat","sed","head","tail","nl","less","more","touch","rm","mv","cp"}
TRACE_FILES = {
    "agentsight": "agentsight.json", "ActPlane": "ActPlane.json",
    "bpf-developer-tutorial": "bpf-developer-tutorial.json",
    "eunomia.dev": "eunomia-dev.json",
    "agentskill-observability-paper": "agentskill-observability-paper.json",
    "academic-writing-skills": "academic-writing-skills.json",
}

def first_tokens(cmd):
    """first token of each ;&| segment, crude"""
    out=[]
    for seg in re.split(r"[;&|]+", cmd):
        seg=seg.strip()
        if not seg: continue
        try: toks=shlex.split(seg)
        except ValueError: toks=seg.split()
        if toks: out.append(toks[0].rsplit("/",1)[-1].lower())
    return out

result = {}
for name in ["ActPlane","bpf-developer-tutorial","eunomia.dev","agentskill-observability-paper","academic-writing-skills","agentsight"]:
    proj = d[name]
    project = [p for p in fz["projects"] if p["project"]==name][0]
    trace = json.loads((EXP / "private/deterministic/projection/raw/events" / TRACE_FILES[name]).read_text())
    trace_stems = set()
    tev = {}
    for e in trace["events"]:
        sid = str(e.get("session_id") or "")
        stem = sid.split(":",1)[1] if ":" in sid else sid
        trace_stems.add(stem)
        tev[(stem, str(e.get("source_call_id") or ""))] = e
    # native index: (freeze session_id, call_id) -> row
    idx = {}
    for source in project["sources"]:
        for ev in m.native_events(source["vendor"], HOME / source["home_relative"], source):
            if ev.get("kind") != "tool": continue
            args = ev.get("args") or {}
            idx[(source["session_id"], str(ev.get("call_id")))] = {
                "name": ev.get("tool"), "command": args.get("command") or args.get("cmd") or "",
                "args": args, "stem": source["source_stem"], "vendor": source["vendor"],
            }
    stem_of = {s["session_id"]: s["source_stem"] for s in project["sources"]}

    def trace_row(sess, cid):
        return tev.get((stem_of.get(sess,""), cid))

    def extra_bucket(sess, cid):
        row = idx.get((sess, cid))
        if row is None: return "E-no-native-row"
        cmd = row["command"]; tname = str(row["name"]).lower()
        if "*** begin patch" in cmd.lower(): return "E-patch-in-exec-wrapper"
        if tname in ("bash","exec","exec_command","shell_command","run_shell_command","shell"):
            if re.search(r"(^|\s|;|&|\|)(git|gh)\b", cmd): return "E-git-operands"
            if "<<" in cmd or re.search(r"(?<![<>|&])>(?![>&])|(?<![<>])<(?![<=])", cmd): return "E-redir-segment"
            fts = set(first_tokens(cmd))
            nonspec = fts - SPEC_CMDS
            if nonspec and not (fts & SPEC_CMDS): return "E-nonspec-cmd(" + ",".join(sorted(nonspec)) + ")"
            if nonspec: return "E-mixed(" + ",".join(sorted(nonspec)) + ")"
            return "E-shell-spec-cmd"
        return f"E-tool({tname})"

    def missing_bucket(sess, cid):
        stem = stem_of.get(sess,"")
        if stem not in trace_stems: return "M-session-dropped(candidate-bug)"
        te = trace_row(sess, cid)
        if te is not None and str(te.get("status")) == "fail": return "M-failed-call-dropped"
        row = idx.get((sess, cid))
        if row is None: return "M-no-native-row"
        cmd = row["command"]; tname = str(row["name"]).lower()
        if te is None: return "M-event-missing-in-trace"
        if tname in ("bash","exec","exec_command","shell_command","run_shell_command","shell"):
            return "M-shell(" + ",".join(sorted(set(first_tokens(cmd))))[:60] + ")"
        return f"M-tool({tname})"

    extra_b, missing_b = Counter(), Counter()
    extra_by_key, missing_by_key = {}, {}
    for key, n in proj["extra"].items():
        b = extra_bucket(key[0], key[1]); extra_b[b]+=n; extra_by_key[key]=b
    for key, n in proj["missing"].items():
        b = missing_bucket(key[0], key[1]); missing_b[b]+=n; missing_by_key[key]=b
    result[name] = {"extra_b":extra_b, "missing_b":missing_b,
                    "extra_by_key":extra_by_key, "missing_by_key":missing_by_key}
    print(f"== {name}\n  EXTRA: {dict(extra_b.most_common())}\n  MISS : {dict(missing_b.most_common())}")

with open("/tmp/rq7-repro/buckets.pkl","wb") as f:
    pickle.dump(result, f)
