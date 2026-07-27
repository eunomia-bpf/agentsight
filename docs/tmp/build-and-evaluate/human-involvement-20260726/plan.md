# Experiment Plan: RQ1--RQ4 Corpus Characterization — Human Involvement

## Research Question
- RQ exactly as written in the active study contract: the study asks whether
  days of Agent activity become durable, reuse- and validation-associated
  artifact progress, and how rework and continuity evolve across session
  boundaries. This analysis does not rename or answer an additional RQ; it
  measures human involvement as a corpus property and possible confound for
  the existing RQ1--RQ4 observations.
- Specific uncertainty tested here: how much observable human direction,
  follow-up, interruption, and elapsed response latency accompanies the 551
  project-attributed session memberships in the final RQ1--RQ4 corpus, and how
  those quantities
  co-occur descriptively with action, mutation, reuse, and validation records.
- Why the answer matters: the six repositories are author-associated natural
  cases. Without this measurement, descriptions of "Agent activity" can be
  misread as fully autonomous behavior even when humans repeatedly steer it.

## Paper-Value Admission
- Planned role: supporting.
- Largest credible paper story this experiment could unlock: an honest,
  source-grounded characterization of the autonomy/steering regime represented
  by the natural corpus, suitable for interpreting its scope and confounds.
- Strongest reviewer reject argument or load-bearing uncertainty addressed:
  apparent Agent behavior may substantially encode one author's interactive
  work schedule and steering rather than autonomous long-horizon execution.
- Independent evidence added beyond existing runs and published results:
  prior analyses count prompts only as tool-call segmentation metadata; none
  reconstructs human messages, message volume, explicit interruptions, elapsed
  reply gaps, or project-by-vendor guidance density from the native records.
- Why the result is not tautological, already settled, or dominated: the
  projection contains only repeated prompt previews, so the requested message
  and timing distributions require an independent source-native reconstruction.
- Paper decision if positive: describe the corpus as mixed-initiative and make
  author steering a first-class scope/confound statement.
- Paper decision if contradictory, mixed, or inconclusive: if most sessions are
  startup-only, describe the corpus as substantially goal-launched but retain
  project/vendor heterogeneity; if source coverage or event semantics prevent
  recovery, report the dimension as unmeasured rather than infer autonomy.
- Best alternative experiment and why this one has higher decision value:
  another artifact/tool-call analysis would deepen dimensions already measured
  but would not resolve who is directing the observed work.

## Expected And Alternative Outcomes
- Current expected answer: involvement is heterogeneous, with both one-prompt
  autonomous runs and heavily steered multi-turn sessions; author-associated
  projects and vendor storage conventions will differ materially.
- Strongest competing explanation: repeated `prompt_index` values or native
  synthetic messages could falsely inflate human turns, while long idle gaps
  could falsely inflate apparent human attention.
- Result that would contradict the expectation: nearly all source-verified
  sessions contain exactly one substantive human message and negligible
  explicit interruption across every supported project/vendor stratum.

## Published Precedent And Real Assets
- Closest published protocol: none is needed for this deterministic corpus
  audit. The analysis follows ordinary conversational-log measurement and
  reports source-native counts rather than introducing a benchmark score.
- Official system/model/data/benchmark/tool and version: the final RQ1--RQ4
  exports at `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq1-raw/`,
  their embedded `source_file` paths under `~/.claude`, `~/.codex`, and
  `~/.gemini`, Python 3, pandas, NumPy, SciPy, and Matplotlib.
- What is reused: the admitted 551 session memberships, 181,303 projected
  tool-action rows, timestamps, project/vendor/session IDs, action targets, and
  the existing 13,906 mutation rows with reuse and validation outcomes.
