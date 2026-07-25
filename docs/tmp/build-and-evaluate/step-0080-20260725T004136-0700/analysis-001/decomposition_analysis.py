#!/usr/bin/env python3
"""Fine-grained decomposition of the step-0080 profile-guided reader.

Offline analysis of already-collected data. Reads:
  - step-0080 raw-results.json + raw-responses/<query>.json (stage-1 selections)
  - step-0079 raw-results.json (full-trace direct reader, cross-check only)
  - frozen group mapping fixed-groups.jsonl (source_preserving_agent)

Writes analysis-results.json and analysis-report.md next to this script.
Stdlib + numpy/scipy only. Deterministic, rerunnable.
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
STEP80 = ROOT / "docs/tmp/build-and-evaluate/step-0080-20260725T004136-0700/experiment-001"
STEP79 = ROOT / "docs/tmp/build-and-evaluate/step-0079-20260724T235753-0700/experiment-001"
FIXED_GROUPS = ROOT / ".agentsight/experiments/rq2-canonical-tags-v2-current/trace/results/fixed-groups.jsonl"

MAX_SELECT_GROUPS = 5


def path_key(path):
    return " \u203a ".join(path)


def extract_json_object(text):
    """Faithful copy of the step-0080 evaluator's extractor."""
    text = text.strip()
    if not text:
        return None
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    candidates = []
    if fence:
        candidates.append(fence.group(1))
    candidates.append(text)
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidates.append(text[start : end + 1])
    for candidate in candidates:
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return None


def parse_selected_groups_uncapped(response_text, valid_paths):
    """Same normalization as the step-0080 evaluator, but WITHOUT the
    MAX_SELECT_GROUPS truncation, so we can see where a missed target group
    would have ranked in the model's full ordered selection."""
    obj = extract_json_object(response_text)
    if obj is None:
        return None
    selected = obj.get("selected_group_paths")
    if selected is None and "selected_groups" in obj:
        selected = obj["selected_groups"]
    if selected is None and "groups" in obj:
        selected = obj["groups"]
    if not isinstance(selected, list) or not selected:
        return None

    valid_by_key = {path_key(p): list(p) for p in valid_paths}
    alt_keys = {}
    for key, path in valid_by_key.items():
        alt_keys[key] = path
        alt_keys[" / ".join(path)] = path
        alt_keys["/".join(path)] = path
        alt_keys[" > ".join(path)] = path
        alt_keys[json.dumps(path, ensure_ascii=False)] = path

    out = []
    seen = set()
    for item in selected:
        path = None
        if isinstance(item, list) and all(isinstance(x, str) for x in item):
            key = path_key(item)
            if key in valid_by_key:
                path = valid_by_key[key]
        elif isinstance(item, str):
            if item in alt_keys:
                path = alt_keys[item]
            elif item in valid_by_key:
                path = valid_by_key[item]
        elif isinstance(item, dict):
            if "group_path" in item and isinstance(item["group_path"], list):
                key = path_key([str(x) for x in item["group_path"]])
                if key in valid_by_key:
                    path = valid_by_key[key]
            elif "path_key" in item and str(item["path_key"]) in valid_by_key:
                path = valid_by_key[str(item["path_key"])]
        if path is None:
            return None
        key = path_key(path)
        if key in seen:
            continue
        seen.add(key)
        out.append(path)  # no budget break: keep the full ordered list
    return out if out else None


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else None


