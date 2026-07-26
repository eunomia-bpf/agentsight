#!/home/yunwei37/workspace/.venv/bin/python3
"""Deterministically recompute every AgentRewardBench Case Study 2 quantity.

The script is intentionally read-only with respect to all scientific inputs.
It imports the registered post-annotation scorer so AP and bootstrap execution
use the exact existing harness code path. By default it creates the three
remaining deliverables beside this script and refuses to overwrite any path.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import shlex
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


PAPER_VALUES = {
    "pair_occurrences": "338",
    "bad_operation_occurrences": "7,366",
    "good_operation_occurrences": "3,780",
    "bad_recovery_occurrences": "3,286",
    "good_recovery_occurrences": "455",
    "bad_completion_occurrences": "135",
    "good_completion_occurrences": "191",
    "bad_recovery_share": "44.6%",
    "good_recovery_share": "12.0%",
    "bad_completion_share": "1.8%",
    "good_completion_share": "5.1%",
    "consensus_looping_trajectories": "435",
    "looping_prevalence": ".398",
    "recursive_recovery_ap": ".634",
    "recursive_minus_prevalence_95ci": "[.181,.293]",
    "fixed_chain_projection_ap": ".656",
    "recursive_minus_fixed_95ci": "[-.107,.061]",
}


def find_repo_root(script: Path) -> Path:
    for candidate in script.parents:
        if (
            (candidate / "script" / "agentreward_diff_pprof_eval.py").is_file()
            and (candidate / "script" / "agentreward_recursive_diff_eval.py").is_file()
        ):
            return candidate
    raise RuntimeError("cannot locate repository root from script path")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def file_identity(repo: Path, path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    return {
        "path": str(resolved.relative_to(repo)),
        "absolute_path": str(resolved),
        "bytes": resolved.stat().st_size,
        "sha256": sha256(resolved),
    }


def load_registered_scorer(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(
        "registered_agentreward_recursive_diff_eval", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import registered scorer: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def compact_decimal(value: float, digits: int = 3) -> str:
    rendered = f"{value:.{digits}f}"
    if rendered.startswith("-0."):
        return "-" + rendered[2:]
    if rendered.startswith("0."):
        return rendered[1:]
    return rendered


def interval_display(values: Iterable[float]) -> str:
    left, right = values
    return f"[{compact_decimal(left)},{compact_decimal(right)}]"


def contextual_prefixes(
    rows: list[dict[str, Any]],
    paths: dict[str, list[str]],
    target: str,
) -> Counter[tuple[str, ...]]:
    prefixes: Counter[tuple[str, ...]] = Counter()
    for row in rows:
        evidence_id = str(row["fields"]["evidence_id"])
        path = paths[evidence_id]
        if target not in path:
            continue
        target_index = path.index(target)
        prefixes[tuple(path[: target_index + 1])] += int(row.get("value", 1))
    return prefixes


def quantity(
    *,
    value: Any,
    unit: str,
    definition: str,
    input_files: list[dict[str, Any]],
    code_files: list[dict[str, Any]],
    paper_display: str,
    recomputed_display: str,
    seed: int | None = None,
) -> dict[str, Any]:
    return {
        "value": value,
        "unit": unit,
        "definition": definition,
        "input_files": input_files,
        "code_files": code_files,
        "seed": seed,
        "paper_currently_displayed": paper_display,
        "recomputed_at_paper_precision": recomputed_display,
        "match_at_paper_precision": paper_display == recomputed_display,
    }


def render_results(record: dict[str, Any]) -> str:
    order = [
        ("pair_occurrences", "Bad--good pair occurrences"),
        ("bad_operation_occurrences", "Bad-side operation occurrences"),
        ("good_operation_occurrences", "Good-side operation occurrences"),
        ("bad_recovery_occurrences", "Bad-side recovery occurrences"),
        ("good_recovery_occurrences", "Good-side recovery occurrences"),
        ("bad_completion_occurrences", "Bad-side completion occurrences"),
        ("good_completion_occurrences", "Good-side completion occurrences"),
        ("bad_recovery_share", "Bad-side recovery share"),
        ("good_recovery_share", "Good-side recovery share"),
        ("bad_completion_share", "Bad-side completion share"),
        ("good_completion_share", "Good-side completion share"),
        ("consensus_looping_trajectories", "Consensus expert-looping labels"),
        ("looping_prevalence", "Expert-looping prevalence"),
        ("recursive_recovery_ap", "Recovery-exposure AP"),
        (
            "recursive_minus_prevalence_95ci",
            "AP minus prevalence, 95% task-cluster interval",
        ),
        ("fixed_chain_projection_ap", "Fixed-chain projection AP"),
        (
            "recursive_minus_fixed_95ci",
            "Recursive minus fixed, 95% task-cluster interval",
        ),
    ]
    rows = []
    mismatches = []
    for key, label in order:
        item = record["quantities"][key]
        status = "match" if item["match_at_paper_precision"] else "mismatch"
        rows.append(
            f"| {label} | {item['paper_currently_displayed']} | "
            f"{item['recomputed_at_paper_precision']} | {status} |"
        )
        if status == "mismatch":
            mismatches.append(
                f"- **{label}:** authoritative recomputed value is "
                f"`{item['recomputed_at_paper_precision']}`."
            )

    identity_rows = []
    for name, item in record["input_registry"].items():
        identity_rows.append(
            f"| `{name}` | `{item['path']}` | `{item['sha256']}` | {item['bytes']:,} |"
        )

    prefix_sections = []
    for selector_name in ("recovery", "completion"):
        selector = record["path_selectors"][selector_name]
        prefix_rows = []
        for row in selector["contextual_prefixes"]:
            path = " → ".join(f"`{component}`" for component in row["path"])
            prefix_rows.append(
                f"| {path} | {row['bad_occurrences']:,} | "
                f"{row['good_occurrences']:,} |"
            )
        prefix_sections.append(
            f"""### {selector_name.capitalize()}

