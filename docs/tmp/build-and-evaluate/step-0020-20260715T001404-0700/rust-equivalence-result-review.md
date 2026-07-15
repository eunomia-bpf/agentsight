# Independent Python–Rust Equivalence Result Review

**Verdict:** **PASS**
**Role:** valid mechanical port equivalence; no fresh RQ3 evidence

The fresh reviewer independently started from the authoritative exact-alignment
OSWorld-Human source rather than trusting the generated summary. It rebuilt all
287 sessions, 3,978 operations, 3,691 adjacencies, 2,042 human groups, five
SHA-256 folds, source-only reference/target files, coherent NPMI,
occurrence-weighted deterministic two-means, and every boundary and segment.

The independently reproduced totals are:

- 3,691/3,691 exact boundary decisions;
- 3,978/3,978 exact operation-to-motif assignments;
- 2,656/2,656 exact segment start/end/motif records;
- 44 global recurring motifs; and
- 3,978/3,978 total held-out profile mass.

Held-out session counts are 45, 55, 60, 62, and 65, with complete train/test
session disjointness in every fold. Every generated input row contains exactly
unit `value` and `fields{session,action}` and is object-equal to its
source-derived row. All NPMIs, centers, and cutoffs agree within `1e-12`; every
Rust decision, segment, and motif equals both the independent reconstruction
and approved Python raw outputs.

All five release commands returned status `ok`, wrote empty stderr, used
`agentpprof 0.2.37`, and conserved masses 521, 637, 1,330, 634, and 856. No
repair remains. The result proves exact implementation equivalence on the
existing post-hoc development population and nothing broader; it is not fresh
RQ3 confirmation or evidence for motif-name semantics or cross-family
generalization.
