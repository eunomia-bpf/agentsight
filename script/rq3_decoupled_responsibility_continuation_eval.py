#!/usr/bin/env python3
"""Evaluate decoupled responsibility continuation on CodeTraceBench.

The boundary call sees only the active semantic responsibility, never the list
of alternatives.  A separate exact-label call runs only at initialization or
after a predicted change.  Gold stages are opened only by the score command.
"""

from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import sys
import time
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "script"))

import rq3_index_free_responsibility_alignment_eval as joint  # noqa: E402


base = joint.base
ALGORITHM_VERSION = "decoupled-responsibility-continuation-v1"
SCHEMA = "agentsight.rq3-decoupled-responsibility-continuation"
EXPECTED_SESSIONS = joint.EXPECTED_SESSIONS
EXPECTED_OPERATIONS = joint.EXPECTED_OPERATIONS
EXPECTED_STAGES = joint.EXPECTED_STAGES
EXPECTED_TASKS = joint.EXPECTED_TASKS
EXPECTED_FRAMEWORKS = joint.EXPECTED_FRAMEWORKS
MAX_REQUEST_TOKENS = joint.MAX_REQUEST_TOKENS
OUTPUT_TOKENS = joint.CAUSAL_OUTPUT_TOKENS

CONTINUATION_SYSTEM = """Decide whether the current agent operation continues
the active concrete workflow responsibility. Alternative responsibilities are
intentionally hidden. A change in tool, command, file, observation, or local
action does not itself imply a responsibility change. Return continue when the
operation advances, checks, repairs, or retries the active concrete work.
Return change only when the concrete work responsibility changes. Return only
the required JSON."""

LABEL_SYSTEM = """Select the one retained task responsibility that best
describes the current operation's concrete work. The displayed choices are an
unordered semantic inventory, not a workflow sequence. Copy one allowed string
exactly and return only the required JSON."""

