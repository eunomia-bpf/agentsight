# Round 8: Terminology and Claim Tone

## Node identity

- **Started:** 2026-07-12 00:21:39 -0700
- **Cycle/Gate:** `cycle-0001-20260711T164850-0700` / `WRITE_GATE`
- **Parent:** `round-7-language-word.md` (`PASS`)
- **Entry paper:** 9 pages; seven content pages; References begins page 8
- **Entry invariants:** four fixed RQs; three target contributions; 59 citation commands

## Objective and method

A fresh read-only subagent was instructed to invoke
`check-terminology-infoflow` in terminology-infoflow scope and then
`paper-writing-style` for claim-tone mechanics. It reads the complete current
paper, builds a concept inventory, audits compound-term frequencies and the
core-concept budget, checks reviewer recognition and definition order, finds
synonym/overloading drift and hardcoded system names, and distinguishes
self-attacking prose from scientific scope. Honest negative results,
unanswered evidence, scientific falsifiers, implementation status, and all
scope-bearing hedges are protected.

## Findings, decisions, and completion evidence

**Completed:** 2026-07-12T00:56:30-07:00.  
**Final verdict:** `PASS` after five repair-and-reread passes.  
**Final independent counts:** zero Must-fix, zero Should-fix, zero Consider.

### Inputs and source-fidelity anchors

The reviewer and main agent reread the complete `docs/paper/main.tex`, not only
the Round 8 diff, and reread `docs/user-instruction.md` before every convergence
pass. The main agent also checked the current PDF/log, the experiment-plan
definition of the target comparator family, and the R251 implementation and raw
result used by the behavior-entropy paragraph:

- `docs/tmp/cycle-0001-20260711T164850-0700/01-experiment-gate/loop-rq2-01/experiment-plan.md`;
- `docs/visexp/r251_behavior_tag_alignment.py`;
- `docs/visexp/out/behavior-tag-alignment-r251/behavior-tag-alignment-r251.json`.

R251 defines behavior as the sanitized process/effect/status tuple, uses folded
system-effect count as weight, reports the conditional entropy reduction
`100[H_w(B|S)-H_w(B|S,P)]/H_w(B|S)`, expands integer weights into repeated
observations, and shuffles prompt tags only within a fixed session. The paper now
states that exact statistic and its inference boundary rather than inventing a
generic “behavior entropy” description.

### Independent findings and convergence history

The first full-paper review found eight Must-fix, eleven Should-fix, and one
Consider issue. The highest-impact defects were hardcoded system names,
confusion between query-selectable accounting views and the query-independent
semantic tree, candidate tags described as validated identities, an undefined
operation-stack/scope-constructor relation, notation used before definition,
an unclear RQ2 caption, undefined RQ3 metrics, and drift among trajectory, run,
session, span, policy, hierarchy, and bundle-control terms.

The main agent applied all Must-fix and Should-fix findings and evaluated the
single Consider item. Repeated complete-paper rereads then returned the following
counts:

| Reread | Must-fix | Should-fix | Consider | Main remaining issue |
|---|---:|---:|---:|---|
| Initial review | 8 | 11 | 1 | candidate/stable identity, tree/view, metrics, captions |
| Convergence 1 | 5 | 8 | 0 | central unit, undefined comparator names, R251 statistic |
| Convergence 2 | 3 | 6 | 0 | cross-run definition, identity applicability, exact entropy formula |
| Convergence 3 | 0 | 4 | 0 | G2 boundary and small canonical-term drift |
| Convergence 4 | 0 | 2 | 0 | trajectory/span wording and representation terminology |
| Final confirmation | 0 | 0 | 0 | `PASS` |

No pass was accepted merely because compilation succeeded or a search returned
zero known strings. Each convergence pass reread the complete paper and was
allowed to find new regressions.

### Applied terminology and claim-tone repairs

1. **System and unit vocabulary.** All active prose uses `\sys`; the literal
   system name remains only in the macro definition. The paper now defines a
   trajectory as one recorded execution, reserves cross-run for aggregation,
   transfer, or learned priors spanning trajectories, and uses session/span only
   as source fields. Trajectory-local is the canonical name for a within-execution
   candidate or control. SDBL's source artifact remains a multi-agent log, while
   this paper calls the adapted comparator a current-trajectory scope.
2. **Candidate versus stable identity.** The implemented pipeline propagates
   candidate semantic tags. A tag becomes a stable semantic identity only after
   a vocabulary frozen before evaluation transfers unchanged to held-out
   families. The architecture, G1--G3, formal model, implementation boundary,
   RQ3, Related Work, and Conclusion now use that distinction consistently.
