# Iter-Refine-Ideas Round 2g — Attention-Contract Defense

## Contract repair

The method now separates four costs:

1. offline stable-identity and index construction;
2. query-time metadata scoring;
3. raw operation content exposed by whole emitted scopes;
4. downstream localizer tokens.

Ingestion computes query-independent metadata `z(o)`.  The query risk
`r_q(o)=f(q,z(o))` is metadata-only by default.  Any selector that reads raw text
or invokes an LLM at query time must charge those tokens as selection work and
cannot claim lower total model attention unless the end-to-end total improves.
RQ3 is explicitly responsible for index/selector CPU, memory, time, model tokens,
raw content, downstream tokens, and capture overhead.

## Non-obvious prediction

The paper no longer suggests that a historical-prior tree ranker is novel merely
because its components are named.  Its falsifiable prediction is:

> Although cross-run aggregation normally erases local execution context,
> stable semantic recurrence can make the pooled profile a better diagnostic
> index for an untouched trace than that trace’s own execution tree.

Support requires the frozen cross-run prior to beat the same tree with local
risk alone, native and matched trees, and SDBL-style current-log scopes at
matched raw-content and end-to-end cost.  Failure falsifies the central method
and leaves only the engineering substrate.

## Status

This closes the remaining idea-contract defect.  It does not provide the missing
fresh-family evidence or implementation.  A new reattack must decide whether
the idea is now `HARDENED` with explicit experiment obligations.
