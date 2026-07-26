# Discussion: how to finish the RQ7 repair — I want your critical read, not code

You are in a research repo (longitudinal AI-agent workspace study). Do NOT modify any files — this is a read-only design discussion. Read these first:

- docs/tmp/build-and-evaluate/rq7-error-taxonomy-20260725/taxonomy.md (per-question error taxonomy of 28 wrong conformance answers)
- docs/tmp/build-and-evaluate/rq7-error-taxonomy-20260725/rerun-at-HEAD/result.md (HEAD rerun: trajectory B+C 51/60, 9 mismatches left)
- docs/tmp/build-and-evaluate/step-0004-20260723T181008-0700/experiment-001/private/question-spec.md (frozen question semantics)
- docs/evaluation.md (study status; RQ1-RQ4 currently rely on the same projection)

State of play:
- 28 wrong answers split into 14 deliberate-broader shell/scope semantics (projection counts git add/diff/status operands, redirection/heredoc segments, grep/rg/wc/ls/find operands; the frozen oracle excludes them per spec) + 14 genuine bugs (session-join, fail-drop, path-extraction) which are fixed in HEAD.
- HEAD rerun: 51/60 B+C. Of the 9 remaining mismatches, 3 are oracle-side artifacts (cat -n arity, inline-cd tracking) and 6 (ActPlane/bpf C-family) are heavily driven by an oracle blind spot: codex exec JS-wrapper apply_patch (~480 real mutations invisible to the oracle).
- A separate worker is right now fixing the oracle (v4: JS-wrapper unwrap, inline-cd) and re-deriving all 120 expected answers. Another worker is recomputing RQ1-RQ4 main-corpus numbers at HEAD.

Discuss these questions and give me a concrete recommendation on each, with trade-offs:

1. The 6 residual "broader semantics" rows: should the projection gain a spec-aligned narrow mode (exclude git-status-class operands, redirection/heredoc, search-tool operands) so the conformance matrix can pass exactly, or should the study keep the broader extraction and report the difference as admitted semantics? Consider: the same broader extraction feeds RQ1-RQ4, so a narrow mode might change those numbers too; and reviewers will ask "so which one is the measurement?"
2. Moving ground truth: the oracle is being corrected mid-study (v3 -> v4). What discipline keeps this defensible (e.g., per-question justification log, keeping frozen v2 results, replaying both oracles)? Anything you would refuse to do?
3. After both workers finish, what is the minimal set of things that must be true before the paper's negative capability claim ("rejects the current implementation's exact-fact capability") can be revised — and what should it be revised INTO? Consider the options: (a) claim capability with the taxonomy as evidence of fixed bugs, (b) keep a weakened claim with broader-vs-aligned dual reporting, (c) keep the negative result for the frozen implementation and report HEAD separately.
4. Sequencing risk: RQ1-RQ4 numbers will shift (eunomia.dev recovered 580 calls). What is the right order of operations to update docs/evaluation.md and docs/paper/main.tex without creating an inconsistent intermediate state?

End with: the single most likely way this repair effort could still produce an overclaim, and how to prevent it.
