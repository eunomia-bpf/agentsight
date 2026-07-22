def labels: ["stagnation", "goal_drift", "validation_gap", "harness_waste"];
def ratio($n; $d): if $d == 0 then null else $n / $d end;
def f1_counts($tp; $fp; $fn):
  (2 * $tp + $fp + $fn) as $denominator
  | if $denominator == 0 then null else 2 * $tp / $denominator end;

$gold[0] as $g
| $pred[0] as $p
| [labels[] as $label | {
    label: $label,
    gold: ($g[$label] == true),
    predicted: ($p[$label] == true)
  }] as $decisions
| ($decisions | map(select(.gold and .predicted)) | length) as $label_tp
| ($decisions | map(select((.gold | not) and .predicted)) | length) as $label_fp
| ($decisions | map(select(.gold and (.predicted | not))) | length) as $label_fn
| ratio($label_tp; $label_tp + $label_fp) as $label_precision
| ratio($label_tp; $label_tp + $label_fn) as $label_recall
| [$decisions[] | select(.gold and .predicted) | .label] as $correct_positive_labels
| ([$correct_positive_labels[] as $label
    | $g.evidence[$label].action_ids[]?] | unique) as $gold_actions
| ([$correct_positive_labels[] as $label
    | $p.evidence[$label].action_ids[]?] | unique) as $pred_actions
| ([$pred_actions[] | select(. as $action | $gold_actions | index($action))] | length) as $evidence_tp
| ($pred_actions | length) as $evidence_predicted
| ($gold_actions | length) as $evidence_gold
| ratio($evidence_tp; $evidence_predicted) as $evidence_precision
| ratio($evidence_tp; $evidence_gold) as $evidence_recall
| {
    labels: {
      exact_match: ($decisions | all(.gold == .predicted)),
      decisions: $decisions,
      tp: $label_tp,
      fp: $label_fp,
      fn: $label_fn,
      precision: $label_precision,
      recall: $label_recall,
      f1: f1_counts($label_tp; $label_fp; $label_fn)
    },
    evidence: {
      correctly_predicted_positive_labels: $correct_positive_labels,
      gold_action_count: $evidence_gold,
      predicted_action_count: $evidence_predicted,
      tp: $evidence_tp,
      precision: $evidence_precision,
      recall: $evidence_recall,
      f1: f1_counts(
        $evidence_tp;
        $evidence_predicted - $evidence_tp;
        $evidence_gold - $evidence_tp
      )
    },
    intervention: {
      recommendation_match:
        (($g.intervention_recommended == true) ==
         ($p.intervention_recommended == true)),
      earliest_action_exact:
        ($g.earliest_intervention_action_id ==
         $p.earliest_intervention_action_id)
    }
  }
