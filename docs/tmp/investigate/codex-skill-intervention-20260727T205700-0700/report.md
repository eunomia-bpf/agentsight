FEASIBLE ONLY WITH NEW SESSIONS

# Existing-data feasibility report

## Bottom line

The 42-record self-profile supports a useful exploratory natural-experiment
check, but it cannot close a defensible profiler intervention loop. The most
plausibly removable recurring responsibility is `delegate review`, directly
targeted by a real rule limiting extra reviewers/checkers. Under the same
frozen semantic hierarchy, however, its aggregate token share **increases**
from 0.125708% before the rule to 1.145288% after it. An unweighted per-record
statistic moves in the opposite direction, from 3.031144% to 0.204856%. That
sign reversal is evidence of severe record-size and task-mix confounding, not
an optimization result.

There is no credible existing matched-task control, predeclared unaffected
placebo, independent task-quality outcome, or logged instruction-version
exposure. The direct split has only seven post-change records. The existing
data therefore cannot support “profile -> change the skills/rules -> re-profile
the same responsibility -> attributed share moved” as a downstream
intervention or RQ result.

This disposition follows the boundary already recorded in
`docs/evaluation.md` Steps 0013--0014: replaying or reorganizing existing
evidence is not a downstream intervention. I do not rebrand this retrospective
split as one. The currently fixed paper story also has four RQs; making this a
fifth RQ would require a separate author-level story decision even after valid
new evidence exists.

## Data found and inspected

The 42-record self-profile is not an annotation workspace under
`.agentsight/experiments/`. Its authoritative retained run is:

`docs/tmp/build-and-evaluate/step-0086-20260725T213500-0700/experiment-001/`

I inspected:

- `frozen-population.json`: 42 frozen records, 18 Codex and 24 Claude,
  totaling 55,000,887 bytes;
- `frozen-sessions/`: the exact frozen raw inputs;
- `workspace/trace.jsonl`: 10,423 nodes (42 session, 1,252 prompt, 5,620
  LLM, and 3,509 tool nodes);
- `workspace/annotation.json`: 1,737 final semantic annotations;
- `workspace/stacks.folded`: 5,620 token stacks;
- `operation-count.pb.gz`: the 3,509-operation profile;
- `token-width.pb.gz`: the 1,380,863,014-token profile;
- `results.md`, `aggregate-summary.md`, `execution-log.md`, and the independent
  result review.

The 42 records contain only 31 distinct native `source_session` values because
some Claude subagent records share a native parent session. All 42 corresponding
raw histories still exist under `/home/yunwei37/.claude/projects/` and
`/home/yunwei37/.codex/sessions/`; 41 remain at the frozen byte length and one
has grown. All calculations here use the frozen copies, not the mutable source.

The already rendered views are:

- `docs/visexp/out/r221-pprof-renderer-v1/selfprofile.tokens.png`
- `docs/visexp/out/r221-pprof-renderer-v1/selfprofile.operations.png`
- `docs/visexp/out/r221-pprof-renderer-v1/selfprofile.file-read.{png,svg}`
- `docs/visexp/out/r221-pprof-renderer-v1/selfprofile.file-write.{png,svg}`
- `docs/visexp/out/r221-pprof-renderer-v1/selfprofile.network.{png,svg}`

The file-read, file-write, and network renderings were added by the retained
Step 0090 work under
`docs/tmp/build-and-evaluate/step-0090-20260727T023000-0700/experiment-001/`;
they are projections of this history, not new sessions or intervention
outcomes.

The population is highly unbalanced by agent. Claude supplies 1,371,000,658
tokens (99.285783%) and 3,279 operations (93.445426%); Codex supplies
9,862,356 tokens and 230 operations. This prevents treating agent type as a
useful control.

Inventory commands:

```bash
EXP=docs/tmp/build-and-evaluate/step-0086-20260725T213500-0700/experiment-001
wc -l "$EXP/workspace/trace.jsonl" "$EXP/workspace/stacks.folded"
jq 'length' "$EXP/workspace/annotation.json"
jq -r '.sessions[].freeze_byte_length' "$EXP/frozen-population.json" |
  awk '{n++; s += $1} END {print n, s}'
jq -r '.sessions[].agent' "$EXP/frozen-population.json" | sort | uniq -c
jq -r '.kind' "$EXP/workspace/trace.jsonl" | sort | uniq -c
```

The relevant outputs were 10,423 trace lines, 5,620 folded-stack lines, 1,737
annotations, 42 files / 55,000,887 bytes, 24 Claude / 18 Codex records, and
42 / 1,252 / 5,620 / 3,509 session / prompt / LLM / tool nodes.

## Candidate responsibility