Exact selector: an applied operation path contains the exact component
`{selector['exact_component']}`. For auditability, the prefix is the complete
path from its root through the first occurrence of that component (inclusive);
this preserves the registered membership predicate when a nested path repeats
the same label.

| Exact contextual prefix | Bad occurrences | Good occurrences |
|---|---:|---:|
{chr(10).join(prefix_rows)}
"""
        )

    mismatch_text = (
        "\n".join(mismatches)
        if mismatches
        else "No quantity mismatches the paper at its currently displayed precision."
    )
    score = record["scoring_details"]
    return f"""# Case Study 2 deterministic recomputation

All quantities were recomputed from the version-pinned frozen workspace,
pair-occurrence inputs, fixed pair manifest, and consensus expert labels. No
model was called and no annotation was changed.

## Quantity comparison

| Quantity | Paper value | Recomputed value | Match/mismatch |
|---|---:|---:|---|
{chr(10).join(rows)}

{mismatch_text}

Full-precision AP values are `{score['recursive_ap']:.16f}` (recursive) and
`{score['fixed_chain_ap']:.16f}` (fixed); prevalence is
`{score['prevalence']:.16f}`. The bootstrap uses seed
`{score['bootstrap_seed']}` and retains `{score['bootstrap_draws']:,}` draws
over `{score['tasks']}` task clusters. The 435 consensus trajectories contain
`{score['positive_looping']}` positive and `{score['negative_looping']}`
negative labels.

## Exact responsibility path prefixes

The occurrence selector follows the registered harness semantics: it tests
exact component membership in each CLI-applied tool path. The following tables
make every contextual prefix through the selected responsibility explicit.

{chr(10).join(prefix_sections)}
## Frozen-artifact and input identity

| ID | Repository-relative path | SHA-256 | Bytes |
|---|---|---|---:|
{chr(10).join(identity_rows)}

