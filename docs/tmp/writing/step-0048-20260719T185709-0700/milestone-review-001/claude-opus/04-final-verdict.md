# 04 — Final Verdict, Drift Audit, and Routing

- **Reviewer:** Independent Claude Opus milestone reviewer (AgentProf, AAAI-27 main track)
- **Report written:** 2026-07-19, step `step-0048-20260719T185709-0700`, `milestone-review-001`
- **Stage:** Step 4 of 4, written after `01-blind-full-read.md`, `02-external-search.md`, and `03-full-reread-assessment.md`.
- **Inputs read for this report only:** `docs/user-instruction.md` (complete, 251 lines); `docs/idea-story.md` (complete, 634 lines, Initial Narrative through E009 and the Invariants); `docs/evaluation.md` (RQ Frontier table and admitted RQ1 evidence, lines 1–120); `docs/background-related-work.md` (complete verified-closest-work sections, lines 1–199). Current paper state as already read in Steps 1–3.
- **Compliance:** No prior reviewer report was read at any point in this review. No file outside my four assigned report files was modified. No Git command was run. No subagent was used. The `/iter-review-critique` command does not exist in this environment (verified in Step 1 against `~/.claude/commands/`, the repo `skills/` tree, and a home-wide glob); the four-step protocol in the invoking instruction was executed as specified.

---

## 1. The finding that reframes this entire review

I wrote Reports 01–03 without reading any project document, and independently concluded that the paper's most serious problems were:

1. no positioning against Pivot Tracing / process-mining trace segmentation / OLAP;
2. degenerate controls that do not represent the real baseline family;
3. no demonstrated downstream consequence, against a bar set by cited neighbors;
4. contradictory evidence about whether hierarchy alone suffices for attribution.

I then read `docs/background-related-work.md`. **It already contains all four, verified, in writing, dated today.** Verbatim from that file:

> "[Pivot Tracing] dynamically selects, filters, and groups metrics across causally related component events. **It makes independent lineage fidelity, not only mass conservation, a required RQ1 comparison.**"

> "[Activity Mining by Global Trace Segmentation] and [Flexible Activity Trees] discover higher-level activities and hierarchical abstractions from low-level event logs. **They are serious RQ3 mechanism/baseline precedents; always-cut, action-change, and phase-change controls do not represent this family.**"

> "[CHIEF] combines hierarchical agent traces with counterfactual reasoning and **reports that hierarchy alone is insufficient for failure attribution.** [Signals] uses blinded expert judgments and matched sample budgets… Together they **motivate a consequential same-input comparison rather than another visualization or grouping-only metric.**"

> "[AgentDiagnose] … **establishes a published analysis-to-intervention evidence pattern stronger than visualization alone.**"

The frontier document verifies roughly 25 closest-work items with precise novelty-limiting consequences for each. **The paper's Related Work cites 11 and reflects almost none of these consequences.** The paper uses exactly the controls the frontier document says are unrepresentative. It omits Pivot Tracing entirely. It omits CHIEF, whose finding directly challenges D3.

**Diagnosis: this is not an authors-unaware-of-the-literature problem. It is a synchronization failure between the research pipeline's frontier documents and the paper.**

That reframing matters in both directions:

- **Favorably:** the intellectual work is largely done. Most of what I would demand as a reviewer already exists in the project's own documents and needs to be transcribed into the paper. My Step 03 effort estimates were too pessimistic.
- **Unfavorably:** an AAAI reviewer reads only the paper. They will conclude the authors do not know Pivot Tracing or process-mining segmentation exist, and will reject on that basis. The authors' own documents prove that conclusion wrong — and the reviewer will never see them. **The paper is currently underselling its own scholarship.**

---

## 2. Drift audit

### 2.1 Thesis — no drift

Paper (abstract, Introduction ¶5, Conclusion): *"Agent observability needs profiling, not only debugging."*
`idea-story.md` E005 and `background-related-work.md` fixed contract: identical sentence, verbatim.

