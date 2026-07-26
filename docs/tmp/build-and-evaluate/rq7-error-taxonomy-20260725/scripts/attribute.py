#!/usr/bin/env python3
"""Final per-question attribution for the 28 wrong trajectory answers.

Mechanism buckets (edge-level):
EXTRA (production counts, oracle excludes):
  E-git        git/gh command path operands (broader shell design)
  E-redir      redirection/heredoc segments (broader shell design)
  E-nonspec    operands of non-spec commands: grep/rg/wc/ls/find/make/... (broader design)
  E-patchwrap  apply_patch inside codex exec JS wrapper (oracle unwrap gap)
  E-writeDrift Write/write_file access label drift (write vs create) - no answer impact
MISSING (oracle counts, production lacks):
  M-cand       session dropped at candidate filter (dotted/parent claude project dir)
  M-fail       failed tool call actions dropped by production
  M-sedext     sed/nl/cat reads dropped by plausible_path_token ext/len filter
  M-scope      production recorded only a scope(directory) action, filtered out
  O-sedprog    oracle-side artifact: sed program text counted as a path
"""
import pickle, json, sys, re
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path("/home/yunwei37/workspace/agentsight-agent-nebula-research")
EXP = REPO / "docs/tmp/build-and-evaluate/step-0004-20260723T181008-0700/experiment-001"
sys.path.insert(0, "/tmp/rq7-repro")
import rq7m_exp as m

fz = json.loads((EXP / "private/freeze.json").read_text())
d = pickle.load(open("/tmp/rq7-repro/diff.pkl","rb"))
B = pickle.load(open("/tmp/rq7-repro/buckets.pkl","rb"))

def coarse_extra(b):
    if b == "E-git-operands": return "E-git"
    if b == "E-redir-segment": return "E-redir"
    if b == "E-patch-in-exec-wrapper": return "E-patchwrap"
    if b.startswith("E-tool(write"): return "E-writeDrift"
    if b == "E-shell-spec-cmd": return "E-shellspec?"
    if b.startswith("E-tool"): return "E-nonspec"
    return "E-nonspec"  # E-nonspec-cmd, E-mixed

def coarse_missing(b, path):
    if b == "M-session-dropped(candidate-bug)": return "M-cand"
    if b == "M-failed-call-dropped": return "M-fail"
    if path.startswith("s#"): return "O-sedprog"
    if b.startswith("M-shell(find"): return "O-sedprog"  # find|sed pipelines producing sed-program paths
    if b.startswith("M-shell"): return "M-sedext"
    if b.startswith("M-tool"): return "M-tool?"
    return "M-other"

TEMPLATES = ["B1","B2","B3","B4","B5","C1","C2","C3","C4","C5"]

def rel_from_edges(edges, session_count, p0_identity):
    return m.relation_values(edges, session_count, p0_identity)

final = {}
for name in ["ActPlane","bpf-developer-tutorial","eunomia.dev","agentskill-observability-paper","academic-writing-skills"]:
    proj = d[name]
    project = [p for p in fz["projects"] if p["project"]==name][0]
    expected = {q["template"]: q["answer"] for q in fz["questions"] if q["project"]==name}
    pedges = proj["pedges"]; oedges = proj["oedges"]
    n_sess = len(project["sessions"])
    p0_path = project["anchors"][0]["path"]
    # production p0 identity (as deterministic_methods computed)
    p0c = {r["artifact_id"] for r in pedges if r["path"]==p0_path or r["display_path"]==p0_path}
    p0_prod = max(p0c, key=lambda i: sum(r["artifact_id"]==i for r in pedges)) if p0c else None
    o_p0 = project["anchors"][0]["artifact_id"]

    # bucket maps in coarse form
    eb = {k: coarse_extra(v) for k,v in B[name]["extra_by_key"].items()}
    mb = {k: coarse_missing(v, k[2]) for k,v in B[name]["missing_by_key"].items()}

    # --- B-question decomposition on P0 path ---
    # oracle P0 calls
    o_p0_edges = [e for e in oedges if e["artifact_id"]==o_p0]
    o_p0_calls = {(e["session_id"],e["call_id"]) for e in o_p0_edges}
    p_p0_edges = [e for e in pedges if e["artifact_id"]==p0_prod]
    p_p0_calls = {(e["session_id"],e["call_id"]) for e in p_p0_edges}
    # key-level p0 sets
    okey_p0 = Counter((e["session_id"],e["call_id"],e["path"],e["access"]) for e in o_p0_edges)
    pkey_p0 = Counter((e["session_id"],e["call_id"],e["path"],e["access"]) for e in p_p0_edges)
    p0_missing = okey_p0 - pkey_p0
    p0_extra = pkey_p0 - okey_p0
    p0_miss_b = Counter()
    for k,n in p0_missing.items(): p0_miss_b[mb.get(k,"M-?")] += n
    p0_extra_b = Counter()
    for k,n in p0_extra.items(): p0_extra_b[eb.get(k,"E-?")] += n

    # --- C-question counterfactuals ---
    # remove extra edges bucket-by-bucket from production
    prod_answers = m.relation_values(pedges, n_sess, p0_prod) if p0_prod else {}
    # oracle answers recomputed (sanity)
    o_answers = m.relation_values(oedges, n_sess, o_p0)
    # counterfactual: remove ALL extra edges
    pedges_noextra = [e for e in pedges if (e["session_id"],e["call_id"],e["path"],e["access"]) not in eb]
    cf_noextra = m.relation_values(pedges_noextra, n_sess, p0_prod) if p0_prod else {}
    # per-bucket removal
    cf_bucket = {}
    for bucket in sorted(set(eb.values())):
        kept = [e for e in pedges if eb.get((e["session_id"],e["call_id"],e["path"],e["access"])) != bucket]
        cf_bucket[bucket] = m.relation_values(kept, n_sess, p0_prod) if p0_prod else {}
    # oracle minus sed-program artifacts
    o_nobogus = [e for e in oedges if not e["path"].startswith("s#")]
    cf_onobogus = m.relation_values(o_nobogus, n_sess, o_p0)

    final[name] = {
        "expected": expected, "prod": prod_answers, "oracle_recompute": o_answers,
        "p0_path": p0_path, "p0_missing_buckets": p0_miss_b, "p0_extra_buckets": p0_extra_b,
        "cf_noextra": cf_noextra, "cf_bucket": cf_bucket, "cf_oracle_nobogus": cf_onobogus,
    }
    print(f"===== {name} (P0={p0_path})")
    print("  answers: tmpl prod/expected | noextra | oracle-nobogus")
    for t in TEMPLATES:
        pa, ea = prod_answers.get(t), expected.get(t)
        mark = "WRONG" if pa != ea else "ok   "
        print(f"   {mark} {t}: {pa}/{ea} | noX={cf_noextra.get(t)} | Obogus-={cf_onobogus.get(t)}")
    print("  P0 missing:", dict(p0_miss_b), " P0 extra:", dict(p0_extra_b))
    for bucket, cf in cf_bucket.items():
        diffs = {t: (prod_answers.get(t), cf.get(t)) for t in TEMPLATES if prod_answers.get(t) != cf.get(t)}
        if diffs: print(f"  remove {bucket}: {diffs}")

with open("/tmp/rq7-repro/final.pkl","wb") as f:
    pickle.dump(final, f)