`trace.jsonl` is the computational source of applied paths. `annotation.json`
and `stacks.folded` are also pinned above to identify the complete terminal
recursive workspace, although the registered endpoint scorer does not reread
them. The pair-expanded bad/good operation files supply occurrence weights;
`pairs.json` supplies the fixed task/pair relation; and `annotations.csv`
supplies only the post-annotation consensus looping endpoint.

## Method

- Pair totals are sums of integer `value` over the fixed pair-expanded side.
- Responsibility totals include a row iff its applied path contains the exact
  registered component; shares divide that total by the same side's total.
- Recovery exposure is computed on unique trajectories after deduplicating
  pair reuse: recovery operations divided by all operations in that trajectory.
- The registered fixed-chain score is the fraction whose `result` starts with
  `error:` or equals `repeated`.
- AP is scikit-learn's ordinary non-interpolated `average_precision_score`.
  The scorer sorts eligible sessions, resamples the sorted task IDs with
  NumPy `default_rng(20260722)`, includes every trajectory for each sampled
  task, and takes NumPy's 2.5% and 97.5% quantiles.
"""


def compute(script: Path) -> dict[str, Any]:
    repo = find_repo_root(script)
    paths_by_id = {
        "task_spec": script.parent / "task-spec.md",
        "workspace_trace": repo
        / "docs/visexp/out/agentreward-diff-pprof-v1/recursive-annotation-v1/trace.jsonl",
        "workspace_annotation": repo
        / "docs/visexp/out/agentreward-diff-pprof-v1/recursive-annotation-v1/annotation.json",
        "workspace_stacks": repo
        / "docs/visexp/out/agentreward-diff-pprof-v1/recursive-annotation-v1/stacks.folded",
        "pair_manifest": repo
        / ".agentsight/experiments/agentreward-diff-pprof-v1/"
        "aggregate-evidence-release-v2/pairs.json",
        "bad_operations": repo
        / ".agentsight/experiments/agentreward-diff-pprof-v1/"
        "aggregate-evidence-release-v2/aggregate/bad.operations.jsonl",
        "good_operations": repo
        / ".agentsight/experiments/agentreward-diff-pprof-v1/"
        "aggregate-evidence-release-v2/aggregate/good.operations.jsonl",
        "expert_labels": repo
        / ".agentsight/external/agentreward-full/data/annotations.csv",
        "pair_harness": repo / "script/agentreward_diff_pprof_eval.py",
        "registered_scorer": repo / "script/agentreward_recursive_diff_eval.py",
        "recompute_script": script,
    }
    missing = [str(path) for path in paths_by_id.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("required input files are missing: " + ", ".join(missing))
    identities = {
        name: file_identity(repo, path) for name, path in paths_by_id.items()
    }

    scorer = load_registered_scorer(paths_by_id["registered_scorer"])
    if scorer.BOOTSTRAP_SEED != 20260722 or scorer.BOOTSTRAP_DRAWS != 10_000:
        raise RuntimeError(
            "registered scorer seed/draw count changed: "
            f"{scorer.BOOTSTRAP_SEED}/{scorer.BOOTSTRAP_DRAWS}"
        )

    applied = scorer.applied_paths(paths_by_id["workspace_trace"])
    bad = scorer.read_jsonl(paths_by_id["bad_operations"])
    good = scorer.read_jsonl(paths_by_id["good_operations"])
    pair_rows = json.loads(paths_by_id["pair_manifest"].read_text(encoding="utf-8"))

    for side_name, rows in (("bad", bad), ("good", good)):
        missing_evidence = sorted(
            {
                str(row["fields"]["evidence_id"])
                for row in rows
                if str(row["fields"]["evidence_id"]) not in applied
            }
        )
        if missing_evidence:
            raise RuntimeError(
                f"{side_name} side has {len(missing_evidence)} evidence IDs "
                "absent from the frozen workspace"
            )

    bad_total = sum(int(row.get("value", 1)) for row in bad)
    good_total = sum(int(row.get("value", 1)) for row in good)
    recovery = str(scorer.RECOVERY_OPERATION)
    completion = str(scorer.COMPLETION_OPERATION)
    recovery_bad_prefixes = contextual_prefixes(bad, applied, recovery)
    recovery_good_prefixes = contextual_prefixes(good, applied, recovery)
    completion_bad_prefixes = contextual_prefixes(bad, applied, completion)
    completion_good_prefixes = contextual_prefixes(good, applied, completion)
    bad_recovery = sum(recovery_bad_prefixes.values())
    good_recovery = sum(recovery_good_prefixes.values())
    bad_completion = sum(completion_bad_prefixes.values())
    good_completion = sum(completion_good_prefixes.values())

    score_start = time.perf_counter()
    sessions = scorer.unique_session_rows(bad, good, applied)
    score = scorer.score_looping(
        sessions,
        scorer.consensus_looping(paths_by_id["expert_labels"].parents[1]),
        scorer.task_by_session(pair_rows),
    )
    score_wall = time.perf_counter() - score_start

    aggregate_inputs = [
        identities["pair_manifest"],
        identities["bad_operations"],
        identities["good_operations"],
    ]
    responsibility_inputs = [
        identities["workspace_trace"],
        identities["bad_operations"],
        identities["good_operations"],
    ]
    score_inputs = [
        identities["workspace_trace"],
        identities["pair_manifest"],
        identities["bad_operations"],
        identities["good_operations"],
        identities["expert_labels"],
    ]
    pair_code = [identities["recompute_script"], identities["pair_harness"]]
    score_code = [identities["recompute_script"], identities["registered_scorer"]]

    displays = {
        "pair_occurrences": f"{len(pair_rows):,}",
        "bad_operation_occurrences": f"{bad_total:,}",
        "good_operation_occurrences": f"{good_total:,}",
        "bad_recovery_occurrences": f"{bad_recovery:,}",
        "good_recovery_occurrences": f"{good_recovery:,}",
        "bad_completion_occurrences": f"{bad_completion:,}",
        "good_completion_occurrences": f"{good_completion:,}",
        "bad_recovery_share": f"{100 * bad_recovery / bad_total:.1f}%",
        "good_recovery_share": f"{100 * good_recovery / good_total:.1f}%",
        "bad_completion_share": f"{100 * bad_completion / bad_total:.1f}%",
        "good_completion_share": f"{100 * good_completion / good_total:.1f}%",
        "consensus_looping_trajectories": f"{score['trajectories']:,}",
        "looping_prevalence": compact_decimal(score["prevalence"]),
        "recursive_recovery_ap": compact_decimal(score["recursive_ap"]),
        "recursive_minus_prevalence_95ci": interval_display(
            score["recursive_minus_prevalence_95ci"]
        ),
        "fixed_chain_projection_ap": compact_decimal(score["fixed_chain_ap"]),
        "recursive_minus_fixed_95ci": interval_display(
            score["recursive_minus_fixed_95ci"]
        ),
    }

    quantities = {
        "pair_occurrences": quantity(
            value=len(pair_rows),
            unit="bad--good pairs",
            definition="Number of rows in the fixed pair manifest.",
            input_files=[identities["pair_manifest"]],
            code_files=pair_code,
            paper_display=PAPER_VALUES["pair_occurrences"],
            recomputed_display=displays["pair_occurrences"],
        ),
        "bad_operation_occurrences": quantity(
            value=bad_total,
            unit="pair-weighted operation occurrences",
            definition="Sum of integer value over the pair-expanded bad-side rows.",
            input_files=aggregate_inputs,
            code_files=pair_code,
            paper_display=PAPER_VALUES["bad_operation_occurrences"],
            recomputed_display=displays["bad_operation_occurrences"],
        ),
        "good_operation_occurrences": quantity(
            value=good_total,
            unit="pair-weighted operation occurrences",
            definition="Sum of integer value over the pair-expanded good-side rows.",
            input_files=aggregate_inputs,
            code_files=pair_code,
            paper_display=PAPER_VALUES["good_operation_occurrences"],
            recomputed_display=displays["good_operation_occurrences"],
        ),
        "bad_recovery_occurrences": quantity(
            value=bad_recovery,
            unit="pair-weighted operation occurrences",
            definition=(
                "Bad-side row weight whose frozen applied path contains the exact "
                f"component {recovery!r}."
            ),
            input_files=responsibility_inputs,
            code_files=score_code,
            paper_display=PAPER_VALUES["bad_recovery_occurrences"],
            recomputed_display=displays["bad_recovery_occurrences"],
        ),
        "good_recovery_occurrences": quantity(
            value=good_recovery,
            unit="pair-weighted operation occurrences",
            definition=(
                "Good-side row weight whose frozen applied path contains the exact "
                f"component {recovery!r}."
            ),
            input_files=responsibility_inputs,
            code_files=score_code,
            paper_display=PAPER_VALUES["good_recovery_occurrences"],
            recomputed_display=displays["good_recovery_occurrences"],
        ),
        "bad_completion_occurrences": quantity(
            value=bad_completion,
            unit="pair-weighted operation occurrences",
            definition=(
                "Bad-side row weight whose frozen applied path contains the exact "
                f"component {completion!r}."
            ),
            input_files=responsibility_inputs,
            code_files=score_code,
            paper_display=PAPER_VALUES["bad_completion_occurrences"],
            recomputed_display=displays["bad_completion_occurrences"],
        ),
        "good_completion_occurrences": quantity(
            value=good_completion,
            unit="pair-weighted operation occurrences",
            definition=(
                "Good-side row weight whose frozen applied path contains the exact "
                f"component {completion!r}."
            ),
            input_files=responsibility_inputs,
            code_files=score_code,
            paper_display=PAPER_VALUES["good_completion_occurrences"],
            recomputed_display=displays["good_completion_occurrences"],
        ),
        "bad_recovery_share": quantity(
            value=bad_recovery / bad_total,
            unit="fraction of bad-side operation occurrences",
            definition="Bad recovery occurrences divided by all bad occurrences.",
            input_files=responsibility_inputs,
            code_files=score_code,
            paper_display=PAPER_VALUES["bad_recovery_share"],
            recomputed_display=displays["bad_recovery_share"],
        ),
        "good_recovery_share": quantity(
            value=good_recovery / good_total,
            unit="fraction of good-side operation occurrences",
            definition="Good recovery occurrences divided by all good occurrences.",
            input_files=responsibility_inputs,
            code_files=score_code,
            paper_display=PAPER_VALUES["good_recovery_share"],
            recomputed_display=displays["good_recovery_share"],
        ),
        "bad_completion_share": quantity(
            value=bad_completion / bad_total,
            unit="fraction of bad-side operation occurrences",
            definition="Bad completion occurrences divided by all bad occurrences.",
            input_files=responsibility_inputs,
            code_files=score_code,
            paper_display=PAPER_VALUES["bad_completion_share"],
            recomputed_display=displays["bad_completion_share"],
        ),
        "good_completion_share": quantity(
            value=good_completion / good_total,
            unit="fraction of good-side operation occurrences",
            definition="Good completion occurrences divided by all good occurrences.",
            input_files=responsibility_inputs,
            code_files=score_code,
            paper_display=PAPER_VALUES["good_completion_share"],
            recomputed_display=displays["good_completion_share"],
        ),
        "consensus_looping_trajectories": quantity(
            value=score["trajectories"],
            unit="unique trajectories",
            definition=(
                "Unique pair-population trajectories with unanimous Yes/No expert "
                "trajectory_looping annotations."
            ),
            input_files=score_inputs,
            code_files=score_code,
            paper_display=PAPER_VALUES["consensus_looping_trajectories"],
            recomputed_display=displays["consensus_looping_trajectories"],
        ),
        "looping_prevalence": quantity(
            value=score["prevalence"],
            unit="positive fraction",
            definition="Consensus looping positives divided by eligible trajectories.",
            input_files=score_inputs,
            code_files=score_code,
            paper_display=PAPER_VALUES["looping_prevalence"],
            recomputed_display=displays["looping_prevalence"],
        ),
        "recursive_recovery_ap": quantity(
            value=score["recursive_ap"],
            unit="average precision",
            definition=(
                "Ordinary non-interpolated AP of unique-trajectory recovery exposure "
                "against consensus expert looping labels."
            ),
            input_files=score_inputs,
            code_files=score_code,
            paper_display=PAPER_VALUES["recursive_recovery_ap"],
            recomputed_display=displays["recursive_recovery_ap"],
        ),
        "recursive_minus_prevalence_95ci": quantity(
            value=score["recursive_minus_prevalence_95ci"],
            unit="average-precision difference",
            definition=(
                "2.5% and 97.5% quantiles of recovery AP minus resample prevalence "
                "under task-cluster bootstrap."
            ),
            input_files=score_inputs,
            code_files=score_code,
            seed=score["bootstrap_seed"],
            paper_display=PAPER_VALUES["recursive_minus_prevalence_95ci"],
            recomputed_display=displays["recursive_minus_prevalence_95ci"],
        ),
        "fixed_chain_projection_ap": quantity(
            value=score["fixed_chain_ap"],
            unit="average precision",
            definition=(
                "Ordinary non-interpolated AP of the unique-trajectory fraction "
                "whose fixed-chain result is repeated or starts with error:."
            ),
            input_files=score_inputs,
            code_files=score_code,
            paper_display=PAPER_VALUES["fixed_chain_projection_ap"],
            recomputed_display=displays["fixed_chain_projection_ap"],
        ),
        "recursive_minus_fixed_95ci": quantity(
            value=score["recursive_minus_fixed_95ci"],
            unit="average-precision difference",
            definition=(
                "2.5% and 97.5% quantiles of recursive recovery AP minus fixed-chain "
                "AP under the same task-cluster bootstrap draw."
            ),
            input_files=score_inputs,
            code_files=score_code,
            seed=score["bootstrap_seed"],
            paper_display=PAPER_VALUES["recursive_minus_fixed_95ci"],
            recomputed_display=displays["recursive_minus_fixed_95ci"],
        ),
    }

    def combine_prefixes(
        bad_prefixes: Counter[tuple[str, ...]],
        good_prefixes: Counter[tuple[str, ...]],
    ) -> list[dict[str, Any]]:
        return [
            {
                "path": list(path),
                "bad_occurrences": bad_prefixes[path],
                "good_occurrences": good_prefixes[path],
            }
            for path in sorted(set(bad_prefixes) | set(good_prefixes))
        ]

    return {
        "schema_version": 1,
        "title": "AgentRewardBench Case Study 2 deterministic primary record",
        "policy": {
            "deterministic_recomputation_only": True,
            "llm_calls": 0,
            "annotations_modified": False,
            "existing_files_overwritten": False,
        },
        "environment": {
            "python_executable": sys.executable,
            "python_version": sys.version.split()[0],
            "numpy_version": importlib.metadata.version("numpy"),
            "scikit_learn_version": importlib.metadata.version("scikit-learn"),
        },
        "input_registry": identities,
        "frozen_workspace_identity": [
            identities["workspace_trace"],
            identities["workspace_annotation"],
            identities["workspace_stacks"],
        ],
        "path_selectors": {
            "recovery": {
                "exact_component": recovery,
                "predicate": f"{recovery!r} in applied_path",
                "contextual_prefix_definition": (
                    "applied_path from root through the first occurrence of the "
                    "exact component, inclusive"
                ),
                "contextual_prefixes": combine_prefixes(
                    recovery_bad_prefixes, recovery_good_prefixes
                ),
            },
            "completion": {
                "exact_component": completion,
                "predicate": f"{completion!r} in applied_path",
                "contextual_prefix_definition": (
                    "applied_path from root through the first occurrence of the "
                    "exact component, inclusive"
                ),
                "contextual_prefixes": combine_prefixes(
                    completion_bad_prefixes, completion_good_prefixes
                ),
            },
        },
        "scoring_details": {
            **score,
            "consensus_conflicts_excluded": len(sessions) - score["trajectories"],
            "bootstrap_requested_draws": scorer.BOOTSTRAP_DRAWS,
            "recovery_exposure_definition": (
                "unique recovery operations / unique operations in trajectory"
            ),
            "fixed_projection_definition": (
                "unique operations with result == repeated or result starting "
                "with error: / unique operations in trajectory"
            ),
            "pair_reuse_policy": (
                "pair occurrences weight signed totals; evidence IDs are deduplicated "
                "before trajectory-level AP"
            ),
        },
        "quantities": quantities,
        "all_match_at_paper_precision": all(
            item["match_at_paper_precision"] for item in quantities.values()
        ),
        "_execution": {"bootstrap_scoring_wall_seconds": score_wall},
    }


def write_deliverables(script: Path, record: dict[str, Any], started: float) -> None:
    output_paths = {
        "primary": script.parent / "primary-record.json",
        "results": script.parent / "results.md",
        "log": script.parent / "execution-log.md",
    }
    existing = [str(path) for path in output_paths.values() if path.exists()]
    if existing:
        raise FileExistsError(
            "refusing to overwrite existing deliverables: " + ", ".join(existing)
        )

    primary_record = {
        key: value for key, value in record.items() if key != "_execution"
    }
    primary_text = json.dumps(
        primary_record, ensure_ascii=False, indent=2, sort_keys=True
    ) + "\n"
    results_text = render_results(record)
    with output_paths["primary"].open("x", encoding="utf-8") as stream:
        stream.write(primary_text)
    with output_paths["results"].open("x", encoding="utf-8") as stream:
        stream.write(results_text)

    wall = time.perf_counter() - started
    command = (
        "PYTHONDONTWRITEBYTECODE=1 "
        + shlex.join([sys.executable, str(script)])
    )
    log_text = f"""# Execution log