**Verdict: exact match. No paraphrase, no narrowing, no broadening.** E005's requirement that the sentence match the untouched submodule baseline is satisfied in all three paper locations. I found no instance anywhere in `main.tex` of the thesis being restated in the narrower "cross-run recurrence and measured effects" form that E005 explicitly rejects. This invariant is being held correctly.

### 2.2 Four RQs — no drift in the questions

Paper: RQ1 resource attribution, RQ2 problem correspondence, RQ3 tag accuracy, RQ4 profiling cost. `user-instruction.md` line 126 and `idea-story.md` E006 fix exactly these four. **Exact match.** I make no recommendation to change them and did not consider doing so.

### 2.3 Registered hypotheses — **substantial drift, all in the direction of under-testing**

This is where the audit finds real problems. `idea-story.md` §"Fixed Research Questions And Hypotheses" registers a positive hypothesis per RQ. Comparing each against what the paper actually tests:

| RQ | Registered hypothesis clause | Paper's test | Status |
|---|---|---|---|
| RQ1 | "reunite recurring responsibility fragmented across executions and improve attribution of independently recorded token, time, tool, process, file, network… measures" | B³ partition agreement vs human stages | ⚠ Partition agreement is a proxy; improved *measure attribution* not directly tested |
| RQ1 | "while preserving source lineage and mass" | RQ1a scoped controls + exact totals | ✓ Tested |
| RQ2 | "concentrate… failures, unsafe effects, redundant work, or task boundaries" | MAP on 3 benchmarks | ✓ Tested |
| RQ2 | "versus **flat, per-session, native, and raw-action** views" | **raw-action only** | ✗ **3 of 4 registered baselines dropped** |
| RQ2 | "**reduces analyst inspection**" | MAP only | ✗ **Not tested in the paper** (but see §3) |
| RQ2 | "without using target labels" | asserted "target-blind" | ⚠ **Unverifiable — estimation scope unstated (BL3)** |
| RQ3 | "recovers accurate, stable task/action identities plus phase/group structure and boundaries" | 5 measurements, standard metrics | ✓ Tested |
| RQ3 | "**on unseen agents and task families**" | session-held-out within corpora; paper admits both are development sets | ✗ **Registered generalization clause not tested** |
| RQ3 | "**without materially corrupting attribution**" | — | ✗ **Never tested** |
| RQ4 | "practical predictable scaling" | Table 4, monotonic, slope | ✓ Tested |
| RQ4 | "**cached field derivation makes repeated profile queries substantially cheaper than initial construction and repeated raw-trace review**" | — | ✗ **Not in the paper** |

**Seven registered clauses are untested or unverifiable in the paper.** None of this is RQ drift in the prohibited sense — the questions are intact and no hypothesis has been weakened in writing. It is *evidentiary* drift: the paper claims positive answers to four RQs while leaving substantial parts of each registered hypothesis unexercised.

Two of these are worth singling out because they are also the answers to my two harshest criticisms:

- **RQ3's "without materially corrupting attribution"** is precisely the tag-error-propagation experiment I called the highest value-per-effort missing item in Report 03 §9. It is **not** an optional strengthening. It is a registered clause of the fixed hypothesis. **Reclassified: missing requirement.**
- **RQ4's caching clause** is precisely the defense against my BL4 cost objection. The intended story — *tagging is paid once, profiles are queried many times, so amortized cost is low* — is registered, the caching mechanism is implemented (Implementation §Field derivation mentions grammar-constrained decoding "and caching"), and `evaluation.md` records that "R160 separately supports the shared cache mechanism **on one predecessor fixed-input pair**." One pair is not a result, and it does not reach the paper. **Running this properly likely converts BL4 from a blocker into a selling point.**

---

## 3. Evidence that exists in the pipeline but is absent from the paper

Reading `evaluation.md` surfaced completed measurements the paper does not report. Some would help the paper; some are validity caveats whose omission is a soundness problem.

### 3.1 Helpful evidence omitted

