#!/usr/bin/env bash
# Independent, read-only RQ7 source/oracle checker. It imports neither
# agent-session nor the proposed query implementation.
set -euo pipefail

freeze=${1:?freeze.json required}
output=${2:?output json required}
private=$(dirname "$freeze")
script_dir=$(cd "$(dirname "$0")" && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

jq -r '.projects[] | .sources[] | [.home_relative,.sha256,(.bytes|tostring)] | @tsv' "$freeze" > "$tmp/sources.tsv"
while IFS=$'\t' read -r relative expected_hash expected_bytes; do
    path="$private/frozen-home/$relative"
    test -f "$path"
    test "$(wc -c < "$path")" = "$expected_bytes"
    test "$(sha256sum "$path" | awk '{print $1}')" = "$expected_hash"
done < "$tmp/sources.tsv"

# Recompute every fixed answer from the source-witness rows and action streams,
# then require exact equality with the separately materialized question table.
jq -r '
  def emit($p;$t;$v): [$p,$t,($v|tostring)] | @tsv;
  def atoms($p): ($p.direct_action_atoms | to_entries | map(.value) | add // []);
  def session_sets($p):
    [range(0; ($p.sessions|length)) as $i |
      [$p.oracle_edges[] | select(.session_ordinal==$i) | .artifact_id] | unique];
  .projects[] as $p |
  ($p.anchors[0].artifact_id) as $p0 |
  ([atoms($p)[] | select(.=="read_file")] | length) as $a1 |
  ([atoms($p)[] | select(.=="edit")] | length) as $a2 |
  ([atoms($p)[] | select(.=="run_test")] | length) as $a3 |
  ([$p.direct_action_atoms | to_entries[].value | join(" ") + " " |
      select(test("read_file (?:[a-z_]+ )*edit "))] | length) as $a4 |
  ([$p.direct_action_atoms | to_entries[].value | join(" ") + " " |
      select(test("edit (?:[a-z_]+ )*run_test "))] | length) as $a5 |
  ([$p.oracle_edges[] | select(.artifact_id==$p0)] | sort_by(.event_ordinal)) as $pe |
  ($pe | unique_by([.session_id,.call_id])) as $pc |
  (session_sets($p)) as $sets |
  (reduce range(0; (($sets|length)-1)) as $i (0;
      . + (if (($sets[$i] - ($sets[$i] - $sets[$i+1])) | length) > 0 then 1 else 0 end))) as $adj |
  (reduce $sets[] as $cur ({seen:[],count:0};
      . as $state
      | .count += (if (($cur - ($cur - $state.seen)) | length) > 0 then 1 else 0 end)
      | .seen = ((.seen + $cur) | unique))) as $revisit_state |
  ($revisit_state.count) as $revisit |
  ([$pe[].session_ordinal] | unique | sort) as $pords |
  (reduce range(0; ($sets|length)) as $i ({seen:false,gap:false,count:0};
      if ($pords|index($i)) != null then
        .count += (if .seen and .gap then 1 else 0 end) | .seen=true | .gap=false
      elif .seen then .gap=true else . end)) as $return_state |
  ($return_state.count) as $returns |
  ([$sets[] | .[]] | group_by(.) | map(select(length>=2)) | length) as $multi |
  emit($p.project;"A1";$a1), emit($p.project;"A2";$a2), emit($p.project;"A3";$a3),
  emit($p.project;"A4";$a4), emit($p.project;"A5";$a5),
  emit($p.project;"B1";($pc|length)),
  emit($p.project;"B2";([$pc[]|select(.action_class=="read")]|length)),
  emit($p.project;"B3";([$pc[]|select(.action_class=="mutate")]|length)),
  emit($p.project;"B4";$pe[0].action_class),
  emit($p.project;"B5";($pords|length)),
  emit($p.project;"C1";$adj), emit($p.project;"C2";$revisit),
  emit($p.project;"C3";$returns),
  emit($p.project;"C4";($pords[-1]-$pords[0])), emit($p.project;"C5";$multi),
  ($p.workspace.paths | to_entries[] | emit($p.project;("D"+((.key+1)|tostring));.value.status))
' "$freeze" | sort > "$tmp/recomputed.tsv"

jq -r '.questions[] | [.project,.template,.answer] | @tsv' "$freeze" | sort > "$tmp/expected.tsv"
cmp "$tmp/recomputed.tsv" "$tmp/expected.tsv"
test "$(wc -l < "$tmp/recomputed.tsv")" = 120
for family in A B C D; do
    test "$(awk -F '\t' -v f="$family" '$2 ~ ("^" f) {n++} END {print n+0}' "$tmp/recomputed.tsv")" = 30
done

# Every immutable witness source is reopened above. Native call IDs that are
# explicit rather than synthetic must also occur in the copied source bytes.
jq -r '.projects[] as $p | $p.oracle_edges[] as $e |
  ($p.sources[] | select(.source_id==$e.source_id)) as $s |
  select(($e.call_id|test("^[0-9]+:[0-9]+$"))|not) |
  [$s.home_relative,$e.call_id] | @tsv' "$freeze" | sort -u > "$tmp/calls.tsv"
while IFS=$'\t' read -r relative call_id; do
    test -z "$relative" && continue
    rg -F --quiet -- "$call_id" "$private/frozen-home/$relative"
done < "$tmp/calls.tsv"

answers_hash=$(sha256sum "$tmp/recomputed.tsv" | awk '{print $1}')
checker_hash=$(sha256sum "$script_dir/rq7_oracle_check.sh" | awk '{print $1}')
jq -n \
  --arg status pass \
  --arg answers_sha256 "$answers_hash" \
  --arg checker_sha256 "$checker_hash" \
  --argjson questions 120 \
  '{status:$status,questions:$questions,answers_sha256:$answers_sha256,checker_sha256:$checker_sha256}' > "$output"
