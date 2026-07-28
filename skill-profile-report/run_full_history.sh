#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "$0")/.." && pwd)
report_dir="$repo_root/skill-profile-report"
claude_root=/home/yunwei37/.claude/projects
binary="$repo_root/agentpprof/target/release/agentpprof"
stack=project,agent,task,skill,phase,action,object,result,outcome,op,call,tool,token

mapfile -d '' session_files < <(
  find "$claude_root" -type f -name '*.jsonl' -print0 | LC_ALL=C sort -z
)
printf '%s\n' "${session_files[@]}" > "$report_dir/session-files.txt"

snapshot_root=$(mktemp -d /tmp/agentpprof-skill-snapshot-XXXXXX)
cleanup_snapshot() {
  rm -rf -- "$snapshot_root"
}
trap cleanup_snapshot EXIT

snapshot_files=()
: > "$report_dir/snapshot-manifest.tsv"
for session_file in "${session_files[@]}"; do
  cp --parents --reflink=auto "$session_file" "$snapshot_root"
  snapshot_file="$snapshot_root$session_file"
  snapshot_files+=("$snapshot_file")
  bytes=$(stat -c '%s' "$snapshot_file")
  sha256=$(sha256sum "$snapshot_file")
  sha256=${sha256%% *}
  printf '%s\t%s\t%s\n' "$sha256" "$bytes" "$session_file" \
    >> "$report_dir/snapshot-manifest.tsv"
done

python3 "$report_dir/source_oracle.py" "${snapshot_files[@]}" \
  > "$report_dir/source-oracle.json"

session_args=()
for session_file in "${snapshot_files[@]}"; do
  session_args+=(--session-file "$session_file")
done

for view in tokens operations; do
  "$binary" \
    --project-root "$repo_root" \
    --project-name claude-full-history \
    --agent claude \
    --view "$view" \
    --stack "$stack" \
    --no-cache \
    --deterministic-output \
    "${session_args[@]}" \
    --output "$report_dir/full-history.$view.pb.gz" \
    > "$report_dir/full-history.$view.run.json" \
    2> "$report_dir/full-history.$view.stderr.log"
done