The best existing candidate is the exact semantic frame
`operation:delegate_review`.

It is preferable to merely large responsibilities such as paper refinement,
evidence inspection, or implementation because some delegated review can be
removed by an explicit workflow rule without removing the underlying research
task. It is nevertheless an imperfect target: the annotation name does not
separate required consolidated/result review from the redundant extra review
that the rule prohibits.

Across the complete profile, `delegate review` contains:

- 3,684,106 tokens, **0.266797%** of 1,380,863,014;
- 12 tool operations, **0.341978%** of 3,509;
- nonzero mass in 8 of 42 annotation records, but only 3 of 31 distinct native
  sessions.

This satisfies recurrence only weakly. It is a concrete measured responsibility,
but it is not a common operation across many independent sessions.

The stock-profile command and output were:

```bash
go tool pprof -top -nodefraction=0 -edgefraction=0 \
  -focus='operation:delegate_review' "$EXP/token-width.pb.gz"
# Showing nodes accounting for 3684106, 0.27% of 1380863014 total

go tool pprof -top -nodefraction=0 -edgefraction=0 \
  -focus='operation:delegate_review' "$EXP/operation-count.pb.gz"
# Showing nodes accounting for 12, 0.34% of 3509 total
```

I also checked seemingly stronger alternatives. `review implementation`
contains 5,834,935 tokens and 52 operations but occurs in only two native
sessions. `build checker` contains 14,391,929 tokens and 20 operations but
occurs in only one. Their larger mass does not compensate for the absence of
cross-session recurrence.

## Real change point

The repository rule most directly aimed at this responsibility is commit:

`4f3c442b6211ca2856b660d2ab2d7904e79467ae`

Author date: **2026-07-15 17:54:32 -0700**.

It added this rule to `CLAUDE.md`:

> Keep each research experiment to its plan, consolidated plan review, raw
> results, and result review. Resolve implementation validity inside those
> reviews; add a separate implementation review, extra evaluator/checker, or
> equivalence workflow only for a concrete unresolved validity risk. File,
> checker, and review counts are not research progress.

This plausibly targets superfluous delegated reviews and checkers. The exact
inspection command was:

```bash
git show --format=fuller --stat \
  4f3c442b6211ca2856b660d2ab2d7904e79467ae -- CLAUDE.md
git show --format= --unified=5 \
  4f3c442b6211ca2856b660d2ab2d7904e79467ae -- CLAUDE.md
```

There is an overlapping, earlier global-skill change:

`d359977a4b7cc9f7872816d640d794286ed172ab`

Author date: **2026-07-14 12:55:02 -0700**. It changed
`research-experiment-design/SKILL.md` to one fresh plan reviewer plus at most
one follow-up, prohibited additional review rounds/infrastructure, and allowed
one result review per completed run. No self-profile record starts between this
skill commit and the repository `CLAUDE.md` commit, so both produce the same
35/7 split. Their effects cannot be separated.

The repo-local `.claude/skills` is a symlink to `../skills`. Its only relevant
log entry added the tree on 2026-07-01, before the corpus, and `skills/` has
zero commits during the corpus window. The user-level
`/home/yunwei37/.claude/skills` points to
`/home/yunwei37/workspace/my-paper-work/academic-writing-skills/skills`, whose
history has **90** skill-tree commits during the corpus window, including
**66** commits touching the core experiment/orchestration/writing/review
skills. Consequently, the direct rule was not an isolated historical
intervention.

The repository-history alternatives do not improve the design:

| Change | Before / after records | Distinct native sessions | Assessment |
| --- | ---: | ---: | --- |
| Collaboration / paper-policy rules, 2026-07-06 | 2 / 40 | 2 / 30 | Essentially no baseline |
| Story and four-RQ invariants, `bbb3a3ed4d`, 2026-07-12 | 21 / 21 | 10 / 21 | Balanced, but it does not directly target a clean recurring removable responsibility |
| Reviewer/checker rule, `4f3c442b62`, 2026-07-15 | 35 / 7 | 24 / 7 | Direct target, anecdotal post side |
| Product-boundary rules, 2026-07-21 | 38 / 4 | 27 / 4 | Too few post records and different target |

The split counts came from the earliest real event in each trace record. I
excluded the synthetic `session bootstrap` prompt stamped at workspace-freeze
time; otherwise old subagent records falsely appear to span until July 26. No
record crosses the direct rule after that exclusion.

## Frozen-hierarchy replay

I did not regenerate or rename any annotations. I projected the existing
Step 0086 trace on either side of the change using the already frozen `path`
arrays and summed the existing token and operation measures.

