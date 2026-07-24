# Independent Full-Paper Review — AgentProf: Semantic Profiling for AI Agents

**Reviewer role:** Independent senior reviewer, AAAI 2027 (cross-domain: systems + ML evaluation).
**Artifact reviewed:** `docs/paper/main.tex` (complete), cross-checked against
`references.bib` and the three independent result reviews for Steps 0072 (RQ2),
0075 (RQ4), and 0076 (RQ1 matched contrast).
**Scope:** whole-paper scientific review. I did not edit the paper, code, or any
repository file other than this report, and I ran no Git.

---

## 1. Paper and thesis summary

The paper argues a single fixed thesis: **"Agent observability needs profiling,
not only debugging."** Agent trajectories interleave an intent layer (prompts,
LLM calls, tool calls) and a system-effects layer, and teams accumulate many
such trajectories, but they lack two structures that classical profilers get for
free: stable semantic identity (natural language gives no shared identifier for
recurring intent) and a runtime call hierarchy for attribution. The paper's
answer is a **semantic operation stack model**: an ordered source tree of native
nodes carrying additive measures (D1); recursive, backend-neutral annotations
that assign shared short semantic names covering every node (D2); and a
deterministic stack `agent → session-op → prompt-op → recursive ops → LLM/tool
evidence` whose equal prefixes fold across runs while raw session/prompt IDs
survive as pprof labels rather than aggregation-fragmenting frames (D3). The
system, **AgentProf**, is an offline Rust CLI that emits exactly one
pprof-compatible profile and adds no bespoke frontend — a discipline the paper
holds to throughout, consistent with the product-boundary invariant.

Four fixed RQs are evaluated: RQ1 (does semantic profiling improve resource
attribution?), RQ2 (does profiler output correspond to real problems?), RQ3 (how
accurately do automatic backends recover operation structure?), RQ4 (what does
constructing a profile cost?). The thesis sentence appears verbatim in the
abstract, introduction ¶5, and conclusion, and the four RQs are not silently
rewritten.

## 2. Strongest contributions