- **Step 0019 downstream reader study.** `evaluation.md` RQ2 row: "The fixed-reader comparison separately improves selected-positive recall on 5/6 tasks and precision on 4/6 versus session." `idea-story.md` adds: a fixed rank-hidden Qwen3.6-27B reader, three of five query-aware top-five groups, six public-data tasks, five cyclic positions, 66 presentations. **This is the closest thing the project has to link-7 (profile → decision) evidence, and it is not in the paper.** Given that Graphectory (+23.5% resolve rate) and Hodoscope (6–23× review reduction) set the actionability bar among the paper's own cited neighbors, omitting the project's only decision-relevant experiment is a significant self-inflicted wound.
- **R251 association-beyond-session.** Prompt tags retain 8.419% weighted behavior information beyond session, versus a 1.903% permutation null (p = 0.0010, 1,000 permutations). This is a clean, significance-tested result that directly supports D2 (tags carry information not reducible to session membership) and it is not in the paper.
- **R224 grouping ablation.** Mixed-bucket weight falls 90.4% → 84.4% → 36.7% → 0% across no-semantic / session-only / prompt-only / session+prompt projections over identical observations, all conserving 183,714 units. This is a quantitative demonstration that semantic fields separate what session structure alone does not — and it is exactly the evidence Figure 2 gestures at qualitatively.

### 3.2 Validity caveats omitted — this is the more serious category

- **R225 (`evaluation.md`): "Prompt spans may contain idle/user wait time and are not true active-runtime measurements."** The paper's `time` flame graph (Figure 2, middle panel) and its "7/10 top prompt categories, Spearman ρ = 0.623, network 8th by time but 93rd by tokens" claim **all rest on this measure**, and the caveat appears nowhere in the paper. A `time` profile whose durations include human think-time is not a runtime profile, and the tokens-vs-time divergence the paper highlights could be substantially an artifact of idle time. **This must be disclosed.**
- **Step 0036 (`evaluation.md` RQ2): "HINT grouping also propagates nonzero support to 76.54% of clean operations versus 0.742% atomic."** Semantic grouping assigns nonzero problem-support to three-quarters of clean operations. That is a large false-positive cost, it is directly material to how a developer would experience the profile, and it is absent from the paper.
- **Step 0036: "Atomic nevertheless wins both AgentProcessBench measurements."** The paper reports the local-only column but frames it as post-hoc mechanism analysis; the internal record is blunter.
- **R170: "records a dirty working-tree provenance boundary."** Not disclosed.
- **Step 0007: the capture used a research `agentsight 0.2.37` path "because the PATH-installed 0.2.43 binary no longer exposes the R114 `--agent-comm` interface… This result therefore does not validate AgentSight 0.2.43 specifically."** The paper cites version 0.2.37 (accurate) but does not note that the shipping version cannot reproduce the experiment. That is a reproducibility caveat a reviewer would want.
- **R170 used a Qwen2.5-3B tagger; RQ3 used Qwen3.6-27B.** This **resolves** the 3B-vs-27B contradiction I raised in Report 01 M1 and Report 03 MJ5: they are two different taggers in two different roles. The paper is not wrong, it is **conflating** — Implementation describes the 3B production path, Evaluation reports the 27B standalone path, and nothing tells the reader they are different. **Downgraded from "internal inconsistency" to "must be disambiguated in one sentence."**

### 3.3 On the "no negative results" instruction

`user-instruction.md` line 126 states the paper should not include negative results and the story should be as attractive as possible; line 130 adds that experiments should be changed to try to prove the hypothesis rather than weakening the hypothesis to fit failed experiments. `idea-story.md` E006 encodes this.

I want to be precise, because this instruction is legitimate and my findings above must not be read as contradicting it.

**Excluding a failed intermediate experiment from the paper's story is normal editorial curation and is entirely the author's prerogative.** The failed information-gain inducer (Steps 0017–0018), the rejected sequence-local NPMI refinement (Step 0025), and the Hodoscope recursion boundary are correctly kept as research history rather than paper content. I have no objection to any of that, and E006's disposition is sound.