| Measure | Before rule | After rule |
| --- | ---: | ---: |
| Annotation records | 35 | 7 |
| Distinct native sessions | 24 | 7 |
| All tokens | 1,189,779,496 | 191,083,518 |
| `delegate review` tokens | 1,495,650 | 2,188,456 |
| Aggregate target token share | **0.125708%** | **1.145288%** |
| All operations | 2,936 | 573 |
| `delegate review` operations | 7 | 5 |
| Aggregate target operation share | **0.238420%** | **0.872600%** |
| Target-positive records | 7 | 1 |
| Target-positive native sessions | 2 | 1 |
| Mean per-record target token share, zeros included | **3.031144%** | **0.204856%** |
| Median per-record target token share | 0% | 0% |

The aggregate token share rises by 1.019580 percentage points, a 9.1107x
ratio. Absolute target tokens also rise despite the much smaller post corpus.
This is not evidence that the rule optimized the responsibility. Conversely,
the unweighted per-record mean falls sharply because it gives small correlated
subagent batches the same weight as large sessions. The opposite signs make
the confound visible.

Reproduction command:

```bash
python3 - <<'PY'
import json, statistics
from datetime import datetime

p = ("docs/tmp/build-and-evaluate/"
     "step-0086-20260725T213500-0700/experiment-001/workspace/trace.jsonl")
cut = int(datetime.fromisoformat(
    "2026-07-15T17:54:32-07:00").timestamp() * 1000)

batches = []
for line in open(p):
    node = json.loads(line)
    if node["kind"] == "session":
        batches.append([node])
    else:
        batches[-1].append(node)

rows = []
for nodes in batches:
    root = nodes[0]
    real = [n for n in nodes[1:]
            if n["data"].get("timestamp_ms") is not None
            and n["data"].get("text") != "session bootstrap"]
    def mass(metric, label=None):
        return sum(n.get("metrics", {}).get(metric, 0) for n in nodes
                   if label is None or label in n.get("path", []))
    rows.append({
        "native": root["data"]["source_session"],
        "start": min(n["data"]["timestamp_ms"] for n in real),
        "end": max(n["data"]["timestamp_ms"] for n in real),
        "tokens": mass("tokens"),
        "operations": mass("operations"),
        "target_tokens": mass("tokens", "delegate review"),
        "target_operations": mass("operations", "delegate review"),
    })

for name, side in (
    ("before", [r for r in rows if r["start"] < cut]),
    ("after",  [r for r in rows if r["start"] >= cut]),
):
    t = sum(r["tokens"] for r in side)
    o = sum(r["operations"] for r in side)
    dt = sum(r["target_tokens"] for r in side)
    do = sum(r["target_operations"] for r in side)
    per_record = [r["target_tokens"] / r["tokens"] if r["tokens"] else 0
                  for r in side]
    print(name, "records", len(side),
          "native", len({r["native"] for r in side}),
          "crossing", sum(r["start"] < cut <= r["end"] for r in side),
          "tokens", t, "target_tokens", dt, "target_token_pct", 100*dt/t,
          "operations", o, "target_operations", do,
          "target_operation_pct", 100*do/o,
          "mean_record_pct", 100*statistics.mean(per_record),
          "median_record_pct", 100*statistics.median(per_record))
PY
```

## Conservation

Exact additive conservation holds for the complete frozen profile and for the
historical projection:

- Tokens:
  `1,189,779,496 + 191,083,518 = 1,380,863,014`.
- Operations:
  `2,936 + 573 = 3,509`.
- Target tokens:
  `1,495,650 + 2,188,456 = 3,684,106`.
- Target operations:
  `7 + 5 = 12`.
- Candidate plus noncandidate tokens:
  `3,684,106 + 1,377,178,908 = 1,380,863,014`.
- Candidate plus noncandidate operations:
  `12 + 3,497 = 3,509`.

The folded-stack and stock-pprof totals independently agree with the trace
measure totals:

```bash
awk '{s += $NF} END {printf "%.0f\n", s}' "$EXP/workspace/stacks.folded"
# 1380863014

go tool pprof -top "$EXP/token-width.pb.gz"
# ... of 1380863014 total

go tool pprof -top "$EXP/operation-count.pb.gz"
# ... of 3509 total
```

Thus conservation is not the failure. Causal identification is.

## Task-mix confound and controls actually available

### No credible matched-task control

Only one exact top-level semantic root occurs on both sides:
`review paper`. Restricting to it appears encouraging but is not a valid
match:

- before: 5 records from 2 native sessions, 874,101 of 9,762,974 tokens
  (8.953225%) and 4 of 25 operations (16%);
- after: 1 record from 1 native session, 0 of 11,212,122 tokens and 0 of 59
  operations.

