# Result review: stable-ID operation marks and two collection cases

Timestamp: 2026-07-22T00:55:00-07:00
Status: root review complete; independent reviews pending

## Correctness

The product interface works as intended on both synthetic tests and the complete
four-session review collection. It conserves all source operations, supports paths of unequal
depth, aggregates shared semantic operation names across sessions, and rejects
ambiguous replay rather than silently falling back. Marks are applied before
filters, so a focused query cannot change the inherited path by deleting an
earlier boundary.

## User value

The first case answers all four fixed questions using standard pprof queries. The most
useful observation is not a generic tool-count summary: repair verification
consumes 38.3% of the four reviews, and the profile decomposes that cost into
scope recovery, artifact validation, fix inspection, documentation audit, and
tests. It also retains specific exception paths that a flat action/tool stack
would mix into generic reads and commands.

The second case is also collection-level: one signed pprof aggregates all 338
bad-good pairs drawn from 440 real trajectories and 125 tasks. It exposes
bad-side repetition, stopped work, and concrete interaction errors together
with good-side terminal, conclusion, and user-reporting paths. This is useful
even though simple step count remains the stronger scalar discriminator,
because the profile identifies what kind of excess work occurred and retains
the action/object path for source drilldown.

## Scientific authorization

The result supports four narrow statements:

1. sparse stable-ID marks are sufficient to construct variable-depth semantic
   operation stacks without relabeling every source operation;
2. one shared operation-name pool produces useful cross-session aggregation in
   the complete AgentCap case;
3. the resulting pprof answers the fixed case questions with source-complete
   operation counts; and
4. one standard signed pprof can aggregate the complete 338-pair population
   and retain diagnostically distinct positive and negative path families.

It does not establish automatic nested-boundary accuracy, semantic-name
accuracy, user utility, superiority to recurrence on CodeTraceBench, or a new
failure classifier. The same Agent chose and interpreted the AgentCap marks,
and AgentRewardBench has no gold semantic hierarchy. Those limitations are
explicit in the paper subsections.

## Decision

Adopt the stable-ID operation-mark input as a product mechanism and retain both
many-session cases in the paper. Do not call the Agent backend an automatic
validated constructor or the signed profile a failure detector. The complete
automatic CodeTrace comparison remains a separate next experiment after the
user-requested case-study-first increment.
