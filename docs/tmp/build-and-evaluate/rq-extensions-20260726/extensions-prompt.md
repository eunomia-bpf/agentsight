# Task: Two incremental RQ analyses + two robustness spot-checks

Repo: longitudinal agent-workspace study (see docs/evaluation.md for current frontier). Frozen main-corpus recompute rows exist at docs/tmp/build-and-evaluate/rq1-rq4-recompute-20260725/rq1-raw/ (rq1-artifacts.csv, rq1-mutations.csv, rq1-summary.csv, events/*.json[.gz], projects.json). The projection/extraction binary is agentvis (Rust, already built at agentvis/target/release/agentvis; rebuild with cargo build --release --manifest-path agentvis/Cargo.toml if needed). Analysis scripts live in agentvis/research/.

Write all outputs to docs/tmp/build-and-evaluate/rq-extensions-20260726/ (result.md + scripts + any CSVs). Do NOT edit docs/paper/* (another worker is restructuring it), do NOT edit frozen dirs, no git commands.

## A. RQ1 extension: dormant-to-revived transitions (documented next action in docs/evaluation.md)

From the recompute rows: for each artifact identity, compute lifecycle episodes — active mutation span, dormancy gap (no touches), revival (first touch after a dormancy gap above a declared threshold). Report per project: number/ share of artifacts that go dormant and are later revived, dormancy-gap distribution (median/p90), and revival counts. Declare thresholds explicitly (e.g., gap > N actions or > T hours; do both an action-gap and a time-gap variant). Keep it descriptive — no progress score.

## B. RQ3 extension: rank-turnover / cooling curves (documented next action)

Per project: over action order, track the top-k most-touched artifact/module in sliding windows; compute rank-turnover (how often the top-1 and top-5 membership changes) and a cooling curve (fraction of windows where a once-hot artifact stays hot after k windows). Report per project + pooled descriptive stats.

## C. Robustness spot-checks (two known latent projection risks)

1. `encoded_claude_root` in agentvis/src/repository.rs (~line 1050) replaces '/' but not '.', so Claude sessions whose project dir contains dots and whose records lack cwd could be dropped. Check whether any session in the current corpus hits this path (cwd-less transcripts under a dotted dir); if the corpus is unaffected, prove it with a query; if affected, quantify.
2. `plausible_path_token` in agent-session/src/parser.rs rejects bare filenames without whitelisted extensions and tokens >140 chars for non-sed commands. Quantify how many shell path operands in the corpus events are dropped by these two filters (scan the events JSONs; estimate upper bound of missed edges).

## Deliverable

result.md with per-analysis numbers and methods, plus a short "for the paper" paragraph per analysis (3-5 sentences each, ready to paste into a supplement). If a spot-check finds real impact, flag it prominently at the top of result.md.