**Omitting a validity caveat about a measurement that *is* in the paper is a different act.** R225's idle-time caveat qualifies a figure and a statistic the paper reports; the 76.54% support-propagation figure qualifies a result the paper claims. These are not negative results being excluded from a story — they are properties of reported results. Omitting them makes the reported claims unsound rather than making the story attractive.

**These two goals are compatible, and `user-instruction.md` line 130 already points at the resolution:** change the experiment to prove the hypothesis. The way to remove the idle-time caveat from the paper is to measure active runtime, not to stay silent about it. The way to remove the 76.54% figure is to fix or bound the support propagation, not to omit it. The way to make phase-only-beats-recurrence stop being awkward is an untouched population where recurrence wins — and RQ3 already shows recurrence beating phase-change 0.680 vs 0.334, a very large margin, so this is a winnable fight.

**I therefore recommend no deletion of any honest statement currently in the paper, and no weakening of any claim.** Every recommendation below adds evidence or adds positioning. That is the direction `user-instruction.md` line 13 demands ("find more evidence, not a smaller claim") and I agree with it on the merits.

---

## 4. Verdict

### 4.1 Recommendation

**Reject for AAAI-27 main track in the current form**, with an unusually clear and achievable path to acceptance. In AAAI's scale this is a **3 (Reject, but would not argue strongly against acceptance)** trending to **4 (Borderline)** if BL3 alone were resolved.

**Confidence in this assessment of the paper as submitted: 0.85.** The blocking items are matters of record — an unstated protocol, an excluded cost term, an uncited prior-art family, an unevaluated conjunction — not matters of taste.

**Confidence in my effort estimate for the fixes: 0.6**, revised upward from Report 03. The frontier documents show the intellectual work is largely complete; I have not seen the experiment harness, so I cannot estimate re-run costs precisely.

**Would I champion this paper after the blockers close? Yes.** The gap is real, the system exists, the sources verify, the arithmetic is sound, and the honesty is above field norms. This is a paper with a defect list, not a paper with a hollow core.

### 4.2 What decides it

Three of the five blockers are **transcription or specification**, not science:

- **BL5 (positioning):** the content exists in `background-related-work.md`. Transcribe it.
- **BL3 (RQ2 protocol):** one paragraph stating the estimation scope and split. The registered hypothesis says "without using target labels," so the intended design is almost certainly sound; it simply is not written down.
- **BL4 (cost):** run the registered RQ4 caching clause and report per-backend end-to-end cost.

Two require experiments, both of which are registered hypothesis clauses rather than reviewer inventions:

- **BL2 (untouched population):** RQ3's registered "on unseen agents and task families."
- **BL1 (conjunction):** one profile where D1, D2, and D3 are simultaneously active.

---

## 5. Ranked findings

### Blockers — the paper cannot be accepted without these

| # | Finding | Class | Where the fix already exists |
|---|---|---|---|
| **BL1** | D1 evaluated only on the 20-task eBPF suite with *predeclared* tags; D2/D3 evaluated only on trajectory-log corpora with no system effects. **The claimed conjunction is never evaluated anywhere.** | Missing requirement | New: one profile with all three active |
| **BL2** | No untouched population for the induction algorithm; paper admits CodeTraceBench and OSWorld-Human are both development sets. Violates RQ3's registered "on unseen agents and task families." | Missing requirement | OpenClawBench (31,264 trajectories, span targets, verified Report 02 §D3); or any of the 15 already-adapted families |
| **BL3** | RQ2 group-score estimation scope unstated → the primary comparison cannot be validated. Compounded by unspecified "judge votes"/"localizer hits" provenance. | Missing requirement (specification) | Author knowledge; one paragraph |
| **BL4** | Abstract/Intro/Conclusion cost claim (1.17 s) excludes field/tag generation, the dominant term (~3–4 orders of magnitude, Report 02 §A6). RQ4's registered caching clause is untested. | Missing requirement | Registered RQ4 hypothesis; caching implemented; R160 is a starting point |
| **BL5** | Model contribution not positioned against OLAP roll-up, process-mining event abstraction, Canopy, or Pivot Tracing — **all of which the authors' own frontier document already verifies.** | Missing requirement (positioning) | `background-related-work.md`, verbatim |

