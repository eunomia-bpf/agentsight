# RQ7/F10 Independent Result Review — Round 2 Follow-up

**Reviewed:** 2026-07-22  
**Scope:** follow-up on the two bounded blockers in `result-review-1.md`; the
approved dependency-only readiness estimand is unchanged  
**Verdict:** **PASS**

## Formal judgment

```text
run status: valid
tested hypothesis: supported within the dependency-only scope
research value: dependency-only
paper impact: measurement/workload boundary; canonical RQ7 remains open
next paper decision: preserve the explicit stopped comparison and do not
                     promote it into a capability/superiority result
```

The final artifacts faithfully answer only whether the frozen RQ1 corpus is
ready for a future independently scored matched comparison.  They do not run a
baseline, build a question set, estimate accuracy or coverage advantage, score
evidence, or report latency/token/cost.  The missing source contracts stop the
comparison, and that stop is now fully recorded and legibly rendered.

## Round-1 blocker closure

### B1. Execution record — closed

`commands.log` is now 3,576 bytes and records:

- both plan-review dispositions and the dependency-only authorization boundary;
- syntax verification and the exact authoritative command;
- the RQ1 expected-hash contract and the six fixed missing contract paths;
- the successful 12-present/24-N/A result;
- wall time and maximum RSS;
- consecutive-run byte identity for the three CSVs, `result.md`, and PNG;
- the reason PDF byte identity is non-gating;
- pre-repair output/script anchors and final PDF/PNG/script anchors; and
- the scientific disposition for every method and template family.

The log does not claim that the PDF is deterministic and does not reinterpret a
missing contract as an observed zero.  It records the same approved command and
does not introduce any additional data source or method execution.

### B2. Figure legibility — closed

The 36 source-matrix cell annotations now use 7 pt rather than 6.5 pt.  All
other principal figure labels remain at least 7 pt.  The final PDF is 7.05 in x
7.25 in with embedded TrueType fonts; the PNG is 1410 x 1450.  At original
resolution and intended two-column width:

- `present`, `coverage-only`, and `N/A` are readable and text-labeled;
- green, amber, and gray are supplementary rather than sole encodings;
- no stopped method or template is dropped;
- every template retains `N/A` and `30 x 4 not evaluated`; and
- `MATCHED COMPARISON STOPPED` plus the no-result qualifier remain prominent.

No data or interpretation changed as part of the font-only repair.

## Independent final reproduction

I independently ran the approved command twice again into two new temporary
directories.  Each of the following was byte-identical across both runs and
byte-identical to the final experiment artifact:

| Output | Final SHA-256 |
|---|---|
| `rq7-source-contract.csv` | `f236880339d484a090b219c975f2fccdc1518b28621072b021f9038457148808` |
| `rq7-method-readiness.csv` | `3a546a3bcbd8946ee7695feb6c4fa5969af6ec240520a0fa4ab6c83177521adc` |
| `rq7-template-readiness.csv` | `f4ed2d7065a1a2f834955b45a6c0e6e61cc51ee12b49a04b27b2a466f60f6d0a` |
| `result.md` | `fa5c2fa392203e377a3a2c9b517b37ce71876ffa8eaa3cfe6f4492ada271fc19` |
| `rq7-benchmark-readiness.png` | `19a4404e7b797726b91b4398827f76226db613f8838325667ba0cefa0625b3f0` |

The review runs took 1.13 s / 1.09 s and 385,316 / 385,664 KiB maximum RSS.
`python3 -m py_compile agentvis/research/plot_rq7.py` also passed.

The unchanged CSV and Markdown hashes prove that the rendering repair did not
alter any readiness cell.  The PNG hash changed from the pre-repair anchor
exactly as expected and matches the final anchor in `commands.log`.

## Final result reconciliation

The independently verified final state remains:

- source contract: **12 present, 0 partial, 24 N/A** across six projects and six
  requirements;
- normalized Counts: `measured`, meaning prerequisite availability for
  descriptive counts only;
- Artifact Trajectory: `coverage-only`, because its normalized projection
  exists without an independent matched oracle;
- Final State, ProcGrep, and Raw-log LLM: `N/A`;
- action-only, artifact-linked, cross-session, and final-state templates: all
  `N/A`; and
- every template-level `30 x 4` gate: `not evaluated`.

The implementation still contains no live-checkout/native-session scan and no
circular oracle.  Output schemas contain readiness statuses and explanations,
not performance metrics.  N/A remains a literal labeled state rather than a
zero-valued result.

## Scope-preserving limitations

The audit remains dependency-only and cannot close canonical RQ7.  If included
in the paper, the title/caption must continue to state that it is a
benchmark-readiness/source-contract audit and that no baseline was run.  The
future matched comparison still needs a new reviewed plan, immutable native
prefixes/cutoff worktree state, independent oracle dispositions and templates,
and executable method contracts.

The Round-1 note about validating actual tar.zst members and their hashes before
a future native archive can ever be labeled `present` remains a future-path
hardening requirement.  It does not affect this valid result because the exact
archive contract is absent and every corresponding cell is N/A.

## Decision

**PASS.** Both bounded blockers are closed, the final outputs independently
reproduce, the figure is legible at the intended width, and no scope expansion
or scientific-value inflation occurred.  No further RQ7 readiness rerun is
needed unless the frozen source contracts themselves change; any actual
capability comparison must begin under a new reviewed experiment plan.
