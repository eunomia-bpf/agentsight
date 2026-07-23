# Paper consistency review: Step 0067 targeted WRITE

**Verdict: PASS.  Must-fix: none.**

Scope: read-only review of the complete
[`docs/paper/main.tex`](../../../../paper/main.tex), focused on the targeted
WRITE changes to implementation warnings, the RQ1 Git case, and the RQ2
AgentReward case.  I cross-checked their claims against the Step 0067 handoff,
both canonical case READMEs, the AgentReward full-result summary/result review,
the source workspace, and canonical pprof artifacts.  No paper, code, figure,
or result input was modified.

## 1. Inconsistencies found

None that require a paper correction.

The targeted changes are internally consistent and match their canonical
artifacts.  I found no stale fixed-chain Case-Study-2 narrative, no conflation
of the Git direct frame and cumulative subtree, no signed-side reversal, no
warning-as-endpoint claim, and no abstract/introduction/conclusion statement
that contradicts the revised cases.

## 2. Evidence cross-checks

### Implementation: hierarchy warnings

The implementation paragraph (main.tex lines 440--457) accurately states the
three warning classes: optional recursive unary refinement, broad flat fan-out
with little recursive refinement, and optional semantic leaves spanning at
least eight tool calls.  It explicitly calls them nonblocking diagnostics and
states that they neither force artificial depth nor block profile generation.
This matches Step 0067-E13 and the Git-case README's mechanical hierarchy
audit.

The paper keeps the intended boundary in all relevant locations:

- RQ1 reports zero unary and flat-fan-out warnings plus 27 **advisory** coarse
  leaves (lines 534--540); this matches the reconciled Git workspace.
- The warnings are never used for RQ1 or RQ2 scientific acceptance.
- The RQ2 endpoint is AP plus task-cluster uncertainty, while the full-result
  review records empty pprof warning arrays as product QA only.

### RQ1: Git multi-resource case

The text, Figure 1 caption, and canonical reconciled pprof files agree on both
the population and the direct-versus-cumulative distinction.

| paper claim | independent artifact readback | result |
|---|---:|---|
| focused task total | 489 operations; 4,558,192 tokens | match |
| direct SSH diagnosis frame | 97 operations; 1,936,828 tokens | match |
| complete SSH subtree | 105 operations (21.47%); 2,103,587 tokens (46.15%) | match |
| count width by framework | Terminus2 56.24%; OpenHands 43.76% | match |
| token width by framework | OpenHands 86.62% | match |
| focused annotations/source nodes/depth/warnings | 96 / 735 / 5 / 0 unary, 0 flat, 27 advisory coarse | match |

In particular, `go tool pprof -top -focus=diagnose_rejected_ssh_password_authentication`
on the canonical reconciled operation and token profiles reports the direct
97/1,936,828 frame and cumulative 105/2,103,587 subtree exactly.  The prose
uses “directly contains” for the former and “complete recursive subtree” for
the latter, so it does not make the prior direct/cumulative error.

The figure paths referenced by main.tex all exist: count overview, token
overview, and the SSH focused panel.  The caption correctly says that source
LLM/tool leaves remain in the pprof artifact while the paper rendering hides
them only for legibility.  This is consistent with the paper's operation-stack
definition (semantic frames followed by source evidence) and with the stated
no-custom-frontend product boundary.

### RQ2: AgentReward differential case

The paper now uses the complete recursive collection profile, not the earlier
fixed-chain figure.  Its canonical recursive artifact has the same SHA-256 as
the retained full-result profile:

```text
bcb8843bafd3fb5aa5bab0e0b7cc560c870382763a08cb781e85da23f277e2dc
```

Population, workspace, signed-side, and focus quantities all match the
canonical full result.