3. **Tree, view, and navigation.** Query-selectable field/filter/measure views
   remain an analyst-facing accounting interface. The target semantic tree and
   identity are frozen and query-independent; only risk and navigation priority
   are query-conditioned. The operation stack is explicitly the path produced
   by a scope constructor, and direct/inclusive mass notation is defined before
   use.
4. **Comparator representations.** The paper no longer alternates among
   undefined “native/fixed/matched/current-log structures.” It defines one
   eight-entry comparator roster: flat risk ranking, development-selected
   contiguous windows, fixed-field rollups, benchmark-native execution trees,
   semantic leaves, 100 shape-matched random hierarchies, SDBL-style
   current-trajectory scopes, and the target semantic tree. Only semantic leaves
   and the semantic tree receive paired trajectory-local/stable identity
   versions; SDBL uses trajectory-local candidates; the other controls use no
   induced identity. The central falsifier compares complete representations
   under matched information, content, and end-to-end cost.
5. **Evaluation controls and metrics.** Pointwise ranking, whole-scope
   navigation, and bundle-emulation control are now distinct and stable names.
   The caption defines AP, delta AP, R@30%, and paired intervals. V-measure is
   clustering agreement; boundary F1 compares adjacent predicted/native phase
   transitions and applies only to ordered datasets. RSS and LLM are expanded at
   first use. RQ1 defines mixed-weight percentage and the R251 conditional
   entropy statistic exactly.
6. **Plain reader language.** One-off project compounds such as
   `diagnostic-work`, `release-pipeline`, `semantic-axis`,
   `declared-category separation`, `scope-identity coverage`, and
   `reusable-scope thesis` were replaced by plain phrases. RQ2 keeps the parallel
   noun-phrase title `Correspondence to Real Problems`, which preserves the
   section convention while using reader language.
7. **Claim tone.** Defensive “straw man,” “not a reduced scope,” and
   “preserve rather than narrow” asides were removed. Honest negative evidence,
   implementation status, unanswered RQs, falsifying conditions, leakage
   boundaries, and scope-bearing qualifiers remain because they delimit the
   science rather than apologize for it.

### Alternatives evaluated and rejected

- The reviewer suggested a smaller four-structure vocabulary as one possible
  repair. That would omit fixed-window, fixed-field, leaf-only, matched-random,
  and SDBL controls required by the ambitious identity-by-structure claim. The
  paper instead keeps the complete eight-comparator roster and states identity
  applicability explicitly.
- The negative AgentRx/TELBench leaf result and all RQ1--RQ4 evidence obligations
  were not removed or softened. The target contribution remains recurring stable
  semantic scopes that can outperform a trajectory's own execution tree as a
  diagnostic index.
- The central falsifier was not converted into optimistic prose. Only the
  rhetorically self-diminishing word “only” was removed from the surviving
  engineering-substrate clause.

### Preservation and compilation checks

- Four paper-level RQs remain, with their scientific meaning unchanged.
- Three target contributions remain.
- Citation-command count remains 59.
- The abstract remains one paragraph with nine role sentences.
- No quantitative value was changed. The only new number in the comparator
  description, 100 matched random hierarchies, is copied from the reviewed RQ2
  experiment plan rather than invented during writing.
- `make -C docs/paper` succeeds under the AAAI-27 style with no undefined
  citations, undefined references, or LaTeX errors.
- The built PDF is letter size and currently has ten pages. The body still
  occupies part of page eight, so the seven-page AAAI body budget is not yet
  satisfied. This is explicitly routed to Round 9 flow/layout compression and
  is not hidden by deleting a claim, RQ, baseline, or evidence obligation.
- Two layout warnings remain: a 47.41556-point overfull architecture figure and
  a 0.99261-point overfull RQ2 table. They are Round 9 visual/layout work, not
  terminology evidence.
- `docs/agentpprof-paper/` remains internally clean at
  `7f80c433c9555317a2aa45a78d0ff93518f4c12c`; this round did not modify it or
  perform any Git operation.

## Scientific impact and next action

Round 8 did not change the hypothesis, RQ set, conclusion claim, or admitted
evidence. It made the target experiment reconstructable and removed vocabulary
that could let a reviewer confuse candidate tags, stable identity, structure,
navigation, or accounting views. The research tree and canonical scientific
frontier therefore do not change.

The next node is Round 9 language flow and polish. A fresh read-only reviewer
must check topic/stress position, old-to-new threading, paragraph transitions,
and register across the complete paper. The main agent must also recover the
AAAI body page budget and eliminate the two overfull boxes without deleting or
narrowing scientific content.
