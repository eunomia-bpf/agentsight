#!/usr/bin/env python3
"""AgentReward 125-task rank-agreement experiment (RQ1, resource attribution).

Scientific question (fixed by task-spec.md): on the complete frozen AgentReward
operation hierarchy, does changing only the additive measure (operation count
vs provider-reported tokens) change which recurring operations dominate?

Method (fixed by task-spec.md):
  1. For every weighted source node (operations > 0 or tokens > 0), the
     operation identity is the deepest semantic tag of its `path` (leaf
     operation name). The full path is also recorded for a path-level variant.
  2. Per task (125 tasks): aggregate over all sessions of that task each
     operation's total operation count and total token mass; rank once by
     count and once by tokens.
  3. Per-task Kendall's tau-b (scipy.stats.kendalltau) and Spearman rho
     (scipy.stats.spearmanr) between the two rankings. Tasks with fewer than
     3 distinct operations are skipped (and counted).
  4. Aggregate: mean per-task tau-b and rho, each with a 10,000-draw
     percentile bootstrap interval that resamples TASKS (cluster bootstrap),
     fixed seed 20260724 (numpy.random.default_rng).
  5. Secondary: (a) pooled population-level ranking over all tasks combined;
     (b) path-level identity (full semantic path string) instead of leaf name.
  6. Validity checks: total operation mass and token mass must equal the
     workspace totals (7,229 operations per the workspace README; 51,904,621
     tokens per the sum of stacks.folded).

Task-ID provenance: each session node's `data.source_session` is the
sanitized label key `<benchmark>__<task_id>__<model>` built by
script/agentreward_diff_pprof_eval.py (Label.key, lines 53-58). The task ID
is the middle `__`-separated segment; the canonical task applies
`canonical_task_id()` from the same script (lines 90-91), i.e.
`task_id.replace(".resized.", ".")`. Weighted nodes are mapped to their
session (and hence task) by walking `parent` links up to the session node.

Read-only: this script only reads the frozen workspace; it writes
raw-results.json next to itself.
"""

import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import kendalltau, spearmanr

EXPERIMENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = EXPERIMENT_DIR.parents[4]
WORKSPACE = REPO_ROOT / "docs/visexp/out/agentreward-diff-pprof-v1"
TRACE = WORKSPACE / "recursive-annotation-v1/trace.jsonl"
FOLDED = WORKSPACE / "recursive-annotation-v1/stacks.folded"

BOOTSTRAP_DRAWS = 10_000
BOOTSTRAP_SEED = 20260724
MIN_DISTINCT_OPS = 3

# Workspace totals: 7,229 operation samples stated in the workspace README
# (agentreward-440-trajectories-recursive.operations.pb.gz); token total is
# recomputed from stacks.folded below.
WORKSPACE_OPERATION_TOTAL = 7229


def canonical_task_id(task_id: str) -> str:
    """Mirror of script/agentreward_diff_pprof_eval.py:canonical_task_id."""
    return task_id.replace(".resized.", ".")


def load_trace():
    nodes = {}
    with TRACE.open(encoding="utf-8") as handle:
        for line in handle:
            node = json.loads(line)
            nodes[node["id"]] = node
    return nodes


def session_of(node, nodes):
    """Walk parent links up to the session node."""
    while node is not None and node["kind"] != "session":
        node = nodes.get(node["parent"])
    return node


def task_of_session(session_node):
    parts = session_node["data"]["source_session"].split("__")
    if len(parts) != 3:
        raise ValueError(
            f"unparseable source_session: {session_node['data']['source_session']!r}"
        )
    benchmark, task_id, _model = parts
    assert benchmark == session_node["data"]["benchmark"]
    return f"{benchmark}/{canonical_task_id(task_id)}"


def aggregate(nodes):
    """Return per-task {identity: [op_mass, token_mass]} for leaf and path ids."""
    leaf = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    path = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    total_ops = 0
    total_tokens = 0
    sessions = set()
    tasks = set()
    for node in nodes.values():
        metrics = node.get("metrics") or {}
        ops = metrics.get("operations", 0)
        tokens = metrics.get("tokens", 0)
        if node["kind"] == "session":
            sessions.add(node["id"])
            tasks.add(task_of_session(node))
        if ops <= 0 and tokens <= 0:
            continue
        total_ops += ops
        total_tokens += tokens
        task = task_of_session(session_of(node, nodes))
        leaf_id = node["path"][-1]
        path_id = " / ".join(node["path"])
        for table, identity in ((leaf, leaf_id), (path, path_id)):
            table[task][identity][0] += ops
            table[task][identity][1] += tokens
    return leaf, path, total_ops, total_tokens, len(sessions), len(tasks)


def rank_agreement(table, min_distinct):
    """Per-task tau-b/rho between count-ranking and token-ranking.

    Returns (rows, skipped): rows are per-task dicts; skipped are task names
    with fewer than `min_distinct` distinct operation identities.
    """
    rows = []
    skipped = []
    for task in sorted(table):
        identities = table[task]
        if len(identities) < min_distinct:
            skipped.append(task)
            continue
        names = sorted(identities)
        counts = [identities[name][0] for name in names]
        tokens = [identities[name][1] for name in names]
        tau, tau_p = kendalltau(counts, tokens)
        rho, rho_p = spearmanr(counts, tokens)
        rows.append(
            {
                "task": task,
                "distinct_operations": len(names),
                "operation_mass": sum(counts),
                "token_mass": sum(tokens),
                "kendall_tau_b": tau,
                "kendall_tau_b_pvalue": tau_p,
                "spearman_rho": rho,
                "spearman_rho_pvalue": rho_p,
            }
        )
    return rows, skipped


