# Step 0061 Report — User-Requested Full-Paper Review

## Step Identity And Recovery

- started: 2026-07-20T19:20:35-07:00
- phase: BUILD_AND_EVALUATE
- selected outer action: user-requested milestone-style full-paper REVIEW
- branch throughout: `research/semantic-flamegraph-artifacts-v2`
- entry commit: `361da290fa9a419e8182b1b3c9cfafd189eb7fee`
- parent: Step 0060 result-grounded task-stack experiment
- status: complete; independent outer audit PASS

### Recovery Node

Step 0060 is complete, independently approved, committed, and pushed. Its
tested fixed Qwen2.5-3B OPEN/CLOSE policy was not adopted because CLOSE almost
always returned complete; recurrence remains the current constructor. That
bounded mechanism result changed neither the paper nor its scientific
contract.

The user instruction log and current paper preserve the exact thesis
**“Agent observability needs profiling, not only debugging,”** the four RQs
(attribution, localization, tag accuracy, and cost), and the required main
representation:

```text
concrete task -> nested subtask* -> phase/strategy
              -> semantic action -> operation object -> result
```

Agent, model, session, prompt, tool, command, path, and status are evidence,
filters, colors, measures, or details rather than persistent semantic task
frames. The user explicitly requested full review by different models,
including Grok, before another algorithm iteration. This step therefore runs a
full-paper review now without treating it as a phase transition or as authority
to rewrite the frozen story.

## EXPERIMENT Gate

### Recorded Skip

No new experiment enters before the requested full-paper review. Step 0060
closed the immediately preceding mechanism branch and explicitly routed to
this review. Selecting another experiment without first identifying the
paper-level reject argument would violate paper-value admission and risk
another low-value prompt variant. The gate is skipped on that evidence; the
review may return one high-value, non-equivalent algorithm experiment to a
later EXPERIMENT gate.

## WRITE Gate

### Recorded Skip

The paper has not changed since the evidence state reviewed at the Step 0060
boundary, and Step 0060 produced no adopted paper result. There is therefore no
phase-permitted result or implementation fact to write before review. No
writing or idea-refinement skill runs, and `docs/paper/` remains unchanged.

## REVIEW Gate

### Entry And Alignment

The root reread `docs/user-instruction.md` and
`docs/questions-for-author.md`; there are no open author questions. The review
uses `iter-review-critique`: blind whole-paper read, attack map, external
primary-source search, full reread, cycle-change audit, and final routing. The
paper is routed as cross-domain systems/AI work targeting AAAI 2027, so both
systems and AI/ML criteria plus the cross-domain causal-chain bar apply.

The review is read-only for the paper, idea story, user log, canonical memory,
and Git. Grok 4.5 and Claude Opus receive the same paper-only review brief and
no prior reviewer verdict, expected answer, experiment history, or proposed
fix. A fresh internal reviewer performs a separate blind paper-only read. The
root independently verifies external sources and accepts, rejects, or defers
model findings against user intent, raw evidence, and the frozen contract.

### Review Completion

The complete review is recorded under `milestone-review-001/`:

- `01-blind-full-read.md` — fresh internal paper-only attack map;
- `reviewer-grok-4.5.md` — Grok 4.5 whole-paper and external-source review;
- `reviewer-claude-opus.md` — Claude Opus 4.8 whole-paper and
  external-source review;
- `02-external-search-source-verification.md` — root primary-source audit;
- `03-full-paper-reread-assessment.md` — post-search paper reread;
- `04-cycle-audit-final-verdict.md` — cycle change audit, disposition, and
  next-state selection.

The independent outer audit, its two correction rounds, and final PASS are
recorded in
[`outer-audit-20260720T195242-0700.md`](outer-audit-20260720T195242-0700.md).

All three independent readers and the root agree that the exact thesis is
important but the current paper is not AAAI-ready. The current formal stack is
an ordered field fold, the automatic recurrence method emits flat segments,
and the principal figure places system metadata in persistent frames. No
current experiment validates the required variable-depth responsibility path:

```text
concrete task -> nested subtask* -> phase/strategy
              -> semantic action -> operation object -> result
```

The reviewers also agree that additional prompt wording, NPMI terms, cutoff
tuning, depth limits, contraction, or lexical cleanup cannot close that gap.

### Evidence Assessment And Routing Decision

The root accepts the mechanism and evidence objection and rejects any automatic
story shrinkage. Claude explicitly recommends recovering and validating a
variable-depth task/subtask hierarchy or dependency structure while preserving
the thesis and four RQs. The root adopts the task-stack form of that direction
because it directly repairs the challenged mechanism while preserving the
permanent Initial Narrative and explicit user instructions. Complex
hierarchical Bayesian and partial-order mechanisms are retained as baselines or
precedents, not automatically promoted into new core abstractions.

The selected non-equivalent mechanism is intent-anchored task-stack
construction: only user tasks, plans, delegations, progress, and completion
events may change persistent task frames. Ordinary model, tool, command, file,
process, and network events inherit the active path and remain action/object/
result evidence or metadata. This preserves operations and operation stacks as
the only core abstractions.

The next experiment answers RQ3 only. Its primary scored population must have
task/subtask structure independent of the constructor. WorkArena++ is the
leading public compositional reference; ToolSandbox can provide a secondary
dependency/completion reference but is not by itself nested-task ground truth.
The complete eligible local Codex population is a secondary real-world
coverage and scale target, not a correctness oracle. Its exact census,
eligibility rules, exclusions, and parser evidence belong in the reviewed
experiment plan and real preflight rather than this review report.

The RQ3 experiment must separately score occurrence-level structure and stable
cross-run task/subtask identity without reading a scoring key during
construction. RQ1 decision quality and RQ2 problem localization remain later
experiments; this mechanism test does not mix their outcomes into RQ3.

## Canonical Memory Sync

`docs/design.md` now records the selected but unadopted task-semantic
construction rule. `docs/evaluation.md` records this review and routes to the
next experiment. `docs/background-related-work.md` records BPOP,
cross-framework signal reversal, WorkArena++, and ToolSandbox as the relevant
structure/evaluation frontier. The paper, idea story, user log, shared skills,
production code, and branch remain unchanged.

## Transition

REVIEW is complete and routes to EXPERIMENT. No WRITE gate is authorized until
the intent-anchored constructor completes a real preflight, complete run, and
independent result review and is adopted by the root.