The five pre records are correlated phase/round reviewer subagent batches; the
single post record is a top-level full-paper review. They do not share an exact
prompt, repository snapshot, model/configuration, or task instance. This is
one pseudo-match, not replication.

The raw histories have no repeated task ID or randomized paired condition.
Normalizing within a record does not solve this, because records differ in
purpose and 11 Claude batches share native sessions with other records.

### No credible placebo

As a post-hoc diagnostic, the seemingly unrelated `inspect paper`
responsibility also rises:

- tokens: 0.402475% before to 0.519836% after;
- operations: 0.783379% before to 2.966841% after.

This is consistent with a different post-change task mix, but `inspect paper`
was neither predeclared nor guaranteed to be unaffected by the review rule. It
cannot serve as a causal placebo.

### No quality/success guardrail

The profile has resource attribution but no independent task-success,
correctness, or manuscript-quality outcome for these sessions. A rule could
reduce review share simply by suppressing necessary checking and degrading the
result. Existing data cannot distinguish optimization from omission.

### Exposure is not logged

The session records do not retain the loaded `CLAUDE.md` commit, skill commit,
instruction hashes, or whether a long-running process reloaded changed files.
The many overlapping user-level skill commits make exact exposure
unrecoverable from timestamps alone.

### The target is retrospective

The semantic hierarchy was generated in one pass after the history was
collected. Reusing it for both halves correctly freezes measurement semantics,
but `delegate review` was selected after inspecting the profile and is not an
independently preregistered intervention endpoint. Step 0086 itself explicitly
does not establish annotation/tag accuracy.

## Other existing-data angles tested

1. **Balanced `bbb3a3ed4d` split (21/21 records).** This rule fixed the story,
   thesis, and four RQs. It has no clean one-to-one target among the recurring
   profile responsibilities. Selecting “align paper,” “review framing,” or
   similar after observing the profile would be a weaker post-hoc mapping than
   `delegate review`.
2. **Later AgentPProf product-boundary rules (38/4).** These have only four post
   records and target output/product design, not a sufficiently recurring
   removable responsibility.
3. **User-level skill history.** It provides many change points, not a clean
   intervention: 90 skill commits overlap the corpus. The most relevant one is
   inseparable from the repository rule because no record begins between them.
4. **Other retained AgentProf corpora.** The public good/bad, CodeTrace, R114,
   and git-multibranch data provide controls for correspondence, attribution,
   or workload behavior, but they do not contain baseline/intervention runs
   under two skill or `CLAUDE.md` policies. They cannot supply the missing
   treatment contrast.
5. **Step 0090 file/network projections.** They add measures over the same
   sessions, not an independent post-change observation or task control.

No better existing-data design was found.

## Cheapest experiment that supplies the missing evidence

The absolute cheapest genuine profiler-loop demonstration is **one new matched
pair**: two fresh sessions on an identical frozen task/repository snapshot,
one using the baseline rule set and one using the optimized rule set. That
would demonstrate one concrete before/after instance, but it would remain
anecdotal.

A still-small and more credible case-study pilot is **three randomized matched
pairs (six new sessions)** on one fixed task:

1. Freeze the repository, input task, prompt, model/version, tool permissions,
   budget, and all rules except the one intervention.
2. Condition A uses the exact pre-change experiment-review rule. Condition B
   adds the exact reviewer/checker limit from `d359977`/`4f3c442`.
3. Randomize A/B order within each pair and use a fresh isolated session/work
   directory for every run.
4. Before viewing results, freeze one semantic hierarchy and the primary
   endpoint: `delegate review` inclusive token share. Also report absolute
   target tokens and operation share.
5. Predeclare an actually unaffected responsibility as a placebo and retain an
   objective correctness/task-success outcome as a noninferiority veto.
   Reduced review mass counts as optimization only if the deliverable remains
   correct.
6. For every profile, require source-measure total = folded-stack total =
   stock-pprof total, and compare A/B within pairs.

Three pairs are a pilot/case-study demonstration, not a powered general claim.
The existing history supplies no paired variance from which to justify a final
sample size. The honest next step after the pilot is to estimate paired
variance, set the smallest meaningful share reduction, and power a
preregistered confirmatory run. A broad RQ-level claim would also need more
than one task so that “same task” control does not become “one-task”
overfitting.

## Could not verify

- Which exact `CLAUDE.md` and skill revisions each historical agent process
  actually loaded.
- Whether historical agents reloaded instructions after a file changed.
- A matched task, prompt, model/configuration, and repository snapshot on both
  sides of any relevant change.
- An independent success/quality outcome for the 42 records.
- That every `delegate review` annotation denotes redundant rather than
  required review.
- Statistical power for a future matched experiment; no paired treatment
  variance exists on disk.

