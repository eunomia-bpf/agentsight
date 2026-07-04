#!/usr/bin/env python3
"""Evaluate a learned operation-boundary backend on labeled operation sequences."""

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
DEFAULT_OPERATION_FILE = (
    ROOT
    / "docs"
    / "visexp"
    / "out"
    / "external-agent-trace-osworldhuman-r290"
    / "osworld-human-operations.jsonl"
)
DEFAULT_OUT_DIR = ROOT / "docs" / "visexp" / "out" / "operation-boundary-backend-r297"
LEAKAGE_FIELDS = {
    "human_group",
    "group_index",
    "group_position",
    "group_size",
    "group_pattern",
    "group_alignment",
    "learned_group",
    "learned_group_pattern",
    "learned_group_position",
    "learned_group_size",
    "learned_boundary_prev",
    "learned_boundary_model",
    "learned_boundary_split",
    "oracle_boundary_field",
}
LEAKAGE_PREFIXES = ("learned_",)
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
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operation-file", type=Path, default=DEFAULT_OPERATION_FILE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--oracle-field", default="human_group")
    parser.add_argument("--sequence-field", default="session")
    parser.add_argument("--turn-field", default="turn")
    parser.add_argument("--require-field", default="group_alignment=exact")
    parser.add_argument("--split-seed", default="r297")
    parser.add_argument("--train-percent", type=int, default=70)
    parser.add_argument(
        "--feature-field",
        action="append",
        default=[],
        help="Adjacent-pair operation field to use. Defaults to desktop action fields.",
    )
    return parser.parse_args()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_operations(path: Path) -> list[dict[str, Any]]:
    operations = []
    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            fields = normalize_fields(row.get("fields") or {})
            operations.append(
                {
                    "fields": fields,
                    "value": int(row.get("value") or 1),
                    "_line": line_number,
                    "_ordinal": len(operations),
                }
            )
    return operations


def normalize_fields(fields: dict[str, Any]) -> dict[str, str]:
    normalized = {}
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
            normalized[str(key)] = text
    return normalized


def parse_requirement(raw: str) -> tuple[str, str] | None:
    if not raw:
        return None
    field, sep, value = raw.partition("=")
    if not sep or not field:
        raise SystemExit(f"invalid --require-field {raw!r}; expected FIELD=VALUE")
    return field, value


def keep_operation(operation: dict[str, Any], oracle_field: str, requirement: tuple[str, str] | None) -> bool:
    fields = operation["fields"]
    if not fields.get(oracle_field):
        return False
    if requirement is None:
        return True
    field, value = requirement
    return fields.get(field) == value


def group_sequences(
    operations: list[dict[str, Any]],
    sequence_field: str,
    oracle_field: str,
    requirement: tuple[str, str] | None,
) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for operation in operations:
        if not keep_operation(operation, oracle_field, requirement):
            continue
        sequence = operation["fields"].get(sequence_field)
        if not sequence:
            continue
        groups[sequence].append(operation)
    return {key: value for key, value in groups.items() if len(value) >= 2}


def sort_sequences(groups: dict[str, list[dict[str, Any]]], turn_field: str) -> None:
    for rows in groups.values():
        rows.sort(key=lambda operation: turn_key(operation, turn_field))


def turn_key(operation: dict[str, Any], turn_field: str) -> tuple[int, str, int]:
    value = operation["fields"].get(turn_field, "")
    try:
        return int(value), value, operation["_ordinal"]
    except ValueError:
        return 0, value, operation["_ordinal"]


def split_sequences(sequence_ids: list[str], seed: str, train_percent: int) -> tuple[list[str], list[str]]:
    train = []
    test = []
    for sequence_id in sorted(sequence_ids):
        digest = hashlib.sha256(f"{seed}:{sequence_id}".encode()).hexdigest()
        bucket = int(digest, 16) % 100
        if bucket < train_percent:
            train.append(sequence_id)
        else:
            test.append(sequence_id)
    if not train or not test:
        raise SystemExit("deterministic split produced an empty train or test set")
    return train, test


