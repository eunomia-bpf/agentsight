# RQ6 Experiment Plan — Skill and Harness Association

**Created:** 2026-07-22T01:30:03-07:00  
**State:** preregistration draft; no RQ6 statistic has been computed

## 1. Question and boundary

RQ6 asks whether the frozen corpus has enough source-visible skill or harness
configuration evidence to support a temporal association analysis. The frozen
RQ1 export does not retain Skill invocation arguments, model/configuration
fields, or repository-external instruction paths. Therefore this experiment is
a preregistered **source-coverage audit and stop decision**, not an
exposed-versus-unexposed analysis. It cannot identify a causal or descriptive
effect of a skill, harness, model, or task. Cases such as document burden or
test-only iteration remain motivating hypotheses, not labels assigned here.

## 2. Recoverable source signals

Reuse only the frozen RQ1 native Tool timeline at cutoff `1784708569241`.
Extract three non-equivalent source kinds and never combine them into a binary
exposure:

1. `skill_tool`: case-insensitive exact `tool_name == "skill"`; the Skill name
   and arguments are unavailable;
2. `instruction_read`: a non-scope file action with `access == read` and
   case-insensitive basename exactly `AGENTS.md`, `CLAUDE.md`, or `SKILL.md`;
3. `instruction_mutation`: the same exact basename rule with access in
   `{write, create, rename, delete}`. This is a work-target signal, not evidence
   that the instruction governed the Agent.

Retain native `ok`, `observed`, and `fail` separately. A failed Tool event emits
no confirmed file effect under RQ1, so instruction-file actions appear only
when the repository projection retained them. `no_observed_source_event` means
only that none of the three signals is visible; it is never called unexposed.
Native model, harness configuration, Skill name, and repository-external
instruction coverage are explicitly unavailable. No prose or LLM inference is
allowed.

## 3. Coverage units and stop audit

The primary denominator is every admitted native session in the frozen RQ1
timeline, stratified by project and vendor. A session can contain multiple
non-exclusive source kinds. Report exact event counts and unique-session counts
by project, vendor, source kind, and native status, plus first/last event time.
For temporal support, partition each project's full event sequence into 60
equal-count action-order bins using `floor(event_index * 60 / N)`, capped at 59,
and count signal events in each bin. This diagnoses calendar/source separation;
it is not a follow-up horizon or outcome window.

No artifact, validation, rework, readback, survival, or test-concentration
contrast is computed. Instruction reads cannot establish actual harness
exposure, instruction mutations are outcomes/work targets, and Skill arguments
are missing. Parallel-session attribution and outcome censoring are therefore
not invoked. The absence of a forest plot is the scientific stop result, not a
missing implementation.

## 4. Figure F9

Create a coverage-only figure:

- **Panel A:** non-exclusive proportion of admitted sessions containing each
  recoverable source kind, with exact session numerator/denominator;
- **Panel B:** event counts by project, vendor, source kind, and status; and
- **Panel C:** 60-bin native action-order occurrence heatmaps showing whether
  the signals are distributed or temporally isolated.

The figure prints `association analysis stopped` and the unavailable fields.
It contains no effect/contrast estimate, confidence interval, or zero-filled
unavailable outcome.

## 5. Execution, verification, and decision

Run:

```bash
python3 agentvis/research/plot_rq6.py \
  --rq1-root docs/tmp/build-and-evaluate/step-0002-20260722T003659-0700/experiment-rq1-20260722T003659-0700/full-six-projects/raw \
  --output docs/tmp/build-and-evaluate/step-0002-20260722T003659-0700/experiment-rq6-20260722T013003-0700
```

Write `raw/rq6-observed-events.csv`, `rq6-source-coverage.csv`,
`rq6-session-coverage.csv`, `rq6-action-bins.csv`,
`figures/rq6-source-coverage.pdf/.png`, `result.md`, and `commands.log`. Verify
frozen hashes; reconcile every RQ1 event to project/vendor/session denominators;
verify every signal against its native source ID and exact Tool/path rule; and
render F9 only by rereading frozen CSVs.

The decision is fixed in advance: because the input lacks Skill arguments,
model/config fields, repository-external instructions, and a negative-exposure
guarantee, RQ6 association claims stop regardless of observed counts. Positive
coverage shows where a future enriched export could support a controlled study;
heterogeneous coverage identifies adapter/project stratification; sparse or
temporally isolated coverage strengthens the stop. None supports harness
effectiveness, waste, causality, or population prevalence. Completion is a
reviewed coverage figure and explicit stop, without human or LLM gold.

Independent plan and result reviews are required before F9 enters the paper.
