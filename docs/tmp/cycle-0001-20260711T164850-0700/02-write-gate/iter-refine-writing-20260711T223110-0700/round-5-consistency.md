# Round 5: Paper Consistency

## Node identity

- **Started:** 2026-07-11 23:30:43 -0700
- **Completed:** 2026-07-11 23:47:24 -0700
- **Cycle/Gate:** `cycle-0001-20260711T164850-0700` / `WRITE_GATE`
- **Parent:** `round-4-abstract-intro-rebuild.md`
- **Entry paper:** 9 pages; seven content pages; References begins page 8
- **Entry invariants:** four fixed RQs; three target contributions; 59 citation commands

## Objective and method

A fresh read-only subagent was instructed to invoke
`check-terminology-infoflow` in paper-consistency scope, read the complete
paper and its paper-consistency reference, and check architecture, workflow,
interfaces, mechanism/status, claims, numbers, cross-references, figures,
tables, goals, contributions, RQs, and evidence alignment. It may inspect
directly linked repository results to verify an anchor but may not edit the
paper or run Git. The RQ meanings, quantitative values, and three ambitious
target contributions are read-only in this writing round.

## Findings, decisions, and completion evidence

### Independent findings

The reviewer returned `REVISE` with six Must-fix findings:

1. the 15-family, 47,590-operation mapping corpus was grammatically
   conflated with the additional AgentRx and TELBench held-out families;
2. the Conclusion omitted `significantly` even though both AP point
   estimates are numerically above prevalence and their paired intervals
   include zero;
3. Setup appeared to hold numeric priors fixed across representations even
   though prefix-keyed prior values cannot be shared across different node
   identities;
4. navigator notation used undefined `L(n)` and `id(n)`;
5. the proposed frozen identity path was written as current ingestion;
6. five unused tables under `docs/paper/figures/` retained a superseded RQ
   scheme and positive RQ2 claims.

The Should-fix findings concerned the missing frozen-scope-tree stage in the
architecture figure, an unsupported `production-development` corpus label,
the unreferenced RQ2 table, a vague RQ1 permutation statistic, and lowercase
CLI titles in the flamegraph rasters. Consider items concerned RQ2/RQ3
dependency order, official dataset names in the RQ3 plot, and an imprecise
identity-section cross-reference.

The reviewer otherwise traced and confirmed the paper's current numeric
anchors, including 325/183,714; 36.7%/84.4%; 2,903; all RQ2 table values;
13,265; seven-of-nine and six joint RQ3 thresholds; and the separated RQ4
timing/tagger counts. It found no drift in the four fixed RQs or three target
contributions.

### Applied Must-fix changes

- **Experimental Setup:** now states that 15 mapping/coverage families total
  47,590 operations, while AgentRx contributes a separate 73 trajectories /
  3,265 operations and TELBench a separate 1,000 cases / 11,934 spans. This
  preserves both the mapping denominator and held-out status.
- **Fair comparison:** Setup now fixes prior feature sources, training data,
  estimator capacity, localizer, and budgets. Each representation fits its
  prefix-specific prior values on the same development data because node
  identities differ; every policy remains frozen before target scoring.
- **Navigator mechanism:** the prose now says `In the target pipeline` and
  uses prospective voice. It defines `L(n)` as inclusive operation membership
  and `id(n)` as the complete stable scope-prefix identity.
- **Conclusion:** added the required `significantly` qualifier in English and
  Chinese without changing either AP value or interval.
- **Stale paper tables:** removed the five unreferenced copied tables
  `claim-gate-table.tex`, `evidence-path-table.tex`,
  `experiment-role-table.tex`, `task-verdict-table.tex`, and `case-table.tex`
  from the current `docs/paper/figures/` workspace. They were not included by
  `main.tex`; their authoritative originals remain untouched in the protected
  submodule. Removing them prevents an old RQ scheme from reentering the
  submission bundle.

### Applied Should-fix changes

- The architecture now draws the proposed path as frozen cross-run identity
  -> frozen cross-run scope tree -> cost-bounded navigator -> selected whole
  scopes. Candidate/trace-local trees remain a fair comparison input. The
  caption lists achieved and proposed stages explicitly, and the diagram was
  rearranged to keep its labels readable within one column.
- Replaced `production-development corpus` with the supported `multi-month
  development corpus`.
- Added an explicit prose reference to Table `tab:localization` before its RQ2
  interpretation.
- Replaced vague `weighted association` with its sourced primary statistic:
  prompt tags reduce behavior entropy beyond session membership by 8.419%,
  versus a 1.903% null p95 over 1,000 session-preserving permutations
  (`p=0.001`). The source record is
  `docs/visexp/out/behavior-tag-alignment-r251/behavior-tag-alignment-r251.json`,
  which also carries the expanded-effect-weight limitation retained in the
  paper.
- Kept the source flamegraph rasters unchanged, but defined their embedded
  lowercase `agentpprof` title as the artifact CLI name. Visual inspection
  showed both left-side crops and their titles intact. The caption's stale
  `top/bottom` directions were independently found and corrected to
  `left/right`.

### Consider decisions

- **Applied:** added an RQ2 opening sentence stating that the complete
  identity--structure test depends on RQ3's frozen identity; reordering the
  numbered subsections as RQ1, RQ3, RQ2, RQ4 would create a larger reading
  defect.
- **Applied:** updated the Python-generated RQ3 plot labels to official paper
  names (`Mind2Web`, `WebShop`, `SWE-agent`, `WebLINX`, `AgentTrek`,
  `GUI-Odyssey`, `AndroidCtrl`, `ToolBench`, and `API-Bank`) and regenerated
  only the RQ3 PDF/PNG from unchanged numeric arrays.
- **Applied:** changed the identity qualification reference from broad
  Background to the formal scope-tree model and a new precise RQ3 label.

### Compilation and recheck

A fresh `make` and final `pdflatex` pass produced a 9-page PDF with seven
content pages and References beginning on page 8. The source retains 59
citation commands and four RQ subsections, and the log contains no undefined
citation or reference. The architecture and RQ3 result pages were rendered at
150 dpi and visually inspected. Two existing overfull boxes remain for later
local language/layout rounds.

The independent focused recheck verified every Must-fix, Should-fix, and
accepted Consider item. It initially reported a truncated file-profile title,
but source-native regeneration disproved that finding: rendering
`docs/flamegraph-example/agentsight-files.svg` at 150 dpi produced a
bit-identical 1875x378 PNG with SHA-256
`4dbca9006c9c44458cccfe73faab5da6e0c7ebbb38faa7657cefb875de4789bc`.
The current source PNG and freshly rendered PDF page 3 both show the complete
`agentpprof files profile` title. The reviewer withdrew the cached-render
finding and returned `PASS`; no paper-consistency Must-fix or Should-fix
remains.

The `docs/agentpprof-paper/` submodule remains internally clean at
`7f80c433c9555317a2aa45a78d0ff93518f4c12c`. This round did not edit the
protected `docs/evaluation.md` or `docs/idea-story.md` changes and performed no
Git operation. Round 6 next audits sentence structure without changing any
scientific claim, number, RQ, or contribution.
