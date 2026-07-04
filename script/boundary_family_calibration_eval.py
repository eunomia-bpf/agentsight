#!/usr/bin/env python3
"""Evaluate adjacent-boundary backends across existing labeled operation families."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
DEFAULT_OUT_DIR = OUT_ROOT / "boundary-family-calibration-r299"
DEFAULT_FEATURE_FIELDS = [
    "action",
    "phase",
    "target",
    "repeat_state",
    "repeat_signal",
    "app",
    "environment",
    "status",
    "tool",
    "op",
]
LEAKAGE_FIELDS = {
    "human_group",
    "group_index",
    "group_position",
    "group_size",
    "group_pattern",
    "group_alignment",
    "step_correct",
    "step_redundant",
    "looping",
    "side_effect",
    "optimality",
    "safety",
    "attack_type",
    "learned_boundary_model",
    "learned_boundary_prev",
    "learned_boundary_split",
    "learned_segment_pattern",
    "learned_segment_position",
    "learned_segment_size",
    "oracle_boundary_field",
}
LEAKAGE_PREFIXES = ("learned_",)


CANDIDATES = [
    {
        "id": "osworld_human_group",
        "dataset": "osworld-human",
        "operation_file": OUT_ROOT
        / "external-agent-trace-osworldhuman-r290"
        / "osworld-human-operations.jsonl",
        "oracle_field": "human_group",
        "sequence_field": "session",
        "turn_field": "turn",
        "require_field": "group_alignment=exact",
        "train": True,
        "claim_role": "reference human grouped-action boundary",
    },
    {
        "id": "agentnet_step_correct",
        "dataset": "agentnet",
        "operation_file": OUT_ROOT / "external-agent-trace-agentnet-r291" / "agentnet-operations.jsonl",
        "oracle_field": "step_correct",
        "sequence_field": "session",
        "turn_field": "turn",
        "exclude_oracle_values": ["unknown"],
        "train": True,
        "claim_role": "desktop step-quality state boundary",
    },
    {
        "id": "agentnet_step_redundant",
        "dataset": "agentnet",
        "operation_file": OUT_ROOT / "external-agent-trace-agentnet-r291" / "agentnet-operations.jsonl",
        "oracle_field": "step_redundant",
        "sequence_field": "session",
        "turn_field": "turn",
        "exclude_oracle_values": ["unknown"],
        "train": True,
        "claim_role": "desktop redundancy state boundary",
    },
    {
        "id": "agentreward_looping",
        "dataset": "agentrewardbench",
        "operation_file": OUT_ROOT
        / "external-agent-trace-agentreward-r288"
        / "agentreward-operations.jsonl",
        "oracle_field": "looping",
        "sequence_field": "session",
        "turn_field": "turn",
        "train": True,
        "claim_role": "expert looping state boundary",
    },
    {
        "id": "satraj_safety",
        "dataset": "satraj-os",
        "operation_file": OUT_ROOT / "external-agent-trace-satraj-r289" / "satraj-operations.jsonl",
        "oracle_field": "safety",
        "sequence_field": "session",
        "turn_field": "turn",
        "train": False,
        "claim_role": "safety label is per trajectory, not an adjacent boundary in the sample",
    },
    {
        "id": "scalecua_history_state",
        "dataset": "scalecua",
        "operation_file": OUT_ROOT
        / "external-agent-trace-scalecua-r292"
        / "scalecua-operations.jsonl",
        "oracle_field": "history_state",
        "sequence_field": "session",
        "turn_field": "turn",
        "train": False,
        "claim_role": "previous-context marker, not a semantic boundary oracle",
    },
    {
        "id": "taubench_tool_dialogue",
        "dataset": "tau-bench",
        "operation_file": OUT_ROOT / "external-agent-trace-taubench-r287" / "tau-operations.jsonl",
        "oracle_field": "role",
        "sequence_field": "session",
        "turn_field": "turn",
        "train": False,
        "claim_role": "skipped because R287 did not track operation JSONL",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--split-seed", default="r299")
    parser.add_argument("--train-percent", type=int, default=70)
    parser.add_argument("--min-positive-pairs", type=int, default=100)
    parser.add_argument("--min-train-positive-pairs", type=int, default=50)
    parser.add_argument("--min-test-positive-pairs", type=int, default=20)
    parser.add_argument("--feature-field", action="append", default=[])
    return parser.parse_args()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def normalize_fields(fields: dict[str, Any]) -> dict[str, str]:
    out = {}
    for key, value in fields.items():
        if isinstance(value, list):
            if not value:
                continue
            value = value[0]
        if isinstance(value, (dict, list)):
            text = json.dumps(value, sort_keys=True, ensure_ascii=True)
        else:
            text = str(value)
        if text:
            out[str(key)] = text
    return out


def load_operations(path: Path) -> list[dict[str, Any]]:
    operations = []
    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            operations.append(
                {
                    "fields": normalize_fields(row.get("fields") or {}),
                    "value": int(row.get("value") or 1),
                    "_line": line_number,
                    "_ordinal": len(operations),
                }
            )
    return operations


def parse_requirement(raw: str | None) -> tuple[str, str] | None:
    if not raw:
        return None
    field, sep, value = raw.partition("=")
    if not sep or not field:
        raise SystemExit(f"invalid requirement {raw!r}")
    return field, value


def keep_operation(
    operation: dict[str, Any],
    oracle_field: str,
    requirement: tuple[str, str] | None,
    excluded_values: set[str],
) -> bool:
    fields = operation["fields"]
    value = fields.get(oracle_field)
    if not value or value in excluded_values:
        return False
    if requirement is None:
        return True
    field, required = requirement
    return fields.get(field) == required


def group_sequences(
    operations: list[dict[str, Any]],
    candidate: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    requirement = parse_requirement(candidate.get("require_field"))
    excluded = set(candidate.get("exclude_oracle_values", []))
    for operation in operations:
        if not keep_operation(operation, candidate["oracle_field"], requirement, excluded):
            continue
        sequence = operation["fields"].get(candidate["sequence_field"])
        if sequence:
            groups[sequence].append(operation)
    for rows in groups.values():
        rows.sort(key=lambda operation: turn_key(operation, candidate["turn_field"]))
    return {key: rows for key, rows in groups.items() if len(rows) >= 2}


def turn_key(operation: dict[str, Any], field: str) -> tuple[int, str, int]:
    value = operation["fields"].get(field, "")
    try:
        return int(value), value, operation["_ordinal"]
    except ValueError:
        return 0, value, operation["_ordinal"]


def split_sequences(sequence_ids: list[str], seed: str, train_percent: int) -> tuple[list[str], list[str]]:
    train = []
    test = []
    for sequence_id in sorted(sequence_ids):
        digest = hashlib.sha256(f"{seed}:{sequence_id}".encode()).hexdigest()
        if int(digest, 16) % 100 < train_percent:
            train.append(sequence_id)
        else:
            test.append(sequence_id)
    return train, test


def count_positive(examples: list[dict[str, Any]]) -> int:
    return sum(bool(example["label"]) for example in examples)


def choose_positive_split(
    groups: dict[str, list[dict[str, Any]]],
    candidate: dict[str, Any],
    feature_fields: list[str],
    split_seed: str,
    train_percent: int,
    min_train_positive: int,
    min_test_positive: int,
) -> dict[str, Any] | None:
    seeds = [split_seed] + [f"{split_seed}-{index}" for index in range(1, 50)]
    for seed in seeds:
        train_sequences, test_sequences = split_sequences(list(groups), seed, train_percent)
        if not train_sequences or not test_sequences:
            continue
        train_examples = build_examples(
            groups,
            train_sequences,
            candidate["oracle_field"],
            feature_fields,
            candidate["turn_field"],
        )
        test_examples = build_examples(
            groups,
            test_sequences,
            candidate["oracle_field"],
            feature_fields,
            candidate["turn_field"],
        )
        train_positive = count_positive(train_examples)
        test_positive = count_positive(test_examples)
        if train_positive >= min_train_positive and test_positive >= min_test_positive:
            return {
                "seed": seed,
                "train_sequences": train_sequences,
                "test_sequences": test_sequences,
                "train_examples": train_examples,
                "test_examples": test_examples,
                "train_positive": train_positive,
                "test_positive": test_positive,
            }
    return None


def is_leakage_field(field: str) -> bool:
    return field in LEAKAGE_FIELDS or field.startswith(LEAKAGE_PREFIXES)


def adjacent_features(
    previous: dict[str, str],
    current: dict[str, str],
    feature_fields: list[str],
    turn_field: str,
) -> set[str]:
    features = set()
    for field in feature_fields:
        if is_leakage_field(field):
            continue
        previous_value = previous.get(field, "missing")
        current_value = current.get(field, "missing")
        features.add(f"prev:{field}={previous_value}")
        features.add(f"curr:{field}={current_value}")
        features.add(f"pair:{field}={previous_value}->{current_value}")
        features.add(f"change:{field}={previous_value != current_value}")
    try:
        step_delta = int(current.get(turn_field, "0")) - int(previous.get(turn_field, "0"))
        features.add(f"step_delta={step_delta}")
    except ValueError:
        pass
    return features


def build_examples(
    groups: dict[str, list[dict[str, Any]]],
    sequence_ids: list[str],
    oracle_field: str,
    feature_fields: list[str],
    turn_field: str,
) -> list[dict[str, Any]]:
    examples = []
    for sequence_id in sequence_ids:
        rows = groups[sequence_id]
        for previous, current in zip(rows, rows[1:]):
            examples.append(
                {
                    "sequence": sequence_id,
                    "label": previous["fields"][oracle_field] != current["fields"][oracle_field],
                    "features": adjacent_features(
                        previous["fields"], current["fields"], feature_fields, turn_field
                    ),
                    "previous": previous,
                    "current": current,
                }
            )
    return examples


class BernoulliBoundaryModel:
    def __init__(self) -> None:
        self.class_counts: Counter[bool] = Counter()
        self.feature_counts: dict[bool, Counter[str]] = {False: Counter(), True: Counter()}
        self.vocab: set[str] = set()
        self.threshold = 0.0

    def fit(self, examples: list[dict[str, Any]]) -> None:
        for example in examples:
            label = bool(example["label"])
            features = example["features"]
            self.class_counts[label] += 1
            self.feature_counts[label].update(features)
            self.vocab.update(features)
        if not self.vocab:
            raise SystemExit("training examples produced no features")
        self.threshold = select_threshold(
            [(self.score(example["features"]), bool(example["label"])) for example in examples]
        )

    def score(self, features: set[str]) -> float:
        total = self.class_counts[False] + self.class_counts[True]
        scores = {}
        for label in [False, True]:
            log_score = math.log((self.class_counts[label] + 1) / (total + 2))
            denom = self.class_counts[label] + 2
            for feature in self.vocab:
                probability = (self.feature_counts[label][feature] + 1) / denom
                log_score += math.log(probability if feature in features else 1 - probability)
            scores[label] = log_score
        return scores[True] - scores[False]

    def predict(self, features: set[str]) -> bool:
        return self.score(features) >= self.threshold

    def probability(self, features: set[str]) -> float:
        score = max(min(self.score(features), 40.0), -40.0)
        return 1.0 / (1.0 + math.exp(-score))


def select_threshold(scored_labels: list[tuple[float, bool]]) -> float:
    thresholds = sorted({score for score, _ in scored_labels})
    best = None
    for threshold in thresholds:
        metrics = binary_metrics([score >= threshold for score, _ in scored_labels], [label for _, label in scored_labels])
        key = (metrics["f1"], metrics["precision"], metrics["recall"])
        if best is None or key > best[0]:
            best = (key, threshold)
    assert best is not None
    return best[1]


def binary_metrics(predicted: list[bool], labels: list[bool]) -> dict[str, Any]:
    tp = sum(pred and label for pred, label in zip(predicted, labels))
    fp = sum(pred and not label for pred, label in zip(predicted, labels))
    fn = sum((not pred) and label for pred, label in zip(predicted, labels))
    tn = sum((not pred) and not label for pred, label in zip(predicted, labels))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    accuracy = (tp + tn) / len(labels) if labels else 0.0
    return {
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "true_negative": tn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "accuracy": round(accuracy, 4),
    }


def evaluate_model(model: BernoulliBoundaryModel, examples: list[dict[str, Any]]) -> dict[str, Any]:
    labels = [bool(example["label"]) for example in examples]
    predictions = [model.predict(example["features"]) for example in examples]
    probabilities = [model.probability(example["features"]) for example in examples]
    return {
        **binary_metrics(predictions, labels),
        "brier": round(sum((prob - float(label)) ** 2 for prob, label in zip(probabilities, labels)) / len(labels), 4)
        if labels
        else 0.0,
        "ece": calibration(probabilities, labels)["ece"],
        "calibration_bins": calibration(probabilities, labels)["bins"],
    }


def calibration(probabilities: list[float], labels: list[bool], bins: int = 5) -> dict[str, Any]:
    bucket_rows = []
    ece = 0.0
    total = len(labels)
    for bucket in range(bins):
        low = bucket / bins
        high = (bucket + 1) / bins
        indexes = [
            index
            for index, probability in enumerate(probabilities)
            if (low <= probability < high) or (bucket == bins - 1 and probability == 1.0)
        ]
        if not indexes:
            bucket_rows.append({"bin": f"{low:.1f}-{high:.1f}", "count": 0})
            continue
        avg_pred = sum(probabilities[index] for index in indexes) / len(indexes)
        observed = sum(float(labels[index]) for index in indexes) / len(indexes)
        ece += len(indexes) / total * abs(avg_pred - observed)
        bucket_rows.append(
            {
                "bin": f"{low:.1f}-{high:.1f}",
                "count": len(indexes),
                "avg_pred": round(avg_pred, 4),
                "observed": round(observed, 4),
            }
        )
    return {"ece": round(ece, 4), "bins": bucket_rows}


def evaluate_baselines(examples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    labels = [bool(example["label"]) for example in examples]
    baseline_specs = [
        ("always_boundary", [True for _ in examples]),
        ("never_boundary", [False for _ in examples]),
        ("phase_change", [field_changed(example, "phase") for example in examples]),
        ("action_change", [field_changed(example, "action") for example in examples]),
        ("target_change", [field_changed(example, "target") for example in examples]),
        ("repeat_signal_change", [field_changed(example, "repeat_signal") for example in examples]),
        ("status_change", [field_changed(example, "status") for example in examples]),
    ]
    return [{"name": name, **binary_metrics(predictions, labels)} for name, predictions in baseline_specs]


def field_changed(example: dict[str, Any], field: str) -> bool:
    previous = example["previous"]["fields"].get(field)
    current = example["current"]["fields"].get(field)
    return bool(previous and current and previous != current)


def summarize_suitability(candidate: dict[str, Any], groups: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    oracle = candidate["oracle_field"]
    present = sum(len(rows) for rows in groups.values())
    pairs = 0
    changes = 0
    values = Counter()
    for rows in groups.values():
        for row in rows:
            values[row["fields"][oracle]] += 1
        for previous, current in zip(rows, rows[1:]):
            pairs += 1
            if previous["fields"][oracle] != current["fields"][oracle]:
                changes += 1
    if not candidate.get("train", False):
        reason = candidate["claim_role"]
    elif changes < 100:
        reason = "too few positive adjacent boundaries for a supervised split"
    else:
        reason = "eligible"
    return {
        "candidate": candidate["id"],
        "dataset": candidate["dataset"],
        "oracle_field": oracle,
        "claim_role": candidate["claim_role"],
        "operations": present,
        "sequences": len(groups),
        "adjacent_pairs": pairs,
        "positive_boundaries": changes,
        "positive_rate": round(changes / pairs, 4) if pairs else 0.0,
        "oracle_values": [{"value": value, "weight": weight} for value, weight in values.most_common()],
        "eligible": candidate.get("train", False) and changes >= 100,
        "suitability_reason": reason,
    }


def augment_test_operations(
    candidate: dict[str, Any],
    groups: dict[str, list[dict[str, Any]]],
    test_sequences: list[str],
    model: BernoulliBoundaryModel,
    feature_fields: list[str],
) -> list[dict[str, Any]]:
    augmented = []
    for sequence_id in test_sequences:
        rows = groups[sequence_id]
        group_ids = [0]
        predictions = [None]
        current_group = 0
        for previous, current in zip(rows, rows[1:]):
            predicted = model.predict(
                adjacent_features(
                    previous["fields"],
                    current["fields"],
                    feature_fields,
                    candidate["turn_field"],
                )
            )
            if predicted:
                current_group += 1
            group_ids.append(current_group)
            predictions.append(predicted)
        group_sizes = Counter(group_ids)
        group_patterns = {}
        for group_id in sorted(group_sizes):
            segment = [row for row, row_group_id in zip(rows, group_ids) if row_group_id == group_id]
            group_patterns[group_id] = summarize_group_pattern(segment)
        seen = Counter()
        for index, (operation, group_id) in enumerate(zip(rows, group_ids)):
            seen[group_id] += 1
            size = group_sizes[group_id]
            if size == 1:
                position = "single"
            elif seen[group_id] == 1:
                position = "start"
            elif seen[group_id] == size:
                position = "end"
            else:
                position = "middle"
            fields = dict(operation["fields"])
            fields["boundary_family_task"] = candidate["id"]
            fields["oracle_boundary_field"] = candidate["oracle_field"]
            fields["learned_boundary_model"] = "bernoulli-adjacent-heldout-r299"
            fields["learned_boundary_split"] = "test"
            fields["learned_segment"] = f"{candidate['id']}-seg-{group_id:03d}"
            fields["learned_segment_pattern"] = group_patterns[group_id]
            fields["learned_segment_size"] = str(size)
            fields["learned_segment_position"] = position
            if predictions[index] is None:
                fields["learned_boundary_prev"] = "start"
            else:
                fields["learned_boundary_prev"] = "boundary" if predictions[index] else "continue"
            augmented.append({"fields": fields, "value": operation["value"]})
    return augmented


def summarize_group_pattern(rows: list[dict[str, Any]]) -> str:
    categories = [action_category(row["fields"].get("action", "")) for row in rows]
    compact = []
    for category in categories:
        if not compact or compact[-1] != category:
            compact.append(category)
    if not compact:
        return "unknown"
    if len(compact) == 1:
        return compact[0]
    return "-and-".join(compact[:8])


def action_category(action: str) -> str:
    action = action.lower()
    if action in {"click", "left_click", "double_click", "triple_click", "right_click"}:
        return "select"
    if action in {"type", "fill", "press", "hotkey", "key", "key_down", "key_up"}:
        return "input"
    if action in {"scroll", "wheel"}:
        return "scroll"
    if action in {"drag", "move_to", "hover"}:
        return "move"
    if action in {"wait", "sleep", "observe"}:
        return "wait"
    if action in {"terminate", "send_msg_to_user"}:
        return "finish"
    if not action:
        return "unknown"
    return action.replace("_", "-")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, sort_keys=True) + "\n")


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# R299 Boundary-Family Calibration",
        "",
        "This run tests whether the R297 adjacent-boundary backend pattern remains useful beyond OSWorld-Human. It uses existing tracked operation JSONL only; no new dataset is synced.",
        "",
        "## Results",
        "",
        "| Candidate | Oracle | Test pairs | F1 | Precision | Recall | ECE | Best baseline | Best baseline F1 |",
        "|---|---|---:|---:|---:|---:|---:|---|---:|",
    ]
    for result in report["trained_results"]:
        best_baseline = max(result["test_metrics"]["baselines"], key=lambda row: row["f1"])
        learned = result["test_metrics"]["learned_boundary_backend"]
        lines.append(
            "| {candidate} | {oracle} | {pairs} | {f1} | {precision} | {recall} | {ece} | {baseline_name} | {baseline} |".format(
                candidate=result["candidate"],
                oracle=result["oracle_field"],
                pairs=result["test_pairs"],
                f1=learned["f1"],
                precision=learned["precision"],
                recall=learned["recall"],
                ece=learned["ece"],
                baseline_name=best_baseline["name"],
                baseline=best_baseline["f1"],
            )
        )
    lines.extend(
        [
            "",
            "## Suitability",
            "",
            "| Candidate | Adjacent pairs | Positive rate | Eligible | Reason |",
            "|---|---:|---:|---|---|",
        ]
    )
    for row in report["suitability"]:
        lines.append(
            f"| {row['candidate']} | {row['adjacent_pairs']} | {row['positive_rate']} | {row['eligible']} | {row['suitability_reason']} |"
        )
    lines.append("")
    return "\n".join(lines)


def html_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    out = ["<table><tr>"]
    out.extend(f"<th>{html.escape(col)}</th>" for col in columns)
    out.append("</tr>")
    for row in rows:
        out.append("<tr>")
        for col in columns:
            out.append(f"<td>{html.escape(str(row.get(col, '')))}</td>")
        out.append("</tr>")
    out.append("</table>")
    return "\n".join(out)


def render_html(report: dict[str, Any]) -> str:
    result_rows = []
    for result in report["trained_results"]:
        learned = result["test_metrics"]["learned_boundary_backend"]
        best_baseline = max(result["test_metrics"]["baselines"], key=lambda row: row["f1"])
        result_rows.append(
            {
                "candidate": result["candidate"],
                "oracle": result["oracle_field"],
                "test_pairs": result["test_pairs"],
                "f1": learned["f1"],
                "precision": learned["precision"],
                "recall": learned["recall"],
                "ece": learned["ece"],
                "best_baseline": best_baseline["name"],
                "best_baseline_f1": best_baseline["f1"],
            }
        )
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>R299 Boundary-Family Calibration</title>
<style>
body{{font-family:system-ui,-apple-system,Segoe UI,sans-serif;margin:28px;background:#fafafa;color:#171717}}
h1{{font-size:24px;margin-bottom:6px}}
h2{{font-size:17px;margin-top:24px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:16px 0}}
.card{{background:#fff;border:1px solid #ddd;border-radius:6px;padding:12px}}
.value{{font-size:24px;font-weight:700}}
table{{border-collapse:collapse;width:100%;background:#fff;border:1px solid #ddd}}
th,td{{padding:7px 9px;border-bottom:1px solid #eee;text-align:left;vertical-align:top;font-size:13px}}
th{{background:#f0f3f8}}
</style>
</head>
<body>
<h1>R299 Boundary-Family Calibration</h1>
<p>Existing tracked operation JSONL only; boundary backends derive operation fields and Rust folds them as operation stacks.</p>
<div class="cards">
<div class="card"><div>Trained candidates</div><div class="value">{len(report['trained_results'])}</div></div>
<div class="card"><div>Suitability candidates</div><div class="value">{len(report['suitability'])}</div></div>
<div class="card"><div>Augmented operations</div><div class="value">{report['augmented_operations']}</div></div>
</div>
<h2>Test Results</h2>
{html_table(result_rows, ['candidate', 'oracle', 'test_pairs', 'f1', 'precision', 'recall', 'ece', 'best_baseline', 'best_baseline_f1'])}
<h2>Suitability</h2>
{html_table(report['suitability'], ['candidate', 'dataset', 'oracle_field', 'adjacent_pairs', 'positive_boundaries', 'positive_rate', 'eligible', 'suitability_reason'])}
</body>
</html>
"""