CONTINUATION_GRAMMAR = (
    'root ::= continue | change\n'
    'continue ::= "{\\\"decision\\\":\\\"continue\\\"}"\n'
    'change ::= "{\\\"decision\\\":\\\"change\\\"}"\n'
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    infer = subparsers.add_parser("infer")
    infer.add_argument("mode", choices=("preflight", "full"))
    infer.add_argument("--source-sessions", type=Path, required=True)
    infer.add_argument("--llama-url", required=True)
    infer.add_argument("--workers", type=int, default=4)
    infer.add_argument("--timeout-seconds", type=int, default=600)
    infer.add_argument("--out", type=Path, required=True)

    score = subparsers.add_parser("score")
    score.add_argument("--target-operations", type=Path, required=True)
    score.add_argument("--predictions", type=Path, required=True)
    score.add_argument("--joint-predictions", type=Path, required=True)
    score.add_argument("--numeric-predictions", type=Path, required=True)
    score.add_argument("--verified-manifest", type=Path, required=True)
    score.add_argument("--multires-assignments", type=Path, required=True)
    score.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def absolute(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_json_atomic(path: Path, payload: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    write_json(temporary, payload)
    temporary.replace(path)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as output:
        for row in rows:
            output.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def cache_name(session: str) -> str:
    return hashlib.sha256(session.encode()).hexdigest()[:24] + ".json"


def label_grammar(plan: list[str], active: str | None) -> str:
    require(plan and len(plan) == len(set(plan)), "plan must be unique and nonempty")
    allowed = [label for label in plan if label != active]
    require(bool(allowed), "label call requires an allowed responsibility")
    label_rule = " | ".join(
        joint.gbnf_terminal(json.dumps(label, ensure_ascii=False)) for label in allowed
    )
    return (
        'root ::= "{\\\"responsibility\\\":" label "}"\n'
        f"label ::= {label_rule}\n"
    )


def continuation_prompt(shared_evidence: str, active: str) -> str:
    return f"{shared_evidence}\n\nACTIVE RESPONSIBILITY\n{active}"


def label_prompt(
    shared_evidence: str,
    plan: list[str],
    active: str | None,
) -> str:
    choices = "\n".join(f"- {label}" for label in plan if label != active)
    return (
        f"{shared_evidence}\n\n"
        "ACTIVE RESPONSIBILITY\n"
        f"{active if active is not None else 'none'}\n\n"
        "RETAINED RESPONSIBILITIES (unordered semantic choices)\n"
        f"{choices}"
    )


def parse_continuation(raw: str) -> str:
    value = json.loads(raw)
    require(
        isinstance(value, dict) and set(value) == {"decision"},
        "unexpected continuation keys",
    )
    decision = value["decision"]
    require(decision in {"continue", "change"}, "invalid continuation decision")
    return str(decision)


def parse_label(raw: str, plan: list[str], active: str | None) -> str:
    value = json.loads(raw)
    require(
        isinstance(value, dict) and set(value) == {"responsibility"},
        "unexpected label keys",
    )
    label = value["responsibility"]
    require(isinstance(label, str), "responsibility must be text")
    require(label in plan, "responsibility is not retained exact text")
    require(label != active, "changed responsibility must differ from active")
    return label


def call_label(
    llama_url: str,
    shared_evidence: str,
    plan: list[str],
    active: str | None,
    timeout_seconds: int,
) -> dict[str, Any]:
    user = label_prompt(shared_evidence, plan, active)
    raw, response, attempts = base.call_model(
        llama_url,
        LABEL_SYSTEM,
        user,
        label_grammar(plan, active),
        timeout_seconds,
        OUTPUT_TOKENS,
    )
    usage = response.get("usage") or {}
    request_tokens = int(usage.get("prompt_tokens", 0))
    require(0 < request_tokens <= MAX_REQUEST_TOKENS, "label request token limit")
    return {
        "label": parse_label(raw, plan, active),
        "system": LABEL_SYSTEM,
        "user": user,
        "raw": raw,
        "usage": usage,
        "attempts": attempts,
        "request_tokens": request_tokens,
    }


def call_continuation(
    llama_url: str,
    shared_evidence: str,
    active: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    user = continuation_prompt(shared_evidence, active)
    raw, response, attempts = base.call_model(
        llama_url,
        CONTINUATION_SYSTEM,
        user,
        CONTINUATION_GRAMMAR,
        timeout_seconds,
        OUTPUT_TOKENS,
    )
    usage = response.get("usage") or {}
    request_tokens = int(usage.get("prompt_tokens", 0))
    require(
        0 < request_tokens <= MAX_REQUEST_TOKENS,
        "continuation request token limit",
    )
    return {
        "decision": parse_continuation(raw),
        "system": CONTINUATION_SYSTEM,
        "user": user,
        "raw": raw,
        "usage": usage,
        "attempts": attempts,
        "request_tokens": request_tokens,
    }


def validate_cached_result(result: dict[str, Any], source: dict[str, Any]) -> None:
    require(result.get("algorithm_version") == ALGORITHM_VERSION, "cache version")
    require(result.get("session") == source["session"], "cache session")
    require(result.get("model_sha256") == base.MODEL_SHA256, "cache model")
    require(
        result.get("source_cache_sha256") == source["_source_sha256"],
        "cache source",
    )


def infer_session(
    source: dict[str, Any],
    llama_url: str,
    timeout_seconds: int,
    cache_dir: Path,
) -> dict[str, Any]:
    session = str(source["session"])
    cache_path = cache_dir / cache_name(session)
    if cache_path.is_file():
        result = json.loads(cache_path.read_text(encoding="utf-8"))
        validate_cached_result(result, source)
    else:
        result = {
            "schema": SCHEMA + ".session.v1",
            "algorithm_version": ALGORITHM_VERSION,
            "session": session,
            "framework": source["framework"],
            "model": base.MODEL,
            "model_sha256": base.MODEL_SHA256,
            "seed": base.SEED,
            "source_cache": relative(Path(source["_source_path"])),
            "source_cache_sha256": source["_source_sha256"],
            "plan": list(source["plan"]),
            "transitions": [],
        }
        write_json_atomic(cache_path, result)

    plan = list(result["plan"])
    transitions = result["transitions"]
    require(
        len(transitions) <= len(source["transitions"]),
        f"{session}: excessive cached transitions",
    )
    active = str(transitions[-1]["active_responsibility"]) if transitions else None
    stage_instance = int(transitions[-1]["stage_instance"]) if transitions else -1

    for operation_number in range(len(transitions), len(source["transitions"])):
        source_transition = source["transitions"][operation_number]
        shared_evidence = str(source_transition["projection"]["shared_evidence"])
        evidence_hash = hashlib.sha256(shared_evidence.encode()).hexdigest()
        continuation_call = None
        label_call = None

        if active is None:
            label_call = call_label(
                llama_url, shared_evidence, plan, None, timeout_seconds
            )
            active = str(label_call["label"])
            stage_instance += 1
            decision = "initialize"
        elif len(plan) == 1:
            decision = "forced-continue"
        else:
            continuation_call = call_continuation(
                llama_url, shared_evidence, active, timeout_seconds
            )
            decision = str(continuation_call["decision"])
            if decision == "change":
                label_call = call_label(
                    llama_url, shared_evidence, plan, active, timeout_seconds
                )
                active = str(label_call["label"])
                stage_instance += 1

        transition = {
            "operation_number": operation_number,
            "step": int(source_transition["step"]),
            "decision": decision,
            "active_responsibility": active,
            "stage_instance": stage_instance,
            "shared_evidence_sha256": evidence_hash,
            "continuation_call": continuation_call,
            "label_call": label_call,
        }
        transitions.append(transition)
        write_json_atomic(cache_path, result)

    require(
        len(result["transitions"]) == len(source["transitions"]),
        f"{session}: incomplete transitions",
    )
    return result


def transition_calls(transition: dict[str, Any]) -> Iterable[dict[str, Any]]:
    for key in ("continuation_call", "label_call"):
        call = transition.get(key)
        if call is not None:
            yield call


def usage_totals(results: dict[str, dict[str, Any]]) -> Counter[str]:
    usage: Counter[str] = Counter()
    for result in results.values():
        for transition in result["transitions"]:
            for call in transition_calls(transition):
                for key, value in (call.get("usage") or {}).items():
                    if isinstance(value, int):
                        usage[key] += value
    return usage


def materialize_predictions(
    selected: list[str],
    sources: dict[str, dict[str, Any]],
    results: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for session in selected:
        source = sources[session]
        result = results[session]
        semantic_by_label = dict(zip(source["plan"], source["plan_semantic"]))
        for source_transition, transition in zip(
            source["transitions"], result["transitions"], strict=True
        ):
            shared_evidence = str(source_transition["projection"]["shared_evidence"])
            require(
                hashlib.sha256(shared_evidence.encode()).hexdigest()
                == transition["shared_evidence_sha256"],
                f"source evidence drift: {session}/{transition['step']}",
            )
            operation = source_transition["projection"]["operation"]
            label = str(transition["active_responsibility"])
            rows.append(
                {
                    "session": session,
                    "framework": source["framework"],
                    "step_id": int(transition["step"]),
                    "task_label": source_transition["projection"]["task"],
                    "action": operation["action_kind"],
                    "action_detail": operation["raw_action_key"],
                    "source_action": operation["source_action"],
                    "candidate_index": int(transition["stage_instance"]),
                    "candidate_stage_instance": int(transition["stage_instance"]),
                    "candidate_label": label,
                    "candidate_label_semantic": bool(semantic_by_label[label]),
                    "candidate_decision": transition["decision"],
                    "candidate_interface": ALGORITHM_VERSION,
                }
            )
    rows.sort(key=lambda row: (str(row["session"]), int(row["step_id"])))
    return rows


def count_aba(results: dict[str, dict[str, Any]]) -> int:
    total = 0
    for result in results.values():
        labels = [
            str(transition["active_responsibility"])
            for transition in result["transitions"]
        ]
        total += sum(
            labels[index - 1] == labels[index + 1]
            and labels[index] != labels[index - 1]
            for index in range(1, len(labels) - 1)
        )
    return total


def stage_return_diagnostics(
    results: dict[str, dict[str, Any]],
) -> tuple[int, int, int]:
    stage_aba = 0
    returns = 0
    first_entries = 0
    for result in results.values():
        stage_labels = []
        previous_instance = None
        for transition in result["transitions"]:
            instance = int(transition["stage_instance"])
            if instance != previous_instance:
                stage_labels.append(str(transition["active_responsibility"]))
                previous_instance = instance
        stage_aba += sum(
            stage_labels[index - 1] == stage_labels[index + 1]
            and stage_labels[index] != stage_labels[index - 1]
            for index in range(1, len(stage_labels) - 1)
        )
        seen = {stage_labels[0]}
        for label in stage_labels[1:]:
            if label in seen:
                returns += 1
            else:
                first_entries += 1
                seen.add(label)
    return stage_aba, returns, first_entries


def natural_alternative_label_mentions_in_source_evidence(
    results: dict[str, dict[str, Any]],
) -> int:
    mentions = 0
    for result in results.values():
        plan = list(result["plan"])
        previous_active = None
        for transition in result["transitions"]:
            call = transition.get("continuation_call")
            if call is not None:
                require(previous_active is not None, "continuation lacks active state")
                user = str(call["user"])
                shared_evidence, marker, _ = user.partition(
                    "\n\nACTIVE RESPONSIBILITY\n"
                )
                require(bool(marker), "continuation prompt lacks active marker")
                if any(
                    label != previous_active and label in shared_evidence
                    for label in plan
                ):
                    mentions += 1
            previous_active = str(transition["active_responsibility"])
    return mentions


def run_inference(args: argparse.Namespace) -> None:
    started = time.monotonic()
    sources = joint.load_source_sessions(args.source_sessions)
    selected = (
        joint.preflight_selection(sources)
        if args.mode == "preflight"
        else sorted(sources)
    )
    out_dir = absolute(args.out)
    prior_summary_path = out_dir / "inference-summary.json"
    prior_summary = (
        json.loads(prior_summary_path.read_text(encoding="utf-8"))
        if prior_summary_path.is_file()
        else None
    )
    cache_dir = out_dir / "sessions"
    cache_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict[str, Any]] = {}

    def infer(session: str) -> dict[str, Any]:
        return infer_session(
            sources[session], args.llama_url, args.timeout_seconds, cache_dir
        )

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(infer, session): session for session in selected}
        for future in as_completed(futures):
            session = futures[future]
            results[session] = future.result()
            print(f"inferred {len(results)}/{len(selected)} {session}", flush=True)

    predictions = materialize_predictions(selected, sources, results)
    expected_operations = sum(len(sources[session]["transitions"]) for session in selected)
    require(len(predictions) == expected_operations, "prediction coverage")
    require(
        len({(row["session"], row["step_id"]) for row in predictions})
        == expected_operations,
        "prediction uniqueness",
    )

    calls = [
        call
        for result in results.values()
        for transition in result["transitions"]
        for call in transition_calls(transition)
    ]
    changes = sum(
        transition["decision"] == "change"
        for result in results.values()
        for transition in result["transitions"]
    )
    learned_continues = sum(
        transition["decision"] == "continue"
        for result in results.values()
        for transition in result["transitions"]
    )
    forced_continues = sum(
        transition["decision"] == "forced-continue"
        for result in results.values()
        for transition in result["transitions"]
    )
    continuation_calls = sum(
        transition["continuation_call"] is not None
        for result in results.values()
        for transition in result["transitions"]
    )
    label_calls = sum(
        transition["label_call"] is not None
        for result in results.values()
        for transition in result["transitions"]
    )
    one_item_sessions = [
        session for session in selected if len(results[session]["plan"]) == 1
    ]
    used = sum(
        len(
            {
                transition["active_responsibility"]
                for transition in result["transitions"]
            }
        )
        for result in results.values()
    )
    plan_items = sum(len(result["plan"]) for result in results.values())
    stage_aba, non_adjacent_returns, first_time_changes = stage_return_diagnostics(
        results
    )
    write_jsonl(out_dir / "predictions.jsonl", predictions)
    elapsed = time.monotonic() - started
    inference_wall_seconds = (
        float(
            prior_summary.get(
                "inference_wall_seconds", prior_summary.get("wall_seconds")
            )
        )
        if prior_summary is not None
        else elapsed
    )
    summary = {
        "schema": SCHEMA + ".inference.v1",
        "algorithm_version": ALGORITHM_VERSION,
        "status": "complete",
        "mode": args.mode,
        "model": base.MODEL,
        "model_sha256": base.MODEL_SHA256,
        "seed": base.SEED,
        "sessions": len(selected),
        "operations": len(predictions),
        "selected_sessions": selected,
        "model_calls": len(calls),
        "continuation_calls": continuation_calls,
        "label_calls": label_calls,
        "changes": changes,
        "learned_continues": learned_continues,
        "forced_continues": forced_continues,
        "predicted_instances": len(selected) + changes,
        "adjacent_boundary_rate": changes
        / max(1, len(predictions) - len(selected)),
        "operation_triplet_aba_alternations": count_aba(results),
        "stage_sequence_aba_alternations": stage_aba,
        "non_adjacent_responsibility_returns": non_adjacent_returns,
        "first_time_responsibility_changes": first_time_changes,
        "one_item_sessions": len(one_item_sessions),
        "one_item_operations": sum(
            len(results[session]["transitions"]) for session in one_item_sessions
        ),
        "responsibility_types_used": used,
        "responsibility_types_available": plan_items,
        "request_token_min": min(int(call["request_tokens"]) for call in calls),
        "request_token_max": max(int(call["request_tokens"]) for call in calls),
        "model_usage": dict(usage_totals(results)),
        "wall_seconds": inference_wall_seconds,
        "inference_wall_seconds": inference_wall_seconds,
        "summary_regeneration_wall_seconds": (
            elapsed if prior_summary is not None else 0.0
        ),
        "predictions": relative(out_dir / "predictions.jsonl"),
        "isolation": {
            "official_manifest_opened": False,
            "official_stages_opened": False,
            "reused_source_evidence_byte_hash_checked": True,
            "alternative_label_inventory_injected": False,
            "continuation_calls_with_injected_alternative_inventory": sum(
                "RETAINED RESPONSIBILITIES" in str(call["user"])
                for result in results.values()
                for transition in result["transitions"]
                for call in [transition.get("continuation_call")]
                if call is not None
            ),
            "continuation_calls_with_natural_alternative_label_mention_in_source_evidence": (
                natural_alternative_label_mentions_in_source_evidence(results)
            ),
            "model_saw_numeric_plan_index": False,
            "model_emitted_numeric_plan_index": False,
            "all_operations_retained": True,
        },
    }
    if args.mode == "full":
        require(summary["sessions"] == EXPECTED_SESSIONS, "full session count")
        require(summary["operations"] == EXPECTED_OPERATIONS, "full operation count")
    write_json(out_dir / "inference-summary.json", summary)
    print(json.dumps(summary, sort_keys=True), flush=True)


def add_external_instances(
    operations: list[dict[str, Any]],
    pairs: list[dict[str, Any]],
    predictions: dict[tuple[str, int], dict[str, Any]],
    output_key: str,
    prediction_key: str,
) -> None:
    values: dict[tuple[str, int], str] = {}
    for operation in operations:
        session = str(operation["session"])
        step = int(operation["step_id"])
        value = str(predictions[(session, step)][prediction_key])
        cluster = f"{session}:{output_key}-{value}"
        operation[output_key] = cluster
        values[(session, step)] = cluster
    for pair in pairs:
        session = str(pair["session"])
        left = int(pair["position"])
        right = left + 1
        pair[output_key] = values[(session, left)] != values[(session, right)]


def score_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Decoupled Responsibility Continuation — Complete Result",
        "",
        f"- status: {summary['status']}",
        f"- registered interpretation: **{summary['registered_interpretation']}**",
        "- evidence status: post-hoc flat-stage mechanism development",
        "",
        "## Standard Metrics",
        "",
        "| Method | Span P | Span R | Span F1 | B³ F1 | Boundary F1 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for method, metric in summary["metrics"].items():
        lines.append(
            f"| {method} | {metric['span']['precision']:.6f} | "
            f"{metric['span']['recall']:.6f} | {metric['span']['f1']:.6f} | "
            f"{metric['bcubed']['f1']:.6f} | {metric['boundary']['f1']:.6f} |"
        )
    lines.extend(["", "## Paired Task-Cluster Bootstrap", ""])
    for name, result in summary["bootstrap"].items():
        lines.append(
            f"- candidate minus {name}: mean {result['mean_delta']:.6f}, "
            f"95% CI [{result['ci95'][0]:.6f}, {result['ci95'][1]:.6f}], "
            f"positive fraction {result['positive_fraction']:.4f}"
        )
    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "Adoption is decided only against both recurrence comparators. "
            "The joint-interface comparison diagnoses the complete current-"
            "operation factorization change, not causal independence of label "
            "selection. The score covers one flat unlabeled workflow-stage "
            "level, not the full task-semantic hierarchy.",
        ]
    )
    return "\n".join(lines) + "\n"


def run_scoring(args: argparse.Namespace) -> None:
    target_path = absolute(args.target_operations)
    prediction_input = absolute(args.predictions)
    joint_path = absolute(args.joint_predictions)
    numeric_path = absolute(args.numeric_predictions)
    manifest_path = absolute(args.verified_manifest)
    baseline_path = absolute(args.multires_assignments)
    out_dir = absolute(args.out)
    inference_summary_path = prediction_input / "inference-summary.json"
    prediction_path = prediction_input / "predictions.jsonl"
    for path in (
        target_path,
        inference_summary_path,
        prediction_path,
        joint_path,
        numeric_path,
        manifest_path,
        baseline_path,
    ):
        require(path.is_file(), f"missing score input: {path}")

    inference_summary = json.loads(inference_summary_path.read_text(encoding="utf-8"))
    require(inference_summary.get("status") == "complete", "inference incomplete")
    require(inference_summary.get("mode") == "full", "score requires full inference")
    require(inference_summary.get("sessions") == EXPECTED_SESSIONS, "session count")
    require(inference_summary.get("operations") == EXPECTED_OPERATIONS, "operation count")

    grouped = base.load_visible_operations(target_path)
    selected = sorted(grouped)
    require(len(grouped) == EXPECTED_SESSIONS, "target session count")
    require(sum(map(len, grouped.values())) == EXPECTED_OPERATIONS, "target operation count")
    candidate = base.load_prediction_rows(prediction_path)
    joint_predictions = base.load_prediction_rows(joint_path)
    numeric = base.load_prediction_rows(numeric_path)
    expected = {
        (session, int(row["step_id"]))
        for session, rows in grouped.items()
        for row in rows
    }
    for name, rows in (
        ("candidate", candidate),
        ("joint", joint_predictions),
        ("numeric", numeric),
    ):
        require(set(rows) == expected, f"{name} prediction coverage")
    score_predictions = {
        key: {**row, "flat_index": int(joint_predictions[key]["flat_index"])}
        for key, row in candidate.items()
    }
    baselines = base.load_baselines(baseline_path)
    require(expected <= set(baselines), "recurrence baseline coverage")

    official, frameworks, tasks = base.load_stages_after_prediction(
        manifest_path, grouped, selected
    )
    pairs, operations = base.score_rows(
        grouped, score_predictions, baselines, official, frameworks, tasks
    )
    add_external_instances(
        operations,
        pairs,
        joint_predictions,
        "joint_candidate",
        "candidate_stage_instance",
    )
    joint.add_numeric_candidate(operations, pairs, numeric)
    require(len(operations) == EXPECTED_OPERATIONS, "scored operation count")
    require(len(pairs) == EXPECTED_OPERATIONS - EXPECTED_SESSIONS, "pair count")
    require(len(set(official.values())) == EXPECTED_STAGES, "official stage count")
    require(len(set(tasks.values())) == EXPECTED_TASKS, "task count")
    require(set(frameworks.values()) == EXPECTED_FRAMEWORKS, "framework set")

    methods = (
        "candidate",
        "joint_candidate",
        "numeric_candidate",
        "current_recurrence",
        "multires_recurrence",
        "plan_free_qwen",
        "phase",
        "raw_action",
        "action",
        "one_span",
    )
    metrics = {
        method: {
            "span": base.span_metrics(operations, method),
            "bcubed": base.bcubed(operations, method),
            "boundary": base.boundary_metrics(pairs, method),
        }
        for method in methods
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    comparison_names = (
        "current_recurrence",
        "multires_recurrence",
        "joint_candidate",
    )
    bootstrap = {
        name: base.task_cluster_bootstrap(
            operations,
            "candidate",
            name,
            out_dir / f"bootstrap-candidate-minus-{name}.jsonl",
        )
        for name in comparison_names
    }
    main = ("current_recurrence", "multires_recurrence")
    candidate_f1 = metrics["candidate"]["span"]["f1"]
    higher = all(candidate_f1 > metrics[name]["span"]["f1"] for name in main)
    positive = all(bootstrap[name]["ci95"][0] > 0 for name in main)
    contradicted = any(bootstrap[name]["ci95"][1] <= 0 for name in main)
    interpretation = (
        "supported-and-adopted"
        if higher and positive
        else "contradicted-not-adopted"
        if contradicted
        else "inconclusive-not-adopted"
    )

    per_framework = {}
    for framework in sorted(EXPECTED_FRAMEWORKS):
        operation_slice = [row for row in operations if row["framework"] == framework]
        pair_slice = [row for row in pairs if row["framework"] == framework]
        per_framework[framework] = {
            method: {
                "span": base.span_metrics(operation_slice, method),
                "bcubed": base.bcubed(operation_slice, method),
                "boundary": base.boundary_metrics(pair_slice, method),
            }
            for method in ("candidate", *main, "joint_candidate")
        }

    summary = {
        "schema": SCHEMA + ".score.v1",
        "status": "complete",
        "registered_interpretation": interpretation,
        "population": {
            "sessions": len(selected),
            "operations": len(operations),
            "pairs": len(pairs),
            "official_stages": len(set(official.values())),
            "tasks": len(set(tasks.values())),
            "frameworks": dict(Counter(frameworks.values())),
        },
        "metrics": metrics,
        "bootstrap": bootstrap,
        "per_framework": per_framework,
        "decision": {
            "main_adoption_comparators": list(main),
            "candidate_point_higher_than_both": higher,
            "candidate_intervals_positive_against_both": positive,
            "candidate_any_interval_wholly_nonpositive": contradicted,
            "joint_predecessor_role": "paired complete-interface diagnostic only",
        },
        "claim_boundary": (
            "post-hoc flat human workflow-stage span fidelity only; later-state "
            "label coupling and the deeper task-semantic hierarchy remain"
        ),
    }
    write_jsonl(out_dir / "operation-score-rows.jsonl", operations)
    write_jsonl(out_dir / "boundary-score-rows.jsonl", pairs)
    write_json(out_dir / "summary.json", summary)
    (out_dir / "report.md").write_text(score_report(summary), encoding="utf-8")
    print(json.dumps(summary, sort_keys=True), flush=True)


def main() -> None:
    args = parse_args()
    if args.command == "infer":
        run_inference(args)
    else:
        run_scoring(args)


if __name__ == "__main__":
    main()