### Majors

| # | Finding |
|---|---|
| MJ1 | No named prior system as a baseline anywhere; conjunction novelty untested against systems holding 2 of 3 conjuncts. TraceProbe is the most conspicuous omission; HINTBench and TraceElephant ship baselines the paper does not report. |
| MJ2 | Abstract/Intro/Conclusion omit that phase-only (0.654) beats the flagship constructor (0.649) on RQ1's population. `evaluation.md` is blunter than the paper: "statistically indistinguishable." |
| MJ3 | **RQ3's registered "without materially corrupting attribution" clause is untested.** Tag-error propagation into profile conclusions, at a measured 0.498 action macro-F1. *Reclassified from optional to required by the drift audit.* |
| MJ4 | Induction algorithm unablated: NPMI vs raw frequency, k-means vs Otsu/percentile, two-cutoff refinement. Frontier doc names the missing baseline family (activity mining / trace segmentation); Report 02 §C4 names the missing statistics (AV, BE, nVBE, DLG). |
| MJ5 | **Validity caveats omitted from the paper**: R225 idle/user-wait time in span durations (underpins Figure 2 middle panel and ρ = 0.623); 76.54% support propagation to clean operations on HINTBench; R170 dirty working tree; AgentSight 0.2.43 cannot reproduce RQ1a. |
| MJ6 | CodeTraceBench 405/4,316 = 9.4%, framed as "all 405"; reconstructability filter's selectivity, mechanism, and correlates undisclosed; no stratification on the benchmark's 5-model dimension. |
| MJ7 | Figure 2 is a session-stratified **debugging** view by the paper's own definition; its largest token bucket is the semantically vacuous `prompt:continue`; its `files` panel achieves essentially no folding above the prompt level. |
| MJ8 | No demonstrated developer consequence in the paper, against a bar set by four items in the authors' own frontier doc (TraceGraph, AgentDiagnose, Agent Mentor, Hodoscope) — **while the project's own Step 0019 reader study sits unused.** |
| MJ9 | RQ2 drops 3 of 4 registered comparison views (flat, per-session, native); RQ1's Table 1 has them, so the asymmetry is unexplained. |
| MJ10 | OSWorld-Human construct validity: an efficiency/latency benchmark's annotations used as semantic-responsibility ground truth, on the population where the rule was designed. |
| MJ11 | Uncited despite verification: Pivot Tracing, CHIEF, activity-mining/trace-segmentation family, AgentDiagnose, Agent Mentor, ARIA, AgentGraph, Signals, Differential Flame Graphs, domain-specific program profiling; plus `agentlens2026`, `procbench2026`, `agentlocate2026` present in `.bib` with today's date and never cited. |
| MJ12 | MP-Bench's critique of single-target attribution evaluation (Report 02 §D1) unaddressed, though cited. CHIEF's "hierarchy alone is insufficient for failure attribution" is direct contradictory evidence to D3 and is verified in the frontier doc but absent from the paper. |
| MJ13 | Background understates the tooling landscape: flame-graph views over agent spans with token weights are shipped product features (Report 02 §B3). |

### Minors

Table 4 lacks the raw-action RSS column though the prose cites a 6.0 MiB delta; RQ4's R² = 0.9997 is fit over five points one of which is the sum of the other four; "93rd" prompt category contradicts "low-cardinality tags"; RQ3's 3,978/6,010 OSWorld-Human fraction unstated; no error bars or significance tests in Tables 3–4; 3B/27B tagger roles need one disambiguating sentence; anonymity risk from `project:agentsight` as Figure 2's root frame and the `agentpprof 0.2.37` string; "9.8K-line" as a contribution measure; no artifact statement in the compiled PDF; Chinese comments retained in `main.tex`; 13 underfull hboxes.

