# Step 0048 Heterogeneous Review Synthesis

**Completed:** 2026-07-19 19:37:31 -0700
**Models:** Grok 4.5 and Claude Opus 4.8
**Paper:** `docs/paper/main.tex` and the compiled `docs/paper/main.pdf`
**Root decision:** accept four bounded writing corrections; admit no new experiment from these reviews

## Review coverage

Both reviewers independently completed the four-stage full-paper protocol:

1. blind full-paper read;
2. external search and primary-source inspection;
3. full-paper reread and scientific assessment;
4. author-intent/drift audit and final verdict.

Each reviewer produced all four required Markdown reports. Grok returned
**Reject** with confidence 0.82. Claude returned **Reject / AAAI score 3,
trending 4** with confidence 0.85. The agreement is therefore a real warning
about how an unprimed reviewer can perceive the paper. It is not, by itself,
evidence that every proposed experiment is scientifically fair or belongs to
the fixed four-RQ contract.

## Corrections accepted into the paper

### 1. RQ2 estimation scope

Claude's BL3 is valid as a writing ambiguity. The Step 0036 result review
already establishes that the benchmark predictions, profiles, scores, and
grouping precede evaluation-label loading. The paper now states that both views
use identical operations and the same precomputed benchmark judge/localizer
predictions, and that predictions, group scores, profiles, fields, and scoring
rules are fixed before human/scorer target labels are loaded.

This is a protocol clarification, not a new freeze contract and not a change to
RQ2, its hypothesis, its experiment, or its result.

### 2. Span-time interpretation

Claude's R225 caveat is valid. The paper now says that span time is elapsed time,
not active CPU time, and may include idle or user wait. The positive result that
time and token weights expose different rankings remains unchanged.

### 3. Evaluation and CLI tagger roles

Claude correctly reclassified its own 3B/27B concern as an ambiguity rather
than a contradiction. The RQ3 text now explicitly distinguishes the fixed
evaluation-only Qwen3.6-27B backend from the 3B CLI backend described in the
implementation.

### 4. Pivot Tracing positioning

Both reviews identified Pivot Tracing as a strong systems precedent. Its
primary publication was verified. The paper now cites it for dynamically
selecting and grouping measurements across causally related events. To preserve
the nine-page AAAI paper, the active citation set drops redundant product and
workshop references while retaining them in the canonical literature map.

## Experiment proposals not admitted

### Grok B1: same-claim process/phase and hierarchical-rollup baselines

**Disposition: reject the proposed experiment.** Step 0046 already performed
the required availability audit on the exact RQ2 corpora:

- HINTBench has a natural phase field;
- AgentProcessBench has only a project-derived semantic phase component;
- TraceElephant has no published phase field;
- no published information-matched process/phase representation is available
  across all three workloads.

The proposed TF-IDF hierarchy and TraceProbe/Graphectory-inspired arms would be
new local designs or external-system reimplementations, not published baselines
on identical inputs. They would violate the user's preference for real,
citable, reusable evaluation rather than another handmade foil. A HINT-only
phase comparison cannot replace the complete three-workload matched result.

The existing experiment already reports the strongest common retained views:
raw action, atomic/local evidence, session, and semantic grouping. The paper is
also explicit that recurrence does not universally dominate declared phase.

### Grok B3 and Claude MJ8: profile-to-intervention or reader outcome

**Disposition: reject as a blocker.** A cross-run budget policy or reader study
would add a new decision policy, new intervention semantics, and a new outcome
contract beyond the fixed attribution, problem-correspondence, tag-accuracy,
and construction-cost RQs. The proposed harness would be project-designed, not
a released benchmark protocol. The existing Step 0019 fixed-reader metric also
uses the custom top-three/inspection-budget protocol that the user explicitly
forbids from the paper. These may become future work only when a published,
reusable protocol and fixed external outcome are available.

### Claude BL1: every contribution component on one population