1. **A genuinely correct reframing of profiling for agents.** The
   `(φ, σ, w_r)` formalism — predicate selects nodes, composed stack supplies
   the frame path, one additive weight selects a resource, folding merges equal
   stacks — is simple, principled, and non-trivial. The key invariant (changing
   `r` changes only widths, never boundaries or names, because `A` and `E` are
   fixed) is exactly the property that makes multi-resource attribution
   meaningful, and it is both stated and empirically exercised (RQ1's count-vs-
   token divergence; RQ4's replayed count/token profiles).

2. **A backend-neutral annotation contract instead of one privileged model.**
   The same `tag/parent/next` interval contract is written by an Agent backend,
   a plain LLM, deterministic rules, change-point methods, and a label-free NPMI
   + 1-D k-means recurrence inducer. This is the difference between a
   contribution and a prompt: the algorithm's validity does not rest on one
   inference service, and the recurrence backend is fully specified
   (NPMI formula, k=2 init at min/max, tie-to-lower-center, midpoint cutoff,
   detail-continuity can only remove boundaries).

3. **Unusually disciplined evidence hygiene.** The paper repeatedly refuses the
   overclaim: RQ1 is labeled post-hoc organization evidence, not discovery
   accuracy; RQ2 openly reports a statistical tie with the information-matched
   baseline; RQ3 separates literal labels, partitions, and boundaries rather
   than fusing them into one bespoke score; RQ4 refuses to call the 54.36-min
   artifact envelope model latency. This restraint is a real strength for a
   venue that punishes overclaiming.

## 3. Per-RQ evidence and baseline assessment

### RQ1 — Multi-resource attribution (Case Study 1, +Step-0076 review)
**Assessment: convincing as a bounded case; correctly labeled.**
The claim tested is the *necessary consequence* — a fixed hierarchy exposes
materially different bottlenecks when the resource weight changes — on a repeated
real Git-deployment task (489 ops, 4,558,192 tokens). By count Terminus2 is
56.24% and OpenHands 43.76%; by tokens OpenHands is 86.62%; the
`diagnose authentication` subtree is 21.47% of ops but 46.15% of tokens. The
Step-0076 independent review recomputed all of these exactly (105 ops /
2,103,587 tokens; largest coarse branch 39.42%; 102 of 105 are generic `run`
mixed with 97 unrelated ops) and confirmed the six matched-organization profiles
conserve mass and load in stock pprof. Critically, the paper states plainly that
because the responsibility was selected from the prior semantic case, "this
matched projection establishes an organization difference, not independent
discovery accuracy." This is exactly the labeling the task asks for, and it is
honored. The residual weakness is intrinsic: RQ1 is *one* task family, so it
establishes a capability, not a rate — which the paper concedes.

### RQ2 — Problem correspondence (Table 1, +Step-0072 review)
**Assessment: the baseline treatment is a genuine strength; the headline
statistical claim is honestly stated but the abstract/intro presentation
undercuts it (see Must-Fix 1).**
The benchmark-native process judge / trajectory localizer is correctly treated
as a strong *direct reader*, not a straw man — the TraceElephant localizer even
reads the full trace and reference answer before predicting. The candidate ranks
lexicographically by `(direct diagnostic, Agent+Evidence group score)`, so the
profile can only break exact diagnostic ties, never override a strict ordering.
Both claims the task flags are supported and honest:
- **Direct+AgentProf > Direct-only**: +.031 [.024,.039], +.107 [.093,.120],
  +.117 [.088,.148] — all-positive, matching the Step-0072 recomputation
  (+.0311, +.1069, +.1168) to three decimals.
- **Direct+AgentProf ≈ Direct+Raw+Evidence**: candidate-minus-baseline intervals
  [-.0003,.0029], [-.0116,.0103], [-.0247,.0280] all contain zero, and the paper
  explicitly declines to claim the semantic prefix ranks better than raw action
  when both retain identical source evidence, attributing the gain to
  group/evidence refinement rather than the semantic prefix. This is the correct
  and admirable reading.

The design is leakage-audited (rank vectors exist before labels load; source
packets carry no target fields; both direct-first methods preserve strict local
order). MAP/AP with paired stratified/clustered bootstrap over the *complete*
populations (614/400/220 target-bearing, 522 zero-positive) is the right metric
family. This is a strong RQ2 for a top venue — precisely because it does not
overclaim.

### RQ3 — Automatic operation structure (Tables 2–3, +body)
**Assessment: standard metrics, adequate and appropriately trivial+nontrivial
baselines, distinct outputs kept distinct.**
The paper uses B³ (partition), exact adjacent-boundary P/R/F1 (boundaries),
V-measure (permutation-invariant partitions), and macro-F1/accuracy (literal
labels), all cited to standard sources, and refuses to conflate them. On the
complete 405-trajectory CodeTraceBench population the Agent backend reaches
0.704 B³ F1 (+0.0414 over recurrence [0.0214,0.0606]; +0.163 over raw action)
and 0.394 boundary F1, with mass conserved (20,866 ops / 494,862,929 tokens) —
consistent with the Step-0075 quality figures. On OSWorld-Human the baseline set
is well-chosen: supervised Naive Bayes (0.739/0.816), label-free recurrence
(0.680/0.786), reference-calibrated recurrence (0.734/0.801, honestly flagged as
using group labels the default does not), plus three trivial controls
(always-boundary, action-change, phase-change). The literal-taxonomy invariant
is respected: the `Locate` leakage check is enumerated (39 AutoCodeRover inputs;
excluding them leaves 0.490/0.622, comparison unchanged). Task-family
(0.695 macro-F1 vs 0.044 majority) and action (0.498 vs 0.061, gain 0.437
[0.380,0.494]) both dominate the majority control. This is a complete,
non-heuristic-soup RQ3.

### RQ4 — Profiling cost (Table 4, +Step-0075 review)
**Assessment: the four-way separation the task asks for is done correctly.**
The paper cleanly separates (a) fixed-input replay (semantic vs raw on identical
inputs: union 1.16 s vs 0.97 s, +19.6% time, +1.14% RSS; slope 0.0418 ms/op,
R²=0.9997), (b) deterministic first-construction components on the full 405
sessions (source-packet 501.64 s + assembly/repair/canonicalization 3.54 s +
replay 1.17 s = 506.35 s), (c) the historical artifact-time envelope (54.36 min,
explicitly mutable filesystem metadata mixing inference/dispatch/idle/writing,
neither model time nor a lower bound), and (d) unavailable model/provider
inference timing, which it refuses to estimate. The Step-0075 review verified
byte-identical determinism, stock-pprof loadability, mass conservation, and the
median arithmetic, and independently caught and corrected a raw cost/quality row
mismatch (now "Coarse action," B³ 0.473 / boundary 0.267). The framing "1.17 s
is replay latency, not annotation latency" is exactly right.

## 4. Novelty and related-work assessment

The positioning is coherent and the delta is real but incremental. Against
observability platforms (LangSmith/Insights, Langfuse, Datadog Patterns, OTel
Profiles, NeMo) the distinguishing combination is: recursive *variable-depth*
semantic responsibility over a *preserved* source-call tree, with *conserved
additive* measures, emitted as *standard pprof*. Against the 2026 cross-run
neighbors (TraceProbe resource-aware process profiles, Graphectory process
graphs, Hodoscope behavior-distribution monitoring, TraceGraph shared decision
landscapes) the paper claims the delta of replayable multi-resource boundaries
and covered native evidence under one folded profile. That delta is defensible
and not a blocker on its own — the pprof-reuse discipline (no bespoke frontend)
is itself a clean scoping decision. The novelty risk is not omission but
*proximity*: TraceProbe and Graphectory in particular sound close, and the
strength of the "we recursively annotate shared responsibility, they don't"
claim depends entirely on those papers being real and accurately characterized.
The bib entries are well-formed (full author lists, arXiv IDs, DOIs), but per
this repository's own citation-verification policy, the neighbor claims should be
PDF-verified before camera-ready, because a mischaracterized close neighbor is
the one thing here that could become a reviewer blocker.

## 5. Correctness, reproducibility, and presentation findings

- **Core-number consistency is high.** Every headline figure I cross-checked
  (RQ1 percentages, RQ3 B³/boundary/macro-F1, RQ4 timings and mass) reconciles
  with the three independent result reviews and across abstract/intro/body/
  conclusion. The thesis sentence is verbatim in all three required locations.
- **Reproducibility is unusually strong** for a submission: byte-identical
  determinism, stock `go tool pprof` loadability, SHA-256 digests, and mass
  conservation are all independently reconfirmed in the evidence reports.
- **The one real presentation defect** (Must-Fix 1): the abstract and
  introduction ¶7 tell the RQ2 story with vocabulary and numbers that never
  appear in the RQ2 subsection or Table 1. "Target-blind **declared semantic
  hierarchy**" and the MAP transitions "0.773→0.789, 0.281→0.452, 0.121→0.230"
  (abstract lines 60–67; intro lines 191–195) are in no table; the RQ2 body and
  Table 1 use "Direct+AgentProf / Direct+Raw+Evidence / Direct-only /
  AgentProf-only" and the values .894/.893/.863/.791 etc. The abstract sentence
  "**Canonical renaming alone improves HINT; its paired intervals include zero
  on AgentProcess and Trace**" (lines 65–66) has no counterpart anywhere in the
  body and is not reconstructable from Table 1 (e.g., AgentProf-only HINT .432
  is *below* declared .452, so "improves HINT" cannot be read off the table). A
  reader cannot map the paper's central RQ2 claim to its evidence.
- **Minor:** intro ¶7 calls the 405 trajectories "failed," while the RQ3 body
  says only "reconstructable"; harmonize. "Qwen3.6-27B" is an unusual model name
  a reviewer may query — fine if the cited model card is real.

## 6. Top strengths

1. Simple, principled `(φ, σ, w_r)` model with the width-only-changes invariant
   that makes multi-resource attribution well-defined.
2. Backend-neutral contract exercised by five real backends — not a
   single-prompt system.
3. Best-in-class evidence hygiene: RQ1 post-hoc labeling, RQ2 honest tie, RQ3
   distinct-output separation, RQ4 four-way cost separation, all independently
   re-verified.
4. Product discipline: exactly one pprof artifact, reusing stock tooling.

## 7. Must-fix issues (submission-blocking)

1. **Make the abstract/introduction RQ2 claims traceable to Table 1 and the RQ2
   body.** Either (a) add the standalone MAP rows the abstract/intro cite —
   raw-action-only (0.773/0.281/0.121) and declared/AgentProf-only-hierarchy
   (0.789/0.452/0.230) — to a table and adopt one consistent method vocabulary
   ("declared semantic hierarchy" vs the body's "AgentProf-only"/"Agent+
   Evidence"), or (b) rewrite the abstract/intro to state the RQ2 result in the
   exact terms the body proves (Direct+AgentProf raises MAP over Direct-only by
   .031/.107/.117; statistically tied with the information-matched Direct+Raw+
   Evidence). In particular, **delete or fully ground the sentence "Canonical
   renaming alone improves HINT; its paired intervals include zero on
   AgentProcess and Trace"** — as written it is an undefined, body-unsupported
   claim in the abstract. This is the one defect that blocks a clean submission.

## 8. Should-fix issues

1. **PDF-verify and, if needed, sharpen the delta against TraceProbe and
   Graphectory** (the two closest 2026 neighbors), since the novelty claim rests
   on their exact scope.
2. **Harmonize "failed" vs "reconstructable"** for the 405 CodeTraceBench
   trajectories across intro ¶7 and RQ3.
3. **Surface RQ1's single-task scope earlier.** RQ1's subsection is honest, but a
   reader arriving from the contributions list may over-read one Git task; one
   clause in the contributions bullet ("a repeated-task case study") would
   inoculate against reviewer overreaction.
4. **State the RQ2 development caveat in the abstract's neighborhood.** The body
   correctly notes the local-first rule and fixed source-only paths were
   developed on these populations (adaptive-mechanism, not untouched
   generalization); a one-clause echo where the abstract reports RQ2 would
   pre-empt a "trained on the test populations" objection.
5. **Add a one-line pointer to where the 12 RQ2 method×workload MAP values live**
   (only 4 of them are in Table 1), so the Step-0072-verified full grid is
   discoverable.

## 9. Verdict

**Weak Accept.** Confidence: **medium-high.**

The thesis is intact and the RQs are unrewritten; the model is simple and
principled rather than heuristic soup; the metrics are standard; the baselines
(especially RQ2's strong direct reader and information-matched refinement) are
appropriate and honestly reported; and every core number I checked reconciles
with three independent recomputations. The paper's evidence is imperfect — RQ1 is
one post-hoc task, and RQ2 does not beat the information-matched baseline — but
both limits are stated plainly and neither is grounds to narrow the thesis or the
RQs. What holds this back from a clear Accept is the single, fixable, but
genuinely submission-blocking traceability defect in how the abstract and
introduction present RQ2 (Must-Fix 1), plus the unverified proximity of two 2026
neighbors. Fix the RQ2 framing and verify those neighbors and this is a solid
Accept-track paper.

## 10. Single highest-value next action

**Rewrite the abstract and introduction ¶7 RQ2 sentences to use exactly the
method names and numbers proven in Table 1 and the RQ2 body, and delete the
unsupported "Canonical renaming alone improves HINT…" sentence** (Must-Fix 1).
This one edit converts the paper's most central claim from
reader-unverifiable to fully grounded, and it depends on no new experiment.