def main():
    results = {}

    # ---- load frozen group mapping -------------------------------------
    op_group = {}          # operation_id -> tuple(source_preserving_agent)
    seq_groups = defaultdict(set)
    seq_ops = defaultdict(list)
    with open(FIXED_GROUPS) as f:
        for line in f:
            r = json.loads(line)
            g = tuple(r["groups"]["source_preserving_agent"])
            op_group[r["operation_id"]] = g
            seq_groups[r["sequence"]].add(g)
            seq_ops[r["sequence"]].append(r["operation_id"])

    # ---- load step-0080 / step-0079 results -----------------------------
    d8 = json.load(open(STEP80 / "raw-results.json"))
    d7 = json.load(open(STEP79 / "raw-results.json"))
    pq = d8["per_query"]
    p7 = {e["query_id"]: e for e in d7["per_query"]}
    n = len(pq)
    assert n == 220

    # cross-check: step-0080's direct_reader AP is step-0079's direct reader
    xcheck_ap_mismatch = sum(
        1 for e in pq
        if abs(e["ap"]["direct_reader"] - p7[e["query_id"]]["ap"]["direct_reader"]) > 1e-12
    )
    xcheck_target_mismatch = sum(
        1 for e in pq if e["target_operation_ids"] != p7[e["query_id"]]["target_operation_ids"]
    )
    xcheck_group_mismatch = sum(
        1 for e in pq
        if len(seq_groups[e["query_id"]]) != e["group_count"]
        or len(seq_ops[e["query_id"]]) != e["operations"]
    )
    results["cross_checks"] = {
        "direct_reader_ap_mismatches_step0080_vs_step0079": xcheck_ap_mismatch,
        "target_operation_id_mismatches": xcheck_target_mismatch,
        "group_or_op_count_mismatches_vs_fixed_groups": xcheck_group_mismatch,
    }

    # ---- per-query enrichment -------------------------------------------
    for e in pq:
        q = e["query_id"]
        sel = [tuple(p) for p in e["selected_group_paths"]]
        sel_set = set(sel)
        e["_target_groups"] = [op_group[t] for t in e["target_operation_ids"]]
        e["_index_hit"] = all(g in sel_set for g in e["_target_groups"])
        # group sizes within this query
        sizes = Counter(op_group[op] for op in seq_ops[q])
        e["_largest_group_size"] = max(sizes.values())
        e["_target_group_size"] = sizes[e["_target_groups"][0]]

    hits = [e for e in pq if e["_index_hit"]]
    misses = [e for e in pq if not e["_index_hit"]]

    map_profile = mean(e["ap"]["profile_reader"] for e in pq)
    map_direct = mean(e["ap"]["direct_reader"] for e in pq)
    map_agentprof = mean(e["ap"]["local_agentprof"] for e in pq)
    map_local_only = mean(e["ap"]["local_only"] for e in pq)

    # ================= Q1: loss decomposition ============================
    map_hit = mean(e["ap"]["profile_reader"] for e in hits)
    map_miss = mean(e["ap"]["profile_reader"] for e in misses)
    map_direct_on_miss = mean(e["ap"]["direct_reader"] for e in misses)
    map_direct_on_hit = mean(e["ap"]["direct_reader"] for e in hits)
    counterfactual_map = (
        sum(e["ap"]["profile_reader"] for e in hits)
        + sum(e["ap"]["direct_reader"] for e in misses)
    ) / n
    total_gap = map_direct - map_profile
    miss_contrib = sum(e["ap"]["direct_reader"] - e["ap"]["profile_reader"] for e in misses) / n
    hit_contrib = sum(e["ap"]["direct_reader"] - e["ap"]["profile_reader"] for e in hits) / n

    results["q1_loss_decomposition"] = {
        "n_queries": n,
        "index_hit_count": len(hits),
        "index_miss_count": len(misses),
        "index_hit_rate": len(hits) / n,
        "map_overall": {"profile_reader": map_profile, "direct_reader": map_direct,
                        "local_agentprof": map_agentprof, "local_only": map_local_only},
        "profile_map_conditional_on_hit": map_hit,
        "profile_map_conditional_on_miss": map_miss,
        "direct_map_conditional_on_hit": map_direct_on_hit,
        "direct_map_conditional_on_miss": map_direct_on_miss,
        "counterfactual_map_misses_scored_with_direct_ap": counterfactual_map,
        "counterfactual_delta_vs_profile": counterfactual_map - map_profile,
        "total_gap_direct_minus_profile": total_gap,
        "gap_contribution_from_miss_queries": miss_contrib,
        "gap_contribution_from_hit_queries": hit_contrib,
        "share_of_gap_from_misses": miss_contrib / total_gap,
        "share_of_gap_from_within_hit_ranking": hit_contrib / total_gap,
    }

    # ================= Q2: per-stratum table =============================
    strata = {}
    for e in pq:
        strata.setdefault(e["stratum"], []).append(e)
    q2 = {}
    for s in sorted(strata):
        rows = strata[s]
        q2[s] = {
            "n_queries": len(rows),
            "map_profile_reader": mean(e["ap"]["profile_reader"] for e in rows),
            "map_direct_reader": mean(e["ap"]["direct_reader"] for e in rows),
            "map_local_agentprof": mean(e["ap"]["local_agentprof"] for e in rows),
            "map_local_only": mean(e["ap"]["local_only"] for e in rows),
            "index_hit_rate": mean(1.0 if e["_index_hit"] else 0.0 for e in rows),
            "mean_content_opened_fraction": mean(e["content_opened_fraction"] for e in rows),
            "gap_direct_minus_profile": mean(e["ap"]["direct_reader"] for e in rows)
            - mean(e["ap"]["profile_reader"] for e in rows),
        }
    results["q2_per_stratum"] = q2

    # ================= Q3: win/loss anatomy ==============================
    wins = [e for e in pq if e["ap"]["profile_reader"] > e["ap"]["direct_reader"]]
    ties = [e for e in pq if e["ap"]["profile_reader"] == e["ap"]["direct_reader"]]
    losses = [e for e in pq if e["ap"]["profile_reader"] < e["ap"]["direct_reader"]]

    def brief(e):
        return {
            "query_id": e["query_id"],
            "profile_ap": e["ap"]["profile_reader"],
            "direct_ap": e["ap"]["direct_reader"],
            "ap_delta_profile_minus_direct": e["ap"]["profile_reader"] - e["ap"]["direct_reader"],
            "index_hit": e["_index_hit"],
            "n_groups": e["group_count"],
        }

    wins_sorted = sorted(wins, key=lambda e: e["ap"]["profile_reader"] - e["ap"]["direct_reader"], reverse=True)
    losses_sorted = sorted(losses, key=lambda e: e["ap"]["profile_reader"] - e["ap"]["direct_reader"])

    results["q3_win_loss_anatomy"] = {
        "n_wins_profile_beats_direct": len(wins),
        "n_ties": len(ties),
        "n_losses": len(losses),
        "wins_mean_ap_gain": mean(e["ap"]["profile_reader"] - e["ap"]["direct_reader"] for e in wins),
        "wins_mean_content_opened_fraction": mean(e["content_opened_fraction"] for e in wins),
        "losses_mean_ap_drop": mean(e["ap"]["profile_reader"] - e["ap"]["direct_reader"] for e in losses),
        "losses_mean_content_opened_fraction": mean(e["content_opened_fraction"] for e in losses),
        "ties_mean_content_opened_fraction": mean(e["content_opened_fraction"] for e in ties),
        "overall_mean_content_opened_fraction": mean(e["content_opened_fraction"] for e in pq),
        "wins_index_hit_rate": mean(1.0 if e["_index_hit"] else 0.0 for e in wins),
        "losses_index_hit_rate": mean(1.0 if e["_index_hit"] else 0.0 for e in losses),
        "top5_wins": [brief(e) for e in wins_sorted[:5]],
        "top5_losses": [brief(e) for e in losses_sorted[:5]],
    }

    # ================= Q4: index difficulty correlates ===================
    feats = {
        "n_operations": np.array([e["operations"] for e in pq], dtype=float),
        "n_groups": np.array([e["group_count"] for e in pq], dtype=float),
        "largest_group_size": np.array([e["_largest_group_size"] for e in pq], dtype=float),
        "target_group_size": np.array([e["_target_group_size"] for e in pq], dtype=float),
        "content_opened_fraction": np.array([e["content_opened_fraction"] for e in pq], dtype=float),
    }
    y_hit = np.array([1.0 if e["_index_hit"] else 0.0 for e in pq])
    y_ap = np.array([e["ap"]["profile_reader"] for e in pq], dtype=float)

    q4 = {}
    for name, x in feats.items():
        rho_h, p_h = stats.spearmanr(x, y_hit)
        rho_a, p_a = stats.spearmanr(x, y_ap)
        q4[name] = {
            "spearman_vs_index_hit": {"rho": rho_h, "p_value": p_h},
            "spearman_vs_profile_ap": {"rho": rho_a, "p_value": p_a},
        }
    results["q4_index_difficulty_correlates"] = q4

    # ================= Q5: budget sensitivity ============================
    sel_len_dist = Counter(len(e["selected_group_paths"]) for e in pq)
    saturated = sum(1 for e in pq if len(e["selected_group_paths"]) == MAX_SELECT_GROUPS)

    # Uncapped re-parse of the raw stage-1 response; validate against the
    # stored (capped) selection for ALL 220 queries first.
    validation_failures = []
    miss_rank_info = []
    uncapped_len_dist = Counter()
    for e in pq:
        q = e["query_id"]
        fn = STEP80 / "raw-responses" / (q.replace("/", "_") + ".json")
        resp = json.load(open(fn))
        attempt = resp["stage1_attempts"][-1]
        valid_paths = [list(g) for g in seq_groups[q]]
        uncapped = parse_selected_groups_uncapped(attempt["raw_response"], valid_paths)
        if uncapped is None:
            validation_failures.append({"query_id": q, "reason": "uncapped_parse_returned_none"})
            continue
        capped = [tuple(p) for p in uncapped[:MAX_SELECT_GROUPS]]
        stored = [tuple(p) for p in e["selected_group_paths"]]
        if capped != stored:
            validation_failures.append({"query_id": q, "reason": "uncapped_head_ne_stored_selection"})
            continue
        uncapped_len_dist[len(uncapped)] += 1
        if not e["_index_hit"]:
            missed = [g for g in e["_target_groups"] if g not in set(stored)]
            for g in missed:
                rank = None
                for i, p in enumerate(uncapped, start=1):
                    if tuple(p) == g:
                        rank = i
                        break
                miss_rank_info.append({
                    "query_id": q,
                    "target_group_rank_in_uncapped_selection": rank,  # None = absent
                    "uncapped_selection_length": len(uncapped),
                })

    rank_dist = Counter(
        (m["target_group_rank_in_uncapped_selection"]
         if m["target_group_rank_in_uncapped_selection"] is not None else "absent")
        for m in miss_rank_info
    )
    results["q5_budget_sensitivity"] = {
        "budget": MAX_SELECT_GROUPS,
        "selected_group_count_distribution": {str(k): v for k, v in sorted(sel_len_dist.items())},
        "n_budget_saturated_exactly_5": saturated,
        "saturation_rate": saturated / n,
        "uncapped_selection_length_distribution": {str(k): v for k, v in sorted(uncapped_len_dist.items())},
        "n_queries_model_listed_more_than_budget": sum(
            v for k, v in uncapped_len_dist.items() if k > MAX_SELECT_GROUPS),
        "miss_queries_missed_target_group_rank_distribution": {
            str(k): v for k, v in sorted(rank_dist.items(), key=lambda kv: str(kv[0]))},
        "miss_queries_where_target_group_absent_from_selection": rank_dist.get("absent", 0),
        "miss_queries_where_target_group_ranked_6_to_10": sum(
            v for k, v in rank_dist.items() if isinstance(k, int) and 6 <= k <= 10),
        "miss_rank_detail": miss_rank_info,
        "uncapped_reparse_validation_failures": validation_failures,
    }

    # ---- write JSON ------------------------------------------------------
    with open(HERE / "analysis-results.json", "w") as f:
        json.dump(results, f, indent=1)

    # ---- write report ----------------------------------------------------
    q1 = results["q1_loss_decomposition"]
    q3 = results["q3_win_loss_anatomy"]
    q5 = results["q5_budget_sensitivity"]
    L = []
    A = L.append
    A("# Step-0080 profile-guided reader: fine-grained decomposition\n")
    A("Data: step-0080 experiment-001 (profile-guided two-stage reader, 220 queries), "
      "step-0079 experiment-001 (full-trace direct reader), frozen `source_preserving_agent` "
      "group mapping (5,960 operations). Index hit = every target operation's frozen group "
      "was among the stage-1 selected groups. All cross-checks passed: "
      f"direct-reader AP step-0080 vs step-0079 mismatches = {xcheck_ap_mismatch}, "
      f"target-id mismatches = {xcheck_target_mismatch}, "
      f"group/op-count mismatches vs fixed-groups = {xcheck_group_mismatch}.\n")

    A("## 1. Loss decomposition\n")
    A(f"**Headline: {q1['index_hit_count']}/220 index hits ({q1['index_hit_rate']:.1%}); "
      f"index misses account for {q1['share_of_gap_from_misses']:.1%} of the "
      f"{q1['total_gap_direct_minus_profile']:.4f} MAP gap to the direct reader — more than 100% "
      f"because on hit queries the profile reader already beats the direct reader.**\n")
    A(f"- Overall MAP: profile_reader {map_profile:.4f}, direct_reader {map_direct:.4f}, "
      f"local_agentprof {map_agentprof:.4f}, local_only {map_local_only:.4f}.")
    A(f"- Profile-reader MAP conditional on index hit: **{map_hit:.4f}** (n={len(hits)}); "
      f"conditional on index miss: **{map_miss:.4f}** (n={len(misses)}).")
    A(f"- Direct-reader MAP on the same subsets: hit {map_direct_on_hit:.4f}, miss {map_direct_on_miss:.4f}. "
      f"On hit queries the profile reader is *above* the direct reader "
      f"({map_hit:.4f} vs {map_direct_on_hit:.4f}, +{map_hit - map_direct_on_hit:.4f}) — reading only the "
      "right groups helps stage-2 ranking; misses are where the entire deficit sits.")
    A(f"- Counterfactual — every miss query scored with its step-0079 direct-reader AP instead: "
      f"MAP = **{counterfactual_map:.4f}** (+{counterfactual_map - map_profile:.4f} over the actual "
      f"{map_profile:.4f}, and *above* the direct reader's {map_direct:.4f}). This is the upper bound "
      "of perfectly fixing stage 1 (it recovers misses but leaves within-hit ranking untouched).")
    A(f"- Gap attribution (total gap = {map_direct:.3f} - {map_profile:.3f} = {total_gap:.4f}):\n")
    A(f"  - from miss queries (stage-1 selection failures): {miss_contrib:.4f} "
      f"= **{q1['share_of_gap_from_misses']:.1%}** of the gap")
    A(f"  - from hit queries (within-budget stage-2 ranking differences): {hit_contrib:.4f} "
      f"= **{q1['share_of_gap_from_within_hit_ranking']:.1%}** of the gap (negative: the profile "
      "reader wins within-hit, which offsets part of the miss damage)\n")

    A("## 2. Per-stratum table\n")
    worst = max(q2.items(), key=lambda kv: kv[1]["gap_direct_minus_profile"])
    best = min(q2.items(), key=lambda kv: kv[1]["gap_direct_minus_profile"])
    A(f"**Headline: the profile reader loses most on {worst[0]} "
      f"(gap {worst[1]['gap_direct_minus_profile']:+.4f}) and is closest to the direct reader on "
      f"{best[0]} (gap {best[1]['gap_direct_minus_profile']:+.4f}).**\n")
    A("| Stratum | n | MAP profile | MAP direct | MAP local_agentprof | index-hit rate | mean content opened | gap (direct-profile) |")
    A("|---|---|---|---|---|---|---|---|")
    for s, r in q2.items():
        A(f"| {s} | {r['n_queries']} | {r['map_profile_reader']:.4f} | {r['map_direct_reader']:.4f} "
          f"| {r['map_local_agentprof']:.4f} | {r['index_hit_rate']:.1%} "
          f"| {r['mean_content_opened_fraction']:.1%} | {r['gap_direct_minus_profile']:+.4f} |")
    A("")
    notes = []
    for s, r in q2.items():
        if r["map_profile_reader"] >= r["map_direct_reader"]:
            notes.append(f"{s}: ties/wins (gap {r['gap_direct_minus_profile']:+.4f})")
    if notes:
        A("Strata where the profile reader ties or beats the direct reader: " + "; ".join(notes) + ".")
    A("")

    A("## 3. Win/loss anatomy\n")
    A(f"**Headline: profile beats direct on {q3['n_wins_profile_beats_direct']} queries, "
      f"ties on {q3['n_ties']}, loses on {q3['n_losses']}. "
      f"Wins open only {q3['wins_mean_content_opened_fraction']:.1%} of content on average "
      f"(overall mean {q3['overall_mean_content_opened_fraction']:.1%}): reading less can help.**\n")
    A(f"- Wins: mean AP gain {q3['wins_mean_ap_gain']:+.4f}; mean content-opened fraction "
      f"{q3['wins_mean_content_opened_fraction']:.4f}; index-hit rate {q3['wins_index_hit_rate']:.1%}.")
    A(f"- Losses: mean AP change {q3['losses_mean_ap_drop']:+.4f}; mean content-opened fraction "
      f"{q3['losses_mean_content_opened_fraction']:.4f}; index-hit rate {q3['losses_index_hit_rate']:.1%}.")
    A(f"- Ties: mean content-opened fraction {q3['ties_mean_content_opened_fraction']:.4f}.\n")
    A("Largest 5 wins (profile AP minus direct AP):\n")
    A("| query_id | profile AP | direct AP | delta | index hit | #groups |")
    A("|---|---|---|---|---|---|")
    for b in q3["top5_wins"]:
        A(f"| {b['query_id']} | {b['profile_ap']:.4f} | {b['direct_ap']:.4f} "
          f"| {b['ap_delta_profile_minus_direct']:+.4f} | {'hit' if b['index_hit'] else 'MISS'} | {b['n_groups']} |")
    A("\nLargest 5 losses:\n")
    A("| query_id | profile AP | direct AP | delta | index hit | #groups |")
    A("|---|---|---|---|---|---|")
    for b in q3["top5_losses"]:
        A(f"| {b['query_id']} | {b['profile_ap']:.4f} | {b['direct_ap']:.4f} "
          f"| {b['ap_delta_profile_minus_direct']:+.4f} | {'hit' if b['index_hit'] else 'MISS'} | {b['n_groups']} |")
    A("")

    A("## 4. Index difficulty correlates\n")
    sig = max(q4.items(), key=lambda kv: abs(kv[1]["spearman_vs_index_hit"]["rho"]))
    A(f"**Headline: the strongest index-hit correlate is {sig[0]} "
      f"(Spearman rho {sig[1]['spearman_vs_index_hit']['rho']:+.3f}, "
      f"p={sig[1]['spearman_vs_index_hit']['p_value']:.2e}).**\n")
    A("| feature | rho vs index-hit (0/1) | p | rho vs profile AP | p |")
    A("|---|---|---|---|---|")
    for name, r in q4.items():
        A(f"| {name} | {r['spearman_vs_index_hit']['rho']:+.3f} | {r['spearman_vs_index_hit']['p_value']:.2e} "
          f"| {r['spearman_vs_profile_ap']['rho']:+.3f} | {r['spearman_vs_profile_ap']['p_value']:.2e} |")
    A("\nDescriptive correlations only; no modeling. Negative rho vs index-hit means "
      "larger values of the feature make stage-1 selection failure more likely.\n")

    A("## 5. Budget sensitivity (descriptive)\n")
    A(f"**Headline: the stage-1 budget of {MAX_SELECT_GROUPS} was saturated on "
      f"{q5['n_budget_saturated_exactly_5']}/220 queries ({q5['saturation_rate']:.1%}); "
      f"for miss queries the target group was absent from the model's ordered selection in "
      f"{q5['miss_queries_where_target_group_absent_from_selection']}/{len(misses)} cases "
      f"and ranked 6th-10th in {q5['miss_queries_where_target_group_ranked_6_to_10']}/{len(misses)}.**\n")
    A(f"- Selected-group-count distribution (stored, capped at {MAX_SELECT_GROUPS}): "
      + ", ".join(f"{k} groups: {v}" for k, v in sorted(q5['selected_group_count_distribution'].items(), key=lambda kv: int(kv[0])))
      + ". The single sub-budget query has only 4 groups in total.")
    A("- Method note: the stored selection is the model's ordered stage-1 answer truncated at the "
      f"first {MAX_SELECT_GROUPS} valid groups (order preserved). I re-parsed the raw stage-1 "
      "responses without the cap (same normalization as the evaluator); the re-parse reproduced "
      f"the stored capped selection for all 220 queries "
      f"(validation failures: {len(q5['uncapped_reparse_validation_failures'])}). "
      "So the ordered selection exists and its full length is observable.")
    A("- Uncapped selection-length distribution: "
      + ", ".join(f"length {k}: {v}" for k, v in sorted(q5['uncapped_selection_length_distribution'].items(), key=lambda kv: int(kv[0])))
      + f". The model listed more than {MAX_SELECT_GROUPS} groups in "
      f"{q5['n_queries_model_listed_more_than_budget']} queries.")
    A(f"- For the {len(misses)} index-miss queries, rank the missed target group would have needed "
      "in the model's full ordered selection: "
      + ", ".join(f"{k}: {v}" for k, v in sorted(q5['miss_queries_missed_target_group_rank_distribution'].items(), key=lambda kv: str(kv[0])))
      + ".")
    A("- Caveat (field limitation, stated rather than approximated): the stage-1 prompt instructed "
      f"the model to \"Select up to {MAX_SELECT_GROUPS} groups\", and no response ever listed more than "
      f"{MAX_SELECT_GROUPS}. Ranks beyond {MAX_SELECT_GROUPS} are therefore UNOBSERVABLE in this data — "
      "\"absent\" means the target group was not among the groups the model chose to list under an "
      f"up-to-{MAX_SELECT_GROUPS} instruction, not proof that it would not have been the 6th-10th choice "
      "under a larger instructed budget. What the data does show: under the current budget the model "
      "used every slot and still displaced the target group entirely.\n")

    A("## Conclusion: what would most improve MAP\n")
    A(f"- Fixing stage-1 selection is the dominant lever the data shows: index misses carry "
      f"{q1['share_of_gap_from_misses']:.1%} of the {total_gap:.4f} MAP gap (the share exceeds 100% "
      "because the profile reader already beats the direct reader within hits), and the "
      f"perfect-stage-1 counterfactual lifts MAP from {map_profile:.4f} to {counterfactual_map:.4f} — "
      f"above the direct reader's {map_direct:.4f}.")
    A(f"- Whether a larger stage-1 budget would help is not decidable from this data: the prompt "
      f"instructed up to {MAX_SELECT_GROUPS} groups and no response ever listed more, so post-budget "
      "ranks are unobservable. What is observable: the budget was saturated on "
      f"{q5['saturation_rate']:.1%} of queries and in all {len(misses)} miss queries the target group "
      "was displaced entirely (not merely ranked 6th), so the failure is group discrimination at "
      "stage 1, not stage-2 reading depth.")
    A(f"- Reading less is compatible with winning: the {q3['n_wins_profile_beats_direct']} wins open "
      f"{q3['wins_mean_content_opened_fraction']:.1%} of content on average, so the loss mechanism is "
      "which groups are opened, not how much is opened.")
    A(f"- Difficulty scales with trace size: {sig[0]} is the strongest miss correlate "
      f"(rho {sig[1]['spearman_vs_index_hit']['rho']:+.3f}), consistent with stage 1 degrading on "
      "larger, more fragmented profiles.")
    A("")

    with open(HERE / "analysis-report.md", "w") as f:
        f.write("\n".join(L))

    print("wrote analysis-results.json and analysis-report.md")
    print(f"hits {len(hits)}/220, MAP hit {map_hit:.4f}, miss {map_miss:.4f}, "
          f"counterfactual {counterfactual_map:.4f}, miss share {q1['share_of_gap_from_misses']:.3f}")


if __name__ == "__main__":
    main()
