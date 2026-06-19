# R250 OSDI Gate Review

Status: `not_weak_accept_after_review`

Two read-only subagents reviewed the state after R249. One reviewed
paper/evidence alignment; one reviewed artifact/community readiness and the
R249 package. Both kept the project at OSDI Level 3, not weak accept.

## Highest-Risk Blocker

C5 still has 0 real participant responses, and C6 still has 0 real human
adequacy labels. R249 makes the paper-scale C5 launch package executable, but
it is not outcome evidence.

## Paper Review

Must-fix boundaries:

- Do not claim developer utility without scored C5 participant responses.
- Do not claim tag adequacy without R124 human labels.
- Keep C4 scoped to fixed and controlled workloads while Codex/Claude-launched
  target-network rows remain partial.

Applied revision:

- Reworded R249 descriptions from `12 participants` to `12 participant packets`
  or `12 assignment slots` when referring to launch material.
- Kept the C5 gate false and preserved the requirement for real scored
  responses.

## Artifact Review

Must-fix boundaries:

- The checked R248 artifact smoke uses `cargo install --path agentpprof --locked
  --force`; public registry releases may lag this research branch.
- R248 generated reports must not commit local absolute paths from Cargo stderr.
- R249 must not instruct coordinators to fill the committed blank template in
  place.

Applied revision:

- Updated top-level and `agentpprof` install docs to prefer source-tree install
  for artifact reproduction.
- Updated R248 to sanitize stderr tails and include its JSON/Markdown reports in
  the privacy scan.
- Updated R249 generated README, participant instructions, manifest fields, and
  real-response scoring command to use a private completed-response CSV.
- Documented that `--include-previews` writes prompt/command/LLM-output previews
  into JSON and should be avoided for public artifacts unless inputs are
  sanitized.

## Verdict

R250 improves review hygiene, artifact privacy, and paper-scale collection
wording. It does not add participant responses, human labels, external-machine
adoption, or weak-accept evidence.