def cluster_bootstrap(values, draws=BOOTSTRAP_DRAWS, seed=BOOTSTRAP_SEED):
    """Percentile 95% interval of the mean, resampling tasks (clusters)."""
    values = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    n = len(values)
    indices = rng.integers(0, n, size=(draws, n))
    means = values[indices].mean(axis=1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    return float(lo), float(hi)


def pooled_agreement(table):
    """Population-level ranking over all tasks combined."""
    pooled = defaultdict(lambda: [0, 0])
    for identities in table.values():
        for name, (ops, tokens) in identities.items():
            pooled[name][0] += ops
            pooled[name][1] += tokens
    names = sorted(pooled)
    counts = [pooled[name][0] for name in names]
    tokens = [pooled[name][1] for name in names]
    tau, tau_p = kendalltau(counts, tokens)
    rho, rho_p = spearmanr(counts, tokens)
    ranked_by_count = sorted(names, key=lambda n: (-pooled[n][0], n))
    ranked_by_tokens = sorted(names, key=lambda n: (-pooled[n][1], n))
    return {
        "distinct_operations": len(names),
        "kendall_tau_b": tau,
        "kendall_tau_b_pvalue": tau_p,
        "spearman_rho": rho,
        "spearman_rho_pvalue": rho_p,
        "top10_by_count": [
            {"operation": n, "count": pooled[n][0], "tokens": pooled[n][1]}
            for n in ranked_by_count[:10]
        ],
        "top10_by_tokens": [
            {"operation": n, "count": pooled[n][0], "tokens": pooled[n][1]}
            for n in ranked_by_tokens[:10]
        ],
    }


def analyze(table, label, min_distinct=MIN_DISTINCT_OPS):
    rows, skipped = rank_agreement(table, min_distinct)
    taus = np.array([r["kendall_tau_b"] for r in rows], dtype=float)
    rhos = np.array([r["spearman_rho"] for r in rows], dtype=float)
    result = {
        "label": label,
        "min_distinct_operations": min_distinct,
        "tasks_total": len(table),
        "tasks_skipped": len(skipped),
        "skipped_tasks": skipped,
        "tasks_scored": len(rows),
        "mean_kendall_tau_b": float(taus.mean()),
        "kendall_tau_b_bootstrap_ci95": list(cluster_bootstrap(taus)),
        "mean_spearman_rho": float(rhos.mean()),
        "spearman_rho_bootstrap_ci95": list(cluster_bootstrap(rhos)),
        "median_kendall_tau_b": float(np.median(taus)),
        "median_spearman_rho": float(np.median(rhos)),
        "pooled": pooled_agreement(table),
        "per_task": rows,
    }
    return result


def main():
    started = time.time()
    nodes = load_trace()
    leaf, path, total_ops, total_tokens, n_sessions, n_tasks = aggregate(nodes)

    folded_token_total = 0
    with FOLDED.open(encoding="utf-8") as handle:
        for line in handle:
            folded_token_total += int(line.rsplit(" ", 1)[1])

    results = {
        "experiment": "AgentReward 125-task rank agreement (RQ1 resource attribution)",
        "workspace": str(WORKSPACE.relative_to(REPO_ROOT)),
        "trace": str(TRACE.relative_to(REPO_ROOT)),
        "task_id_provenance": (
            "session node data.source_session is '<benchmark>__<task_id>__<model>' "
            "(Label.key in script/agentreward_diff_pprof_eval.py:53-58); task id is "
            "the middle segment, canonicalized with canonical_task_id() "
            "(script/agentreward_diff_pprof_eval.py:90-91): replace('.resized.', '.'). "
            "Weighted nodes reach their session by walking parent links."
        ),
        "population": {
            "sessions": n_sessions,
            "canonical_tasks": n_tasks,
            "trace_nodes": len(nodes),
        },
        "validity": {
            "operation_mass_trace": total_ops,
            "operation_mass_workspace_readme": WORKSPACE_OPERATION_TOTAL,
            "operation_mass_match": total_ops == WORKSPACE_OPERATION_TOTAL,
            "token_mass_trace": total_tokens,
            "token_mass_stacks_folded": folded_token_total,
            "token_mass_match": total_tokens == folded_token_total,
        },
        "bootstrap": {
            "draws": BOOTSTRAP_DRAWS,
            "seed": BOOTSTRAP_SEED,
            "method": "percentile 95% CI, resampling tasks (cluster bootstrap), "
            "numpy.random.default_rng",
        },
        "primary_leaf_level": analyze(leaf, "leaf operation name"),
        "secondary_path_level": analyze(path, "full semantic path"),
    }

    out = EXPERIMENT_DIR / "raw-results.json"
    out.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    elapsed = time.time() - started
    print(f"wrote {out} in {elapsed:.2f}s")
    print(json.dumps({k: v for k, v in results["validity"].items()}, indent=2))
    for key in ("primary_leaf_level", "secondary_path_level"):
        r = results[key]
        print(
            f"{key}: scored={r['tasks_scored']} skipped={r['tasks_skipped']} "
            f"mean tau-b={r['mean_kendall_tau_b']:.4f} {r['kendall_tau_b_bootstrap_ci95']} "
            f"mean rho={r['mean_spearman_rho']:.4f} {r['spearman_rho_bootstrap_ci95']} "
            f"pooled tau-b={r['pooled']['kendall_tau_b']:.4f} "
            f"pooled rho={r['pooled']['spearman_rho']:.4f}"
        )


if __name__ == "__main__":
    sys.exit(main())