## Command

```bash
{command}
```

## Wall time

- Total deterministic recomputation and deliverable write: `{wall:.6f}` seconds
- Registered 10,000-draw scoring/bootstrap phase:
  `{record['_execution']['bootstrap_scoring_wall_seconds']:.6f}` seconds

The command completed successfully. It made no model calls, performed no
re-annotation, and used exclusive-create writes so no existing deliverable
could be overwritten.
"""
    with output_paths["log"].open("x", encoding="utf-8") as stream:
        stream.write(log_text)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Recompute and print the comparison without creating deliverables.",
    )
    args = parser.parse_args()
    started = time.perf_counter()
    script = Path(__file__).resolve()
    record = compute(script)
    if args.dry_run:
        print(
            json.dumps(
                {
                    "all_match_at_paper_precision": record[
                        "all_match_at_paper_precision"
                    ],
                    "quantities": {
                        name: {
                            "paper": item["paper_currently_displayed"],
                            "recomputed": item["recomputed_at_paper_precision"],
                        }
                        for name, item in record["quantities"].items()
                    },
                },
                indent=2,
                sort_keys=True,
            )
        )
        return
    write_deliverables(script, record, started)
    print(
        json.dumps(
            {
                "status": "complete",
                "all_match_at_paper_precision": record[
                    "all_match_at_paper_precision"
                ],
                "deliverables": [
                    str(script),
                    str(script.parent / "primary-record.json"),
                    str(script.parent / "results.md"),
                    str(script.parent / "execution-log.md"),
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
