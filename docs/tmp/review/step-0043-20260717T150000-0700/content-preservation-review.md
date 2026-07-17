# Step 0043 — Independent Content-Preservation Review

## Node identity

- **Audit snapshot:** 2026-07-17T14:49:41-07:00
- **Parent:** Step 0042 minimal AAAI-27 format repair
- **Gate:** REVIEW
- **Scope:** read-only scientific-content preservation audit of the current
  filesystem snapshot. The only write performed by this reviewer is this
  Markdown report.
- **Target venue/domain:** AAAI-27; genuinely cross-domain agent AI and systems
  observability.
- **Paper entrypoint:** `docs/paper/main.tex`
- **Reviewed PDF:** `docs/paper/main.pdf`
- **Read-only story source:** `docs/agentpprof-paper` at
  `7f80c433c9555317a2aa45a78d0ff93518f4c12c`.
- **Reviewer verdict:** **PASS — 0 must-fix, 0 should-fix, 0 preservation
  concerns.**

This is not a new novelty, acceptance, or experiment-selection review. It asks
only whether Step 0042's mechanical format repair changed the scientific
content that had passed Step 0040's Round 11 meaning audit.

## Skills and review contract

The reviewer explicitly followed the read-only parts of:

1. `iter-review-critique`, including its research-taste, systems, AI/ML, and
   cross-domain references; and
2. `check-terminology-infoflow` in combined paper-consistency and
   terminology-consistency scope, including its `paper-consistency.md`
   reference.

The parent request intentionally narrows this pass from a normal full
scientific review to content preservation. Consequently, no external novelty
search or new accept/reject score was produced: external search cannot answer
whether local float, font-size, and image-serialization edits changed this
paper's existing meaning. The current full paper, all claim-bearing tables and
figures, bibliography, `docs/idea-story.md`, `docs/user-instruction.md`, the
Step 0040 Round 11 meaning audit, and the Step 0041/0042 reports were read.
The existing source diff and submodule state were inspected read-only; no
stage, commit, push, branch, checkout, or other repository mutation occurred.

The report is informed rather than blind because comparison with Step 0041 and
Step 0042 is the object of this audit. This does not contaminate a preservation
verdict, but it means the report must not be reused as a fresh scientific
acceptance review.

## Inputs and snapshot fingerprints

| Artifact | SHA-256 at audit snapshot |
|---|---|
| `docs/paper/main.tex` | `1d4d17c71be9f94173cda88a497ffc7ce8b347d36b7294766e5829440d9b5b09` |
| `docs/paper/figures/fig-architecture.tex` | `c85cbf3e37d4e5478632c1729b5d95dff57d6a52d85730687f8b745b6587f3c9` |
| `docs/paper/references.bib` | `f07fb3fc29f22062bc848bfc7cc840fa59fadca309843c5811b1717c033e8aa4` |
| `docs/paper/main.pdf` | `9d57885cef877193590f14fe41b6ae15f7b218795f345bb69aafa1bd5970b279` |
| Step 0041 report | `946c5b3863afee1e122b49ec2bc93923be3dfe0210e51330de28db78afe4b02e` |
| Step 0042 report | `66983047a10a3c45547bccdb267eaf4fe89b495d7a16bc394123b3572a48aa3d` |

The bibliography's filesystem modification time is
2026-07-17T13:04:32-07:00, before the Step 0041 audit and Step 0042 repair. It
was not part of the format-repair edit interval.

## Reconstruction of the Step 0042 change surface

The current source and diff agree with the five mechanical repairs authorized
by Step 0041 and recorded by Step 0042:

1. the `float` package is gone and `[H]` placements are ordinary `[t]`/`[tb]`
   floats;
2. the architecture diagram is a native-size two-column figure instead of a
   `\resizebox`-scaled one;
3. result tables use `\small` and tighter row spacing instead of
   `\scriptsize`;
4. the flamegraphs reference externally rendered paper assets without LaTeX
   `trim` or `clip`; and
5. architecture annotation fonts are `\small` rather than
   `\footnotesize`/`\scriptsize`.

No prose, equation, algorithm step, table row, table heading, caption claim,
citation key, RQ, or contribution wording is part of this observable
format-repair surface. The full current-paper read found no scientific
addition, deletion, substitution, or silent qualifier loss associated with
these changes.

