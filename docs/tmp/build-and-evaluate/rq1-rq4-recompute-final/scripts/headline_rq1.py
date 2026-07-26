#!/usr/bin/env python3
"""Compute the RQ1 headline stats (reuse range, Spearman rho) for frozen vs HEAD summaries."""
import csv, math
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
FROZEN = REPO/"docs/tmp/build-and-evaluate/step-0002-20260722T003659-0700/experiment-rq1-20260722T003659-0700/full-six-projects/raw/rq1-summary.csv"
HEAD = REPO/"docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq1-raw/rq1-summary.csv"

def average_ranks(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0]*len(values); i = 0
    while i < len(order):
        j = i
        while j+1 < len(order) and values[order[j+1]] == values[order[i]]: j += 1
        rank = (i + j) / 2 + 1
        for k in range(i, j+1): ranks[order[k]] = rank
        i = j + 1
    return ranks

def spearman(xs, ys):
    rx, ry = average_ranks(xs), average_ranks(ys)
    mx, my = sum(rx)/len(rx), sum(ry)/len(ry)
    num = sum((x-mx)*(y-my) for x, y in zip(rx, ry))
    den = math.sqrt(sum((x-mx)**2 for x in rx) * sum((y-my)**2 for y in ry))
    return num/den if den else math.nan

def load(p):
    with open(p) as f: return list(csv.DictReader(f))

for tag, path in [("FROZEN", FROZEN), ("HEAD", HEAD)]:
    rows = load(path)
    tot_sessions = sum(int(r["included_sessions"]) for r in rows)
    tot_actions = sum(int(r["tool_actions"]) for r in rows)
    attr_sessions = sum(int(r["attributed_sessions"]) for r in rows)
    attr_actions = sum(int(r["attributed_tool_actions"]) for r in rows)
    artifacts = None
    mutations = sum(int(r["confirmed_mutations"]) for r in rows)
    print(f"== {tag}: sessions={tot_sessions} actions={tot_actions} attributed={attr_sessions}/{attr_actions} mutations={mutations}")
    # reuse range over longitudinally eligible (reuse_eligible>0)
    reuse = [(r["project"], int(r["reuse_observed"]), int(r["reuse_eligible"])) for r in rows if int(r["reuse_eligible"])>0]
    fracs = [o/e for _, o, e in reuse]
    print("   reuse per project:", [(p, f"{o}/{e}", f"{o/e*100:.2f}%") for p, o, e in reuse], "range:", f"{min(fracs)*100:.2f}-{max(fracs)*100:.2f}")
    # rho panel B: reuse ratio vs attributed actions over qualified_longitudinal
    elig = [r for r in rows if int(r["reuse_eligible"])>0 and r.get("qualified_longitudinal")=="true"]
    xs = [int(r["attributed_tool_actions"]) for r in elig]
    ys = [int(r["reuse_observed"])/int(r["reuse_eligible"]) for r in elig]
    print(f"   panel-B n={len(xs)} rho={spearman(xs, ys):.4f}")
    # persistence/validation qualification
    print("   qualified_longitudinal:", [r["project"] for r in rows if r.get("qualified_longitudinal")=="true"])
    print("   qualified_validation:", [r["project"] for r in rows if r.get("qualified_validation")=="true"])