---

## 6. Strongest accept case

A reviewer arguing to accept would say: the paper identifies a real gap that survived a deliberate 12-search falsification attempt — no prior system combines cross-run semantic folding of agent operations, kernel-linked system effects, and pprof-compatible output (Report 02 §E2). It builds a real, versioned system and evaluates it on **complete** public populations rather than convenience subsets, with matched controls that hold operations and signal fixed and vary only the grouping. Its central RQ2 result — semantic grouping beats matched raw-action grouping on three independent complete benchmarks with paired-bootstrap CIs excluding zero on all three — is a genuine, non-trivial, correctly-bounded finding about the grouping layer. Every one of 14 independent arithmetic re-derivations reproduces exactly, including non-obvious ones. All 11 primary sources verify. Metric selection is exemplary: correct primary citations throughout, explicit tie handling, and distinct metrics for distinct output types. RQ3's protocol includes session-held-out CV, matched controls, a supervised upper reference, and a leakage sensitivity check that most submissions omit. And the paper volunteers its own limitations — that its constructor was selected on its evaluation corpora, that a trivial baseline matches it on one population, that its best RQ2 configuration is a refinement rather than a replacement — at a level of candor well above field norms.

## 7. Strongest reject case

A reviewer arguing to reject would say: contribution 1 is a data model that is OLAP roll-up on a fact table, positioned against neither OLAP, nor process mining, nor Canopy, nor Pivot Tracing — and the authors' own literature file proves they know Pivot Tracing and trace segmentation are load-bearing, so the paper reads as either unaware or evasive. Contribution 2 is an unablated NPMI-plus-k-means segmenter that is a member of a named family (accessor variety, boundary entropy, nVBE, DLG) with no comparison to any member, that has **no untouched evaluation population anywhere**, and that loses to a one-line deterministic rule on the only population where that rule was measured. Contribution 3's headline cost number excludes the dominant cost term by three to four orders of magnitude while the abstract states it unqualified. RQ2's primary comparison cannot be validated because the estimation scope is unstated. No named prior system is a baseline anywhere. The claimed novelty is a *conjunction*, and no experiment, table, or figure ever has all three conjuncts simultaneously active. The showcase figure is, by the paper's own definition, a debugging view whose largest semantic bucket is `prompt:continue` and whose file panel does not fold. And the paper's central `time` measurement includes human idle time, which the authors recorded internally and did not disclose.

---

## 8. Routing

Precise assignment of each blocker and major, using the project's own pipeline vocabulary (`idea-story.md` invariant: "`iter-refine-ideas` proposes; the root records a disposition; the WRITE gate alone changes the paper").

### To WRITE (no new experiments; content already exists)

| Item | Action | Source |
|---|---|---|
| BL5, MJ11, MJ12, MJ13 | Transcribe the verified closest-work families and their novelty-limiting consequences into Related Work and Background. Add Pivot Tracing, CHIEF, activity mining / Flexible Activity Trees, OLAP roll-up (Gray et al. 1997), Canopy, AgentDiagnose, Agent Mentor, ARIA, AgentGraph, Signals, Differential Flame Graphs, domain-specific profiling, plus the three uncited `.bib` entries. State plainly that the projection algebra is standard and that the contribution is *dimension derivation under natural-language and missing-hierarchy conditions*. **Do not narrow the contribution** — this defends it. | `background-related-work.md` |
| BL3 | State RQ2's group-score estimation scope, the train/test split, and what "judge votes" and "localizer hits" are. | Author knowledge |
| MJ2 | One clause in the abstract acknowledging phase-only parity, matching the body's existing honest statement. | Table 1 |
| MJ5 | Disclose R225's idle/user-wait caveat, the 76.54% support propagation, R170's provenance boundary, and the AgentSight 0.2.43 reproduction boundary. | `evaluation.md` |
| MJ6 | State the CodeTraceBench denominator (405 of 4,316), the reconstructability filter's mechanism, and whether it correlates with length/agent/model. | `evaluation.md` + Report 02 §A1 |
| MJ8 (partial) | Add the Step 0019 fixed-reader result and R251's permutation-tested association as reported evidence. | `evaluation.md`, `idea-story.md` |
| MJ9 | Either add flat/per-session/native to RQ2's comparison or state why RQ1's ladder is not repeated there. | Registered RQ2 hypothesis |
| Minors | Table 4 RSS column; drop R²; disambiguate 3B vs 27B taggers; state 3,978/6,010; rename Figure 2's root frame for anonymity. | — |