There is no retained byte-for-byte source snapshot made exactly between Step
0040 and Step 0042. This review therefore triangulates the current paper
against the detailed Step 0040 Round 11 preservation contract, the Step 0041
violation inventory, the Step 0042 authorized-change list, the current source
diff, and the rendered PDF. That is sufficient for the localized format-only
change surface and does not justify adding a new snapshot or protocol.

## Scientific invariant audit

### Thesis and story

**PASS.** The exact sentence

> Agent observability needs profiling, not only debugging.

appears three times in active paper prose: Abstract, Introduction, and
Conclusion. It is character-for-character identical to the sentence in the
read-only submodule and to the permanent thesis in `docs/idea-story.md`.

The story's causal chain remains intact:

1. agents produce populations of heterogeneous trajectories;
2. per-run execution structure does not supply reusable cross-run semantic
   responsibility;
3. a uniform weighted **operation** represents agent activity or an effect;
4. a query-time **operation stack** folds selected additive measures under a
   chosen responsibility hierarchy; and
5. AgentProf complements per-run debugging with population-level profiling.

Operations and operation stacks remain the only two core abstractions. Format
repair introduced no new concept, mechanism, contribution, or narrower
replacement thesis.

### Four RQs and order

**PASS.** The active Evaluation declaration contains exactly these four
questions, in the required attribution, localization, tag-accuracy, and cost
order:

1. **RQ1:** Does semantic profiling improve resource attribution?
2. **RQ2:** Does profiler output correspond to real problems?
3. **RQ3:** How accurate are the tags?
4. **RQ4:** What is the profiling cost?

Their normalized wording matches the four original submodule subsection
questions. The current short subsection titles — Resource Attribution, Problem
Correspondence, Tag Accuracy, and Profiling Cost — preserve the same order and
constructs. No RQ was added, removed, merged, narrowed, or reordered.

### Claims, qualifiers, and quantitative evidence

**PASS.** The current abstract, introduction, RQ sections, scope/limitations,
and conclusion retain a consistent set of load-bearing values and qualifiers.
The following cross-section checks all agree:

| Evidence chain | Preserved values and scope |
|---|---|
| RQ1 controlled capture | 20 completed real Codex tasks; 1,520/1,574 recovered in-scope effects; 100.0% precision; 96.569% recall; all 1,629 concurrent-control effects rejected; five predeclared task-category totals conserved. Abstract/Introduction use the consistent rounded 96.6% recall. |
| RQ1 responsibility partitions | All 405 reconstructable failed CodeTraceBench trajectories, 20,866 operations, and 2,948 human stages; ordinary B³ F1 0.541 to 0.649 over raw action, with the recorded 0.108 gain and [0.087, 0.129] interval. The post-hoc-support qualifier remains. |
| RQ2 localization | Standard MAP comparisons remain .789/.773, .452/.281, and .230/.121 for semantic/raw on AgentProcessBench, HINTBench, and TraceElephant. The complete target-bearing populations and adaptive/post-hoc qualifiers remain explicit. |
| RQ3 field and boundary evidence | Ordinary B³, V-measure, exact boundary F1, macro-F1, and accuracy results remain: 0.654 phase B³ F1; 0.557/0.815 V-measure; 0.695 task macro-F1; 0.498 action macro-F1; 0.680 boundary F1 and 0.786 B³ F1 for label-free recurrence. The integrated task path versus standalone action adapter distinction, held-out-session protocol, 39-`Locate` sensitivity, and development-evidence qualifiers remain. |
| RQ4 construction cost | Four complete public workloads plus their union remain; union size is 27,765 operations; semantic/raw time is 1.17/0.99 seconds; peak RSS is 464.5 MiB; stated deltas remain 180 ms (18.2%) and 6.0 MiB (1.3%). Capture, source adaptation, field/tag generation, and live-agent overhead remain excluded. |
| Evaluation population qualifiers | The 325 histories remain explicitly collected over multiple months. The 15 families remain real-agent or human web/API/coding/mobile/GUI executions. The nine-dataset 13,265-operation depth sweep remains distinct from the 15-family 47,590-operation adapter population. |

The rendered PDF contains all four RQ headings, all four claim-bearing result
tables, the architecture caption, the three-flamegraph caption, the exact
thesis, and the conclusion. No content disappeared during float movement.

### Citations and metric-to-construct mapping

**PASS.** The active paper has 114 citation-key uses covering 58 unique keys,
with zero undefined keys. The existing LaTeX log has no undefined citation or
reference warning. Step 0042 did not modify `references.bib`.

The standard paper-facing metrics remain explicitly mapped to defining or
published precedents:

| Construct | Paper-facing metric | Citation retained |
|---|---|---|
| partition agreement | ordinary operation-level B³ precision/recall/F1 | `bagga-baldwin-1998-entity-based` |
| ranked problem localization | per-query non-interpolated AP, averaged as MAP | `robertson2008ap` |
| literal task/action classification | macro-F1 and accuracy | `lewis2004rcv1` |
| partition-valued fields | V-measure | `rosenberg-hirschberg-2007-v-measure` |
| adjacent segmentation boundaries | exact precision/recall/F1 | `ruokolainen2016segmentation` |

The metrics continue to answer only their declared constructs; the format pass
did not promote a protocol knob into a metric or alter a metric definition.

### Explicit prohibited-protocol search

**PASS.** Case-insensitive searches over active `main.tex`,
`references.bib`, and paper figure/source files return zero occurrences of:

- token-weighted B³;
- Recall@20% or a 20%-budget recall result;
- fixed top-3;
- fixed-reader; or
- model-reader.

The paper uses **ordinary** B³ as its primary partition metric. RQ2 uses
standard AP/MAP. The removed reader protocol survives only in research history
outside the paper, as intended; Step 0042 did not reintroduce it.

## Figure and table preservation audit

### Architecture figure

**PASS.** `fig-architecture.tex` changed only typography/contrast. Component
and edge text is unchanged: local/public inputs, uniform operations, field
derivation, rules/model/mapping, stack construction plus folding, profiles,
pprof/SVG/JSON, and the parse/read edge labels remain. Moving the figure from
one column with `\resizebox` to native two-column placement does not alter the
pipeline or caption.

### Flamegraph panels

**PASS.** The new paper panels are presentation transforms of the existing
`docs/flamegraph-example/agentsight-{tokens,time,files}.svg` profiles. An
independent XML comparison produced:

| Panel | Source groups | Paper groups | Ordered titles | x/width/fill |
|---|---:|---:|---|---|
| tokens | 940 | 940 | exact match | exact match |
| time | 865 | 865 | exact match | exact match |
| files | 2,051 | 2,051 | exact match | exact match |

The transform changes y coordinates, row height, label font size, and visible
label truncation only. Every complete node title — including its hierarchy,
value, and percentage — remains in the paper SVG in the same order, and every
rectangle retains its x position, width, and fill. It therefore preserves
hierarchy, additive width, ordering, source data, and the caption's three
measures. The original time PNG is pixel-identical to a rasterization of its
vector source at the old size; token and file originals have the corresponding
scaled source dimensions and matching geometry. No experiment or data was
rerun.

### Tables

**PASS.** Float specifiers, font size, and row spacing changed. All method and
workload labels, column headings, numeric cells, bold markings, captions, and
references remain. PDF text extraction confirms that every row is present.

## Terminology and information-flow preservation

The changed surfaces introduce no reader-facing terminology. The full-paper
concept anchors remain defined and stable:

- **operation:** weighted fielded record for activity/effects;
- **operation stack:** ordered query-time field projection used for folding;
- **tag:** operation field consumed through the pluggable field interface;
- **label-free recurrence:** adjacent visible-action recurrence learned without
  target annotations; and
- **semantic/raw/local groupings:** distinct comparison conditions, not names
  for the same mechanism.

Architecture labels match the Design/Implementation terms; table captions
match their RQ prose; B³ is consistently described as ordinary and
per-operation; MAP is consistently the mean of per-query AP; and the scope
qualifiers remain adjacent to their claims. No format-induced synonym drift,
undefined term, component rename, interface/mechanism mismatch, or broken
cross-section information flow was found.

## Read-only submodule audit

**PASS.** `docs/agentpprof-paper` has no working-tree changes, no parent diff,
and remains at `7f80c433c9555317a2aa45a78d0ff93518f4c12c`. Step 0042 did not modify
the read-only authoritative source.

## Inconsistencies found

None.

## Must-fix items

None.

## Completion assessment and routing

The Step 0042 format repair **preserves scientific meaning**. It preserves the
exact thesis, the exact four RQs and order, two-object model, story, claims,
qualifiers, numbers, captions, standard-metric policy, citations, and read-only
submodule. Token-weighted B³, Recall@20%, and fixed top-3/model-reader protocols
remain absent.

**Final preservation verdict: PASS.** This reviewer authorizes closing the
content-preservation part of Step 0042. The independent format-compliance
review and the separately requested fresh whole-paper AAAI scientific review
remain distinct decisions; this PASS must not be interpreted as their result.
