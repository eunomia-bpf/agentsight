# Phase 2B: Cross-Run Identity Is Unscorable; Reuse Proxy

## Result

No public CodeTraceBench gold defines whether two stages from different
trajectories are the same semantic operation. Standard pairwise identity
precision, recall, F1, false-merge counts, false-split counts, and
majority/random identity baselines are therefore **not computable** on this
population.

Phase 2A was not run. Equal local stage ordinals were not substituted for
semantic types, and no project-defined score was invented.

The deterministic Phase 2B proxy instead measures:

1. whether canonical IDs are actually reused across sessions, tasks, and
   frameworks;
2. how much source-name, action, and local-position diversity each reused ID
   contains;
3. whether complete canonical paths, not only individual frames, recur.

These are descriptive reuse statistics and qualitative-audit inputs. They are
not accuracy metrics.

## Population and pipeline

The analysis uses every Step 0087 artifact:

- 405 CodeTraceBench trajectories;
- 20,866 operations;
- 4,496 semantic occurrence instances;
- 2,948 human stage ranges;
- 251 task names;
- four agent frameworks;
- 3,895 pre-canonical open labels;
- all 783 post-canonical IDs and all 2,086 complete canonical paths.

The canonicalizer preserves the Step 0087 temporal partition and leaves zero
adjacent display-path collisions. Thus this analysis concerns only cross-run
identity reuse; it does not reinterpret the existing B³ or boundary result.

## Cross-run reuse

### Individual canonical frames

| Scope | IDs | Reused across sessions | Reused across tasks | Reused across frameworks | Present in all 4 frameworks |
|---|---:|---:|---:|---:|---:|
| Any stack depth | 783 | 243 (31.034%) | 214 (27.331%) | 183 (23.372%) | 32 (4.087%) |
| Leaf position | 740 | 227 (30.676%) | 206 (27.838%) | 163 (22.027%) | 28 (3.784%) |
| Root position | 45 | 23 | 18 | 20 | 4 |

At least one cross-session canonical frame appears on 20,859 of 20,866
operation paths (99.966%). A cross-session canonical ID is the leaf on 18,015
operations (86.337%). The pipeline therefore does perform broad cross-run
aggregation; its IDs are not merely per-session aliases.

Cross-framework leaf-ID overlap is also widespread:

| Framework pair | Shared leaf IDs |
|---|---:|
| OpenHands + Terminus2 | 108 |
| OpenHands + mini-SWE-agent | 89 |
| Terminus2 + mini-SWE-agent | 72 |
| OpenHands + SWE-agent | 45 |
| SWE-agent + mini-SWE-agent | 38 |
| SWE-agent + Terminus2 | 33 |

These overlaps establish reuse coverage, not correctness.

### Complete paths

Of 2,086 complete canonical paths:

- 345 recur across sessions (16.539%);
- 246 recur across frameworks (11.793%);
- 1,741 occur in only one session.

The most reused complete paths are:

| Canonical path | Sessions | Frameworks | Tasks | Operations |
|---|---:|---:|---:|---:|
| `resolve work -> inspect work` | 87 | 4 | 74 | 917 |
| `build work -> inspect work` | 76 | 4 | 57 | 734 |
| `build work -> verify work` | 61 | 4 | 46 | 302 |
| `resolve work -> verify work` | 58 | 4 | 54 | 237 |
| `build work -> create work` | 55 | 4 | 42 | 211 |
| `build work -> test work` | 40 | 4 | 32 | 210 |
| `resolve work -> test work` | 39 | 4 | 39 | 168 |

Complete-path reuse is substantially less common than individual-frame reuse.
This matters for audit: a broad leaf label may be more interpretable under its
ancestor path, but the released gold cannot say whether that context makes the
merge correct.

## Highest-reuse leaf IDs and member diversity

The table below reports the strongest qualitative-audit targets. “Original
names” is the number of distinct pre-canonical Step 0087 labels mapped to the
canonical ID. “Actions” counts the benchmark's nine coarse source action kinds.
“Stage ordinals” counts distinct local stage positions; it is not a semantic
type count.

| Canonical leaf | Sessions | Tasks | Frameworks | Original names | Actions | Stage ordinals | Example source names |
|---|---:|---:|---:|---:|---:|---:|---|
| `inspect work` | 289 | 200 | 4 | 327 | 9 | 17 | `inspect affected code`; `inspect environment`; `inspect owlvit flow` |
| `verify work` | 227 | 165 | 4 | 250 | 9 | 18 | `verify runtime health`; `verify replacement`; `verify requirements` |
| `test work` | 189 | 145 | 4 | 234 | 8 | 18 | `test baseline`; `test solver settings`; `test tensorflow loading` |
| `diagnose work` | 111 | 83 | 4 | 132 | 8 | 14 | `diagnose ssh access`; `diagnose early exits`; `diagnose heading parsing` |
| `validate work` | 102 | 83 | 4 | 119 | 8 | 15 | `validate behavior fixes`; `validate generated outputs`; `validate npm install` |
| `create work` | 101 | 75 | 4 | 125 | 7 | 16 | `create environment`; `create fallback artifacts`; `create dependency mocks` |
| `configure work` | 99 | 76 | 4 | 100 | 8 | 15 | `configure account database`; `configure runtime`; `configure toolchain` |
| `resolve work` | 92 | 72 | 4 | 110 | 8 | 11 | `resolve syntax conflicts`; `resolve runtime dependencies`; `resolve matching` |
| `build work` | 87 | 68 | 4 | 121 | 8 | 15 | `build semantic annotations`; `build delivery logs`; `build raytracer` |
| `reproduce work` | 81 | 71 | 4 | 90 | 8 | 14 | `reproduce curl binary`; `reproduce installation`; `reproduce documentation failures` |

The complete raw JSON retains, for every canonical ID:

- operation, occurrence, session, task, and framework counts;
- depth and local-stage-ordinal distributions;
- the complete pre-canonical label-count map;
- action-kind and raw-action-key diversity;
- deterministic source-linked examples, covering frameworks before repeats.

This diversity is exactly where a semantic gold would be needed. Broad
action-first terms may correctly reunite recurring responsibilities, may merge
different objects too aggressively, or may do both in different members. The
proxy cannot choose among those explanations.

## Local stage-position correlate

Of the 227 leaf IDs reused across sessions:

- 210 (92.511%) appear under more than one local stage ordinal;
- 17 appear under exactly one local stage ordinal.

This rules out the trivial descriptive explanation that most cross-session
name reuse is simply a renaming of “stage 1,” “stage 2,” and so on. It does
**not** validate semantic identity: a real operation can occur at different
positions, and unrelated operations can occur at the same position.

No pairwise metric was computed against these ordinals.

## Interpretation

The strongest supported conclusion is:

> Step 0087 canonicalization creates substantial cross-session and
> cross-framework reuse, and complete paths retain some recurring context, but
> CodeTraceBench supplies no public semantic relation that can determine
> whether those merges and splits are correct.

Accordingly:

- the existing 0.763539 B³ F1 and 0.479952 boundary F1 remain valid only for
  per-trajectory stage partition and boundary fidelity;
- the 783 canonical IDs must not be described as gold-validated cross-run
  operation classes;
- high-reuse generic IDs such as `inspect work`, `verify work`, and `test work`
  are the highest-value targets for a future independently annotated identity
  audit;
- this result is an evidence-boundary finding and qualitative audit, not a
  contradiction of RQ3 or the paper thesis.

All exact counts and source-linked examples are in `raw-results.json`. The
deterministic recomputation entry point is `analyze_identity_proxy.py`.