### To EXPERIMENT (registered hypothesis clauses, one RQ each)

| Item | Experiment | RQ | Registered? |
|---|---|---|---|
| **BL1** | One profile over the eBPF-captured suite with **induced** rather than predeclared tags, so D1+D2+D3 are simultaneously active. Report the same conservation and attribution checks. | RQ1 | Implied by the conjunction claim |
| **BL2** | Run the frozen constructor once on an untouched family. OpenClawBench is the strongest candidate (31,264 trajectories, span-localization targets, released taxonomy). Pre-register fields; single run; no tuning. | RQ3 | ✓ "on unseen agents and task families" |
| **BL4** | Per-backend end-to-end cost table (regex / 3B / 27B): first-construction cost including tagging, then repeated-query cost with warm cache, versus repeated raw-trace review. | RQ4 | ✓ registered caching clause |
| **MJ3** | Tag-noise sensitivity: inject label error at the measured rates (0.498 action, 0.695 task-family), re-fold, report top-k frame rank stability and RQ1/RQ2 degradation curves. | RQ3 | ✓ "without materially corrupting attribution" |
| **MJ4** | Three cheap ablations on the existing transition table: NPMI vs raw frequency; k-means vs Otsu/percentile; two-cutoff refinement on/off. Plus AV / BE / nVBE / DLG as baselines. | RQ3 | Implied by frontier doc's baseline-family note |
| **MJ1** | At least one named prior grouping system (TraceProbe preferred) on RQ1c or RQ3 inputs; report HINTBench's and TraceElephant's published baselines. | RQ1/RQ2/RQ3 | Implied by frontier doc |

`user-instruction.md` line 21 requires real benchmarks and complete runs and prefers citable designs over bespoke scripts. **Every experiment above satisfies this**: OpenClawBench, TraceProbe, and the AV/BE/nVBE/DLG family are all published, citable, and released. None requires a hand-written harness.

### To ROOT (disposition only — not for WRITE to decide)

- Whether to report the Step 0019 reader study given its "higher work on 4/6 tasks" component. My recommendation as a reviewer: **report it.** Its inclusion answers the field's actionability bar; its mixed component is far less damaging than having no downstream evidence at all, and the paper already demonstrates it can report mixed results well.
- Whether BL1's conjunction experiment justifies a new capture run.

---

## 9. Higher-value evaluation proposal

If only one new experiment can be run, I would not run any of the six above. I would run this, because it is the only design that tests the **thesis** rather than a component, and it subsumes BL1 and MJ8.

**Proposal: the cross-run budget-policy experiment.**

*Question it answers:* can a population-level profile support a decision that no per-run diagnostic view can support? That is the operational content of "profiling, not only debugging," and nothing in the paper currently tests it.

*Design.* Split a real trajectory corpus into a reference half and a held-out half. From the **reference half only**, build a semantic profile and derive a mechanical policy — e.g., "cap or route the top-*k* semantic frames by token weight," with *k* fixed in advance. Derive a matched policy from each control view: per-run local diagnostic score, per-session, raw-action, and flat. Apply every policy unchanged to the **held-out half** and measure realized token/time savings and task-outcome change.