**Disposition: reject as a mandatory experiment.** The paper evaluates source
lineage and conserved heterogeneous effects in RQ1, semantic organization and
problem ranking in RQ1/RQ2, tag/group construction in RQ3, and construction
cost in RQ4. Scientific decomposition does not require every backend and every
data source to be activated in one dataset. The full system and Figure 2
already carry agent operations and additive token/time/file measures through
selectable stacks. Requiring an automatically induced tagger on the eBPF suite
would test a new backend combination, not invalidate the model or current
component claims.

### Claude BL2: new untouched constructor population

**Disposition: optional strengthening, not admitted now.** The paper expressly
labels CodeTraceBench and OSWorld-Human as post-hoc support and limits its claims
to named populations and tag sets. The user's fixed RQ3 is tag accuracy, not a
universal unseen-agent guarantee. Adding OpenClawBench solely because a reviewer
requested another held-out family would reopen a closed RQ and encourage the
same benchmark-chasing loop that earlier trajectory audits identified as
wasteful. It becomes admissible only if a released annotation directly tests a
paper-level unresolved claim using the frozen constructor without a custom
harness.

### Claude BL4: end-to-end tagging and cache experiment

**Disposition: reject as a blocker.** RQ4 and the paper explicitly define the
1.17-second result as fixed-field offline profile construction and explicitly
exclude field/tag generation, capture, adaptation, and live-agent overhead.
R160 remains bounded evidence for the shared cache mechanism. The paper does
not present 1.17 seconds as universal end-to-end LLM tagging latency. A new
3B/27B timing matrix would answer a different deployment question.

### MP-Bench graded nDCG

**Disposition: strongest future RQ2 protocol, not currently executable without
leakage.** MP-Bench provides 289 failed executions with three expert
perspectives and uses standard graded nDCG. Its released repository contains
annotations and upstream logs but no fixed target-blind localizer predictions
that AgentProf can group. Scoring semantic groups from the gold expert labels
would leak the target. Reopen this option only when a released prediction path
or another fixed external signal exists; do not invent a localizer merely to
claim benchmark coverage.

## Writing requests not accepted

- Do not add phase parity to the abstract. Table 1 and the RQ1 prose already
  report it and explicitly reject universal recurrence dominance; the abstract
  states only the true recurrence-versus-raw result.
- Do not add the 76.54% HINT propagation statistic to the paper as a new main
  result. Semantic and raw grouping have identical clean-support flags; the
  paper's RQ2 claim is scoped to target-bearing problem ranking, not universal
  safety precision.
- Do not add dirty-working-tree, Git hash, current AgentSight-version, packet,
  or freezing requirements. They are repository/provenance concerns, not
  scientific gates, and the user explicitly rejected reproducibility
  bureaucracy.
- Do not add every item in the canonical literature map to a nine-page paper.
  Pivot Tracing and MP-Bench are the highest-value active additions. AgentLens,
  ProcBench, AgentLocate, activity mining, OLAP, CHIEF, and product precedents
  remain documented and verified for future revision or rebuttal.
- Do not publish custom Recall@20%, top-three reader, or project-specific
  permutation metrics as primary paper evidence. The active evaluation keeps
  ordinary B-cubed, boundary F1, V-measure, macro-F1, accuracy, AP, and MAP.

## Scientific conclusion

The reviews found no arithmetic invalidation, target leakage, thesis drift, RQ
replacement, or source-fidelity defect. Their shared reject signal comes from
raising the desired novelty bar to a same-claim external-system comparison and
a downstream intervention. Those are reasonable aspirations, but the concrete
experiments proposed here are not fair, published, information-matched tests on
the current populations.

The correct current iteration is therefore:

1. retain the large fixed thesis, four fixed RQs, and existing positive results;
2. land the four source-backed clarifications above;
3. retain MP-Bench nDCG as the best next evaluation design when a target-blind
   external prediction path becomes available;
4. do not switch benchmarks or invent another baseline merely to eliminate all
   reviewer objections.

The milestone remains reviewable and scientifically defensible, but it should
not be represented as unanimous model acceptance: both independent reviewers
still recommend rejection at the AAAI main-track bar.