| paper claim | canonical value | result |
|---|---:|---|
| trajectories / mixed-outcome tasks / pair occurrences | 440 / 125 / 338 | match |
| success / failure sessions | 202 / 238 | match |
| source operations before outcome join | 7,229 | match |
| sparse recursive annotations | 2,131 | match |
| semantic depth before LLM/tool evidence | 4 | match |
| signed bad / good operation occurrences | 7,366 / 3,780 | match |
| recovery focus bad / good | 2,993 / 392 | match |
| completion focus bad / good | 135 / 191 | match |
| recovery bad / good exposure | 40.6% / 10.4% | match (40.633% / 10.370%) |
| completion bad / good exposure | 1.8% / 5.1% | match (1.833% / 5.053%) |

The signed semantics are stated consistently: red means bad-side excess and
green means good-side excess; the profile is explicitly diagnostic rather than
causal.  The caption's focus counts are side-specific counts, whereas a signed
pprof focus displays their net difference.  The body does not confuse those
two quantities.

The two selected figure files exist and are the preregistered stock-pprof
recovery and completion focuses.  Their stated source stack shape (shared
semantic responsibilities followed by LLM and tool evidence, with source
labels for drilldown) agrees with the design definition of
`agent -> semantic operations -> evidence`, not a raw session/prompt stack.

### AP protocol and RQ boundary

The RQ2 case describes a distinct collection-scale endpoint without changing
the paper's RQ2 wording.  It correctly separates it from the three
problem-localization workloads earlier in the same subsection.

- Annotation is described as source-only and completed before outcomes or
  expert annotations are opened.
- Recovery exposure is defined at the correct unit: fraction of a unique
  trajectory's source operations whose semantic path contains the canonical
  recovery responsibility.
- The eligible expert endpoint is 435 consensus-labelled trajectories
  (173 positive, 262 negative); its ordinary non-interpolated AP is .614 and
  prevalence is .398.
- The registered 10,000-draw **task-cluster** bootstrap interval for
  AP-minus-prevalence is [.162,.274], wholly positive.
- Fixed-chain repeated/error AP is .656 and the recursive-minus-fixed interval
  [-.127,.042] crosses zero.  The prose therefore says “does not establish
  detector superiority,” not that recursive profiling wins the detector
  comparison.

These numbers, units, and interpretations agree with the independently
recomputed `full-result/summary.json` and `results.md`.  This supports the
narrow conclusion written in main.tex: correspondence to independently
annotated looping plus source-drillable localization, but no causal claim, no
nested-topology-accuracy claim, and no detector-superiority claim.

### Abstract, introduction, and conclusion

The global framing remains compatible with the targeted WRITE:

- The abstract and introduction retain the semantic operation-stack model,
  source evidence, additive-resource width, and standard pprof boundary; they
  do not claim a warning-free hierarchy or universal recursive superiority.
- The introduction's “two population case studies” and contribution summary
  are consistent with the Git and AgentReward cases as scoped supporting
  evidence.
- The conclusion's “resource-dependent bottlenecks and success--failure
  differences” is supported by the two cases and does not overstate the
  AgentReward AP result as a causal or universal classifier result.

Terminology remains stable across the affected sections: `semantic hierarchy`,
`operation stack`, `source evidence`, `bad-side/good-side`, `recovery exposure`,
and `fixed-chain` retain their defined roles.  The paper distinguishes source
parent structure from inferred semantic operations and uses session/prompt IDs
as labels rather than visible aggregate frames throughout the design and case
descriptions.

## 3. Broader follow-up checks

No additional Step 0067 rewrite is required.  For future result changes, keep
the following invariants together:

1. retain Git's direct frame and cumulative subtree as separately named
   quantities;
2. report AgentReward side-specific focus counts separately from signed net
   pprof values;
3. keep hierarchy warnings advisory and outside every scientific endpoint;
4. preserve the AP unit (unique trajectories) and bootstrap unit (125 task
   clusters), while retaining pair occurrences only for the signed profile.

## Final disposition

**PASS.** The targeted WRITE is numerically, artifact-, figure-, terminology-,
and RQ-boundary-consistent.  **Must-fix: none.**