*Why it is higher value than the alternatives.*
- It is the **only** design that can produce evidence a per-run view *structurally cannot* produce, because the policy must transfer across runs. Every current experiment compares groupings of the same signal; this one compares what you can *do* with them.
- It restores the four registered RQ2 baselines (flat, per-session, native, raw-action) that the paper dropped, satisfying MJ9 as a side effect.
- It matches the evidence pattern the authors' own frontier document identifies as the bar: TraceGraph's resolve-rate gain, AgentDiagnose's 13%-retention downstream improvement, Agent Mentor's repeated-run accuracy, and Signals' matched-budget blinded protocol. `background-related-work.md` already says these "motivate a consequential same-input comparison rather than another visualization or grouping-only metric." This is that comparison.
- It directly serves `user-instruction.md` lines 13 and 130: it makes the claim **larger** and seeks evidence for the strong hypothesis rather than retreating to a smaller one.
- If it succeeds, MJ8 closes, BL1 closes (the profile must carry real weights end to end), the thesis gains its first direct support, and the abstract gets a number no competing system reports.
- If it fails, it fails informatively: it would show that the profile's structure does not transfer, which is a genuine boundary on the mechanism — and per E006 and `user-instruction.md` line 130, that redirects the mechanism, not the RQ or the thesis.

*Cost control.* It reuses existing corpora, existing folding, and existing weights. The only new component is the policy-application harness, and the design is citable against Signals' matched-budget protocol and AgentDiagnose's filtering-to-downstream pattern.

---

## 10. Uncertainty and what would change my verdict

**Would move me toward accept:**
- BL3 resolved as Reading A with a clean split. RQ2 then becomes a genuine population-level transfer result and the paper's best evidence — currently undersold by its own ambiguity. **This single clarification is worth more than any new experiment.**
- BL5 transcribed from `background-related-work.md`. Converts the most likely reject trigger into a demonstration of scholarship.
- BL2 returning a positive result on an untouched family.

**Would move me toward firmer reject:**
- BL3 resolving as Reading B (within-trajectory circularity).
- BL2 returning a substantially worse result on an untouched family, indicating the constructor was overfit to two development corpora.
- Discovery that the eBPF path cannot support induced tags at all, making BL1 unfixable and the conjunction claim unsupportable in principle.

**Residual uncertainty in my own assessment:**
- My 27B tagging-throughput estimate is order-of-magnitude only.
- I did not verify OSWorld-Human's released group-annotation semantics at the data level (MJ10); this needs a check I could not perform read-only.
- I read `evaluation.md` lines 1–120 and `background-related-work.md` lines 1–199, not those files in full. Additional omitted-evidence or omitted-caveat items may exist beyond §3.
- I have not seen the experiment harness, so my effort estimates carry real error.
- **Where I was wrong against the paper:** I recorded the 3B-vs-27B discrepancy as an internal inconsistency in Reports 01 and 03. The drift audit shows they are two different taggers in two legitimate roles. The paper needs one disambiguating sentence, not a correction. I also over-weighted the authors' apparent unfamiliarity with prior art; the frontier document shows the opposite, and my Report 03 effort estimates were correspondingly too pessimistic.

**On the fixed thesis and the four RQs:** I did not recommend, and do not recommend, altering either. Every finding in this review is discharged by adding evidence or adding positioning. Where the paper's evidence falls short of a registered hypothesis, my recommendation is to run the registered experiment — not to weaken the hypothesis. That is both the correct scientific response and what `idea-story.md`'s invariants and `user-instruction.md` lines 13, 17, and 130 require.

## 11. Next action

Route BL5, BL3, MJ2, MJ5, MJ6, MJ8-partial, MJ9, and the minors to a single WRITE pass — none requires new experiments, and the content for most of them already exists in `background-related-work.md` and `evaluation.md`. Route BL1, BL2, BL4, MJ3, and MJ4 to EXPERIMENT as one-RQ-each plans, with BL2 (untouched population) sequenced first because it is the load-bearing generalization claim and every other result is interpreted in its light. Hold the §9 budget-policy proposal for root disposition as the highest-value single experiment if capacity allows only one.

**Reports 01–04 are complete. No file outside this reviewer's four assigned reports was created or modified.**