def build_examples(
    groups: dict[str, list[dict[str, Any]]],
    sequence_ids: list[str],
    feature_fields: list[str],
    oracle_field: str,
    turn_field: str,
) -> list[dict[str, Any]]:
    examples = []
    for sequence_id in sequence_ids:
        rows = groups[sequence_id]
        for previous, current in zip(rows, rows[1:]):
            label = previous["fields"][oracle_field] != current["fields"][oracle_field]
            examples.append(
                {
                    "sequence": sequence_id,
                    "features": adjacent_features(
                        previous["fields"], current["fields"], feature_fields, turn_field
                    ),
                    "label": label,
                    "previous": previous,
                    "current": current,
                }
            )
    return examples


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

    def top_features(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = []
        false_denom = self.class_counts[False] + 2
        true_denom = self.class_counts[True] + 2
        for feature in self.vocab:
            p_true = (self.feature_counts[True][feature] + 1) / true_denom
            p_false = (self.feature_counts[False][feature] + 1) / false_denom
            rows.append(
                {
                    "feature": feature,
                    "log_odds_boundary": round(math.log(p_true / p_false), 4),
                    "boundary_count": self.feature_counts[True][feature],
                    "non_boundary_count": self.feature_counts[False][feature],
                }
            )
        rows.sort(key=lambda row: (-abs(row["log_odds_boundary"]), row["feature"]))
        return rows[:limit]


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
    return binary_metrics(
        [model.predict(example["features"]) for example in examples],
        [bool(example["label"]) for example in examples],
    )


def evaluate_baselines(examples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    labels = [bool(example["label"]) for example in examples]
    baselines = []
    for name, predictions in [
        ("always_boundary", [True for _ in examples]),
        ("never_boundary", [False for _ in examples]),
        ("phase_change", [field_changed(example, "phase") for example in examples]),
        ("action_change", [field_changed(example, "action") for example in examples]),
        ("target_change", [field_changed(example, "target") for example in examples]),
        ("group_pattern_reference", [field_changed(example, "group_pattern") for example in examples]),
    ]:
        row = {"name": name, **binary_metrics(predictions, labels)}
        baselines.append(row)
    return baselines


def field_changed(example: dict[str, Any], field: str) -> bool:
    previous = example["previous"]["fields"].get(field)
    current = example["current"]["fields"].get(field)
    return bool(previous and current and previous != current)


def augment_test_operations(
    groups: dict[str, list[dict[str, Any]]],
    test_sequences: list[str],
    model: BernoulliBoundaryModel,
    feature_fields: list[str],
    oracle_field: str,
    turn_field: str,
) -> list[dict[str, Any]]:
    augmented = []
    for sequence_id in test_sequences:
        rows = groups[sequence_id]
        group_ids = [0]
        predictions = [None]
        current_group = 0
        for previous, current in zip(rows, rows[1:]):
            pred_boundary = model.predict(
                adjacent_features(previous["fields"], current["fields"], feature_fields, turn_field)
            )
            if pred_boundary:
                current_group += 1
            group_ids.append(current_group)
            predictions.append(pred_boundary)
        group_sizes = Counter(group_ids)
        group_patterns = {}
        for group_id in sorted(group_sizes):
            segment_rows = [
                row for row, row_group_id in zip(rows, group_ids) if row_group_id == group_id
            ]
            group_patterns[group_id] = summarize_group_pattern(segment_rows)
        group_positions = {}
        seen = Counter()
        for index, group_id in enumerate(group_ids):
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
            group_positions[index] = position
        for index, (operation, group_id) in enumerate(zip(rows, group_ids)):
            fields = dict(operation["fields"])
            fields["learned_boundary_model"] = "bernoulli-adjacent-heldout"
            fields["learned_boundary_split"] = "test"
            fields["learned_group"] = f"learned-{group_id:03d}"
            fields["learned_group_pattern"] = group_patterns[group_id]
            fields["learned_group_size"] = str(group_sizes[group_id])
            fields["learned_group_position"] = group_positions[index]
            if predictions[index] is None:
                fields["learned_boundary_prev"] = "start"
            else:
                fields["learned_boundary_prev"] = "boundary" if predictions[index] else "continue"
            fields["oracle_boundary_field"] = oracle_field
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
    return "-and-".join(compact)


def action_category(action: str) -> str:
    action = action.lower()
    if action in {"click", "double_click", "triple_click"}:
        return "select"
    if action in {"type", "press", "hotkey", "key_down", "key_up"}:
        return "input"
    if action in {"scroll", "wheel"}:
        return "scroll"
    if action in {"drag", "move_to"}:
        return "drag"
    if action in {"wait", "sleep"}:
        return "wait"
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
    learned = report["test_metrics"]["learned_boundary_backend"]
    baselines = {row["name"]: row for row in report["test_metrics"]["baselines"]}
    lines = [
        "# R297 Operation Boundary Backend",
        "",
        "This run is an expansion probe over existing OSWorld-Human operations. It trains a held-out adjacent-boundary backend from non-oracle operation fields, writes predicted `learned_group` fields back to test operations, and leaves recursive folding to the Rust profiler.",
        "",
        "## Result",
        "",
        "- Learned backend: precision {precision}, recall {recall}, F1 {f1} over {pairs} held-out adjacent pairs.".format(
            precision=learned["precision"],
            recall=learned["recall"],
            f1=learned["f1"],
            pairs=report["test_pairs"],
        ),
        "- Baselines: phase-change F1 {phase}, action-change F1 {action}, group-pattern reference F1 {group_pattern}, always-boundary F1 {always}.".format(
            phase=baselines["phase_change"]["f1"],
            action=baselines["action_change"]["f1"],
            group_pattern=baselines["group_pattern_reference"]["f1"],
            always=baselines["always_boundary"]["f1"],
        ),
        "- Scope: this is supervised label-derived boundary prediction, not unsupervised intent discovery.",
        "",
        "## Generated Operation Fields",
        "",
        "- `learned_group`: predicted session-local group id for the held-out operations.",
        "- `learned_group_pattern`: cross-session action pattern derived inside each predicted group.",
        "- `learned_group_position`: start/middle/end/single inside the predicted group.",
        "- `learned_boundary_prev`: whether the current operation starts a predicted boundary.",
        "",
        "## Files",
        "",
    ]
    for key, value in report["outputs"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)


def render_html(report: dict[str, Any]) -> str:
    learned = report["test_metrics"]["learned_boundary_backend"]
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>R297 Operation Boundary Backend</title>
<style>
body{{font-family:system-ui,-apple-system,Segoe UI,sans-serif;margin:28px;background:#fafafa;color:#171717}}
h1{{font-size:24px;margin-bottom:4px}}
h2{{font-size:17px;margin-top:24px}}
.meta{{color:#555;margin-bottom:16px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}}
.card{{background:white;border:1px solid #ddd;border-radius:6px;padding:12px}}
.value{{font-size:24px;font-weight:700}}
table{{border-collapse:collapse;width:100%;background:white;border:1px solid #ddd}}
th,td{{padding:7px 9px;border-bottom:1px solid #eee;text-align:left;font-size:13px}}
th{{background:#f0f3f8}}
</style>
</head>
<body>
<h1>R297 Operation Boundary Backend</h1>
<div class="meta">Held-out OSWorld-Human adjacent-boundary expansion probe; not an unsupervised detector.</div>
<div class="cards">
<div class="card"><div>Precision</div><div class="value">{learned['precision']}</div></div>
<div class="card"><div>Recall</div><div class="value">{learned['recall']}</div></div>
<div class="card"><div>F1</div><div class="value">{learned['f1']}</div></div>
<div class="card"><div>Test Pairs</div><div class="value">{report['test_pairs']}</div></div>
</div>
<h2>Baselines</h2>
{html_table(report['test_metrics']['baselines'])}
<h2>Top Features</h2>
{html_table(report['model']['top_features'])}
</body>
</html>
"""


def html_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "<p>None.</p>"
    keys = list(rows[0].keys())
    out = ["<table><tr>"]
    out.extend(f"<th>{html.escape(key)}</th>" for key in keys)
    out.append("</tr>")
    for row in rows:
        out.append("<tr>")
        for key in keys:
            out.append(f"<td>{html.escape(str(row.get(key, '')))}</td>")
        out.append("</tr>")
    out.append("</table>")
    return "\n".join(out)


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    feature_fields = args.feature_field or DEFAULT_FEATURE_FIELDS
    requirement = parse_requirement(args.require_field)

    operations = load_operations(args.operation_file)
    groups = group_sequences(operations, args.sequence_field, args.oracle_field, requirement)
    sort_sequences(groups, args.turn_field)
    train_sequences, test_sequences = split_sequences(
        list(groups), args.split_seed, args.train_percent
    )
    train_examples = build_examples(
        groups, train_sequences, feature_fields, args.oracle_field, args.turn_field
    )
    test_examples = build_examples(
        groups, test_sequences, feature_fields, args.oracle_field, args.turn_field
    )

    model = BernoulliBoundaryModel()
    model.fit(train_examples)
    augmented_operations = augment_test_operations(
        groups, test_sequences, model, feature_fields, args.oracle_field, args.turn_field
    )

    augmented_path = out_dir / "osworld-learned-boundary-test-operations.jsonl"
    report_path = out_dir / "boundary-backend-report.json"
    md_path = out_dir / "boundary-backend-report.md"
    html_path = out_dir / "boundary-backend-report.html"
    spec_path = out_dir / "learned-boundary-profile-spec.json"

    profile_spec = {
        "output": "learned-boundary.folded",
        "format": "folded",
        "view": "operations",
        "project_name": "external-agent-traces",
        "operation_files": [augmented_path.name],
        "stack": "project,dataset,task,phase,learned_group_pattern,learned_group_position,action,status",
    }
    report = {
        "schema": "agentsight.operation-boundary-backend.v1",
        "run_id": "R297",
        "source": rel(args.operation_file),
        "oracle_field": args.oracle_field,
        "sequence_field": args.sequence_field,
        "turn_field": args.turn_field,
        "require_field": args.require_field,
        "feature_fields": feature_fields,
        "leakage_policy": {
            "excluded_fields": sorted(LEAKAGE_FIELDS),
            "excluded_prefixes": list(LEAKAGE_PREFIXES),
            "note": "Oracle/group fields are excluded from model features; group_pattern is only a reference baseline.",
        },
        "split": {
            "seed": args.split_seed,
            "train_percent": args.train_percent,
            "train_sequences": len(train_sequences),
            "test_sequences": len(test_sequences),
            "train_operations": sum(len(groups[sequence]) for sequence in train_sequences),
            "test_operations": sum(len(groups[sequence]) for sequence in test_sequences),
        },
        "train_pairs": len(train_examples),
        "test_pairs": len(test_examples),
        "model": {
            "kind": "bernoulli-naive-bayes-adjacent-boundary",
            "threshold": round(model.threshold, 6),
            "features": len(model.vocab),
            "top_features": model.top_features(),
        },
        "train_metrics": {
            "learned_boundary_backend": evaluate_model(model, train_examples),
            "baselines": evaluate_baselines(train_examples),
        },
        "test_metrics": {
            "learned_boundary_backend": evaluate_model(model, test_examples),
            "baselines": evaluate_baselines(test_examples),
        },
        "outputs": {
            "augmented_operations": rel(augmented_path),
            "profile_spec": rel(spec_path),
            "json": rel(report_path),
            "markdown": rel(md_path),
            "html": rel(html_path),
        },
        "claim_scope": {
            "supported": "A supervised adjacent-boundary backend can derive stackable learned_group_pattern fields on held-out OSWorld-Human sessions.",
            "not_supported": "Unsupervised intent discovery or a general boundary detector across all agent traces.",
        },
    }

    write_jsonl(augmented_path, augmented_operations)
    write_json(spec_path, profile_spec)
    write_json(report_path, report)
    md_path.write_text(markdown(report), encoding="utf-8")
    html_path.write_text(render_html(report), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "ok",
                "run_id": "R297",
                "json": rel(report_path),
                "markdown": rel(md_path),
                "html": rel(html_path),
                "augmented_operations": rel(augmented_path),
                "profile_spec": rel(spec_path),
                "test_pairs": len(test_examples),
                "test_f1": report["test_metrics"]["learned_boundary_backend"]["f1"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