- Necessary deviations or custom glue: a read-only vendor adapter uses
  Claude `type=user`, Codex `event_msg/user_message`, and Gemini
  `messages[].type=user` as authoritative human records. Codex
  `response_item/message(role=user)` is fallback-only when a file has no
  `event_msg/user_message`; Claude queue/last-prompt records are not human
  records. Source-native prompt IDs plus timestamps deduplicate records.
  A full-run extreme-value audit showed that Codex projection
  `source_role=user` also covers nested subagent rollouts. The frozen repair
  therefore treats native `session_meta.thread_source=subagent` (or nested
  `source.subagent` metadata) as authoritative and excludes those files from
  human-message, assistant-message, interruption, approval, and timing
  reconstruction. Their projected actions remain in the Agent-action
  denominator.
  System/developer records, tool results, context summaries, local-command
  wrappers, synthetic interruption notices, and every subagent source are
  excluded. Assistant conversational messages similarly use Claude assistant
  text, Codex `event_msg/agent_message` with response-item fallback, and
  non-empty Gemini messages. No message text is stored in outputs.

## Comparison
- Proposed system or method: deterministic source-native reconstruction joined
  to the fixed event projection by `(project, session_id, source_file)` and to
  mutation outcomes by `(project, session_id, vendor)`.
- Main baselines and the competing position each represents: none; this is a
  descriptive measurement, not a method-superiority experiment.
- Why each main baseline needs a matched run instead of citation alone: N/A.
- Controls or ablations, labeled separately: (1) reconcile `.json` and
  `.json.gz` payload hashes and read only one copy; (2) show projected event
  rows and unique `(project, source_file, source_call_id)` calls separately;
  (3) compare native human-message counts with projected distinct
  `(source_stream_id, prompt_index)` pairs on the matching human-bearing source without
  treating either as truth for the other; (4) manually inspect one real
  human-bearing session per vendor during preflight; (5) give both 551
  project-attributed session rows and 550 unique-session-ID totals.
- Conclusion if each main baseline matches or wins: N/A.
- Information, tuning, and compute fairness: every included root session is
  parsed with one frozen vendor rule set; no semantic LLM classification and no
  per-project text-dependent tuning.
- Split or leakage rule when relevant: high/low groups are defined within
  project × vendor strata. No held-out dataset is read or used.

## Workloads And Metrics
- Real workloads or tasks: all six repository-direct natural cases and all
  vendors present in the fixed RQ1--RQ4 event exports.
- Primary metrics:
  1. Per root session: substantive user messages, follow-up messages, character
     count, approximate word-like tokens, assistant conversational messages,
     user share of conversational messages, projected Agent actions, and
     actions per user message.
  2. Startup-only (`1` substantive user message) versus guided (`>=2`) session
     proportions, with `0`/unreadable sessions kept separate.
  3. Follow-up frequency and explicit source-native abort/interruption markers
     as separate quantities; around each eligible follow-up, the exact next
     action's tool-family and path-set change relative to the preceding action
     in the same native human-bearing source file and source stream. Missing path sets
     remain a separate coverage state.
  4. First-human-message hour and weekday in `America/Vancouver`; for each
     closed inter-prompt interval, elapsed Agent activity envelope from a human
     prompt to the last observable Agent activity, and the post-activity
     inactive gap from that activity to the next human prompt. Neither is
     interpreted as CPU time, proven Agent waiting, or human cognitive
     attention.
  5. Visible Agent-to-human question tools, explicit source-native
     approval-request/response record types, and permission-policy
     configuration as separate quantities with vendor coverage.
  6. Agent actions, raw mutation count, mutations per 100 Agent actions, and
     non-delete eligible reuse/validation outcome distributions for
     startup-only versus guided sessions and for within-stratum bottom/top
     guidance-density thirds. Observed, competing, and censored outcomes all
     remain in the denominator; zero-mutation sessions remain via a left join.
     These are descriptive co-occurrences only. Guidance density is frozen as
     follow-up human messages per 100 projected Agent actions.
- Correctness check or ground truth: exact source record types and timestamps
  are authoritative for messages; the event projection is authoritative for
  admitted membership and Agent actions; `rq1-mutations.csv` is authoritative
  for mutation/reuse/validation outcomes. Preflight records expected and
  excluded native record classes without saving private message text.