def run_candidate(
    candidate: dict[str, Any],
    groups: dict[str, list[dict[str, Any]]],
    feature_fields: list[str],
    split_seed: str,
    train_percent: int,
    min_train_positive: int,
    min_test_positive: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    split = choose_positive_split(
        groups,
        candidate,
        feature_fields,
        split_seed,
        train_percent,
        min_train_positive,
        min_test_positive,
    )
    if split is None:
        raise ValueError(
            f"{candidate['id']} could not produce a deterministic split with enough positive train/test boundaries"
        )
    train_sequences = split["train_sequences"]
    test_sequences = split["test_sequences"]
    train_examples = split["train_examples"]
    test_examples = split["test_examples"]
    model = BernoulliBoundaryModel()
    model.fit(train_examples)
    augmented = augment_test_operations(candidate, groups, test_sequences, model, feature_fields)
    result = {
        "candidate": candidate["id"],
        "dataset": candidate["dataset"],
        "oracle_field": candidate["oracle_field"],
        "claim_role": candidate["claim_role"],
        "split": {
            "seed": split["seed"],
            "base_seed": split_seed,
            "train_percent": train_percent,
            "train_sequences": len(train_sequences),
            "test_sequences": len(test_sequences),
            "train_operations": sum(len(groups[sequence]) for sequence in train_sequences),
            "test_operations": sum(len(groups[sequence]) for sequence in test_sequences),
            "train_positive_pairs": split["train_positive"],
            "test_positive_pairs": split["test_positive"],
        },
        "train_pairs": len(train_examples),
        "test_pairs": len(test_examples),
        "model": {
            "kind": "bernoulli-naive-bayes-adjacent-boundary",
            "threshold": round(model.threshold, 6),
            "features": len(model.vocab),
        },
        "train_metrics": {
            "learned_boundary_backend": evaluate_model(model, train_examples),
            "baselines": evaluate_baselines(train_examples),
        },
        "test_metrics": {
            "learned_boundary_backend": evaluate_model(model, test_examples),
            "baselines": evaluate_baselines(test_examples),
        },
    }
    return result, augmented


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    feature_fields = args.feature_field or DEFAULT_FEATURE_FIELDS

    suitability = []
    trained_results = []
    split_skips = []
    augmented_rows = []
    for candidate in CANDIDATES:
        operation_path = candidate["operation_file"]
        if not operation_path.exists():
            suitability.append(
                {
                    "candidate": candidate["id"],
                    "dataset": candidate["dataset"],
                    "oracle_field": candidate["oracle_field"],
                    "claim_role": candidate["claim_role"],
                    "operations": 0,
                    "sequences": 0,
                    "adjacent_pairs": 0,
                    "positive_boundaries": 0,
                    "positive_rate": 0.0,
                    "oracle_values": [],
                    "eligible": False,
                    "suitability_reason": "operation JSONL is not tracked for this run",
                }
            )
            continue
        operations = load_operations(operation_path)
        groups = group_sequences(operations, candidate)
        summary = summarize_suitability(candidate, groups)
        suitability.append(summary)
        if summary["eligible"] and summary["positive_boundaries"] >= args.min_positive_pairs:
            try:
                result, augmented = run_candidate(
                    candidate,
                    groups,
                    feature_fields,
                    args.split_seed,
                    args.train_percent,
                    args.min_train_positive_pairs,
                    args.min_test_positive_pairs,
                )
                trained_results.append(result)
                augmented_rows.extend(augmented)
            except ValueError as error:
                split_skips.append(
                    {
                        "candidate": candidate["id"],
                        "dataset": candidate["dataset"],
                        "reason": str(error),
                    }
                )

    augmented_path = out_dir / "boundary-family-test-operations.jsonl"
    profile_spec_path = out_dir / "boundary-family-profile-spec.json"
    report_path = out_dir / "boundary-family-report.json"
    md_path = out_dir / "boundary-family-report.md"
    html_path = out_dir / "index.html"
    profile_spec = {
        "output": "boundary-family.folded",
        "format": "folded",
        "view": "operations",
        "project_name": "external-agent-traces",
        "operation_files": [augmented_path.name],
        "stack": "project,dataset,boundary_family_task,phase,learned_segment_pattern,learned_segment_position,action,status",
    }
    report = {
        "schema": "agentsight.boundary-family-calibration.v1",
        "run_id": "R299",
        "source_operation_files": sorted(
            {
                rel(candidate["operation_file"])
                for candidate in CANDIDATES
                if candidate["operation_file"].exists()
            }
        ),
        "feature_fields": feature_fields,
        "leakage_policy": {
            "excluded_fields": sorted(LEAKAGE_FIELDS),
            "excluded_prefixes": list(LEAKAGE_PREFIXES),
            "note": "Dataset oracle, quality, safety, and learned fields are excluded from model features; they may still define evaluation labels.",
        },
        "suitability": suitability,
        "split_skips": split_skips,
        "trained_results": trained_results,
        "augmented_operations": len(augmented_rows),
        "outputs": {
            "augmented_operations": rel(augmented_path),
            "profile_spec": rel(profile_spec_path),
            "json": rel(report_path),
            "markdown": rel(md_path),
            "html": rel(html_path),
        },
        "claim_scope": {
            "supported": "The same adjacent-boundary backend pattern can be evaluated on multiple existing labeled operation families and can derive stackable learned segment fields.",
            "not_supported": "One shared universal intent-boundary detector across OSWorld-Human, AgentNet, AgentRewardBench, and tool-dialogue traces.",
        },
    }

    write_jsonl(augmented_path, augmented_rows)
    write_json(profile_spec_path, profile_spec)
    write_json(report_path, report)
    md_path.write_text(markdown(report), encoding="utf-8")
    html_path.write_text(render_html(report), encoding="utf-8")
    run_result = {
        "status": "ok",
        "run_id": "R299",
        "json": rel(report_path),
        "markdown": rel(md_path),
        "html": rel(html_path),
        "augmented_operations": rel(augmented_path),
        "profile_spec": rel(profile_spec_path),
        "trained_candidates": len(trained_results),
        "suitability_candidates": len(suitability),
    }
    write_json(out_dir / "run-result.json", run_result)
    print(json.dumps(run_result, indent=2))


if __name__ == "__main__":
    main()