- Repetitions, seeds, and uncertainty: deterministic, no seed. Report counts,
  proportions, median, quartiles, p90, and full per-session rows rather than
  only means. No population-generalizing confidence intervals are claimed.
- Cost estimate when material: local parsing and plotting only.

## Planned Runs
| Run group | Role | Workload | System/method | Repetitions | Decision consequence |
|---|---|---|---|---:|---|
| preflight | correctness control | one included root session per vendor | source-native adapters + event join | 1 | confirms real schemas and exclusion rules |
| full corpus | measurement | six projects, all admitted session memberships | frozen deterministic analysis | 1 | produces the human-involvement profile |
| group contrast | descriptive control | eligible project × vendor strata | startup/guided and within-stratum density groups | 1 | bounds outcome co-occurrence without causal language |

## Execution
- Authoritative command or workflow:
  `python3 docs/tmp/build-and-evaluate/human-involvement-20260726/analyze_human_involvement.py`
- Real preflight case:
  `python3 docs/tmp/build-and-evaluate/human-involvement-20260726/analyze_human_involvement.py --preflight`
- Full completion rule: every one of the 551 project-attributed session
  memberships (550 unique projected `session_id` values) has a
  coverage row; all readable native candidate files are parsed; totals reconcile to
  181,303 event rows and 13,906 mutation rows; the complete 6 × 3
  project/vendor grid remains explicit, including empty/small cells. The run
  regenerates `session_metrics.csv`, `user_messages.csv`,
  `followup_transitions.csv`, `interaction_intervals.csv`,
  `human_distributions.csv`, `schedule_hour.csv`,
  `schedule_weekday.csv`, `involvement_outcomes.csv`,
  `profile_summary.csv`, `native_coverage.csv`, `approval_visibility.csv`,
  `manifest.json`, `report.md`, and all figures. Unsupported metrics are
  explicit.
- Raw-result path:
  `docs/tmp/build-and-evaluate/human-involvement-20260726/`
- Checkpoint or recovery approach: deterministic outputs are overwritten only
  inside this experiment directory; rerun the single command after repair.

## Interpretation
- Positive result: human steering is common or dense in at least some supported
  strata, so the corpus is accurately described as mixed-initiative and human
  involvement is a plausible confound for cross-session behavior.
- Negative or contradictory result: startup-only operation dominates broadly,
  supporting a more autonomous-use characterization for this corpus while
  retaining the author-associated sampling limitation.
- Mixed or inconclusive result: emphasize distributions and per-stratum
  differences; do not summarize the corpus with one autonomy label.
- Target paper figure or table: stacked startup/guided proportions and
  distributions of user-message/action density plus a compact descriptive
  outcome contrast; this task does not edit `docs/paper/`.

## Reproducibility Notes
- Software and data versions: recorded in `manifest.json`, including input
  hashes and package versions.
- Config and seed notes: timezone is fixed to `America/Vancouver`; word-like
  tokens are Latin/digit runs plus individual Han characters; guidance-density
  groups use within-project × vendor rank thirds with middle observations
  excluded.
- Known deviations: post-activity gaps are observable inactive envelopes, not
  human cognitive attention, typing time, or proof that an Agent was waiting.
  Immediate path/tool change is
  not a semantic goal-change label. Assistant-message granularity is
  vendor-dependent, so user conversational-turn share is reported but not used
  as a cross-vendor autonomy score. Project × vendor strata with fewer than ten
  sessions expose individual values but receive no directional interpretation.
  The planned projection-role filter was strengthened after the first full
  run's extreme-value audit exposed Codex subagent rollouts mislabeled as
  user-role sources; the source-native metadata rule above is the resulting
  systematic corpus-wide repair.
  Per the explicit task scope, this run does
  not update `docs/evaluation.md`, does not edit `docs/paper/`, performs no Git
  operation, and does not access the held-out RQ7 directory.
