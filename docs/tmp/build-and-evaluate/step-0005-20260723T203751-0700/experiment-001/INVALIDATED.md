# Experiment 001 — Invalidated

Experiment 001 is invalid and contributes no positive or negative scientific
result. Its v2 selector/oracles treated a Codex child stream ID as a semantic
native root, while production correctly joined that stream to its parent
root. The scorer then silently filtered the unexpected production root. Under
the corrected root resolver, the selected root overlaps the Step 0004
development set.

Consequently, its preflight score, B+C answers, edge counts, and claimed
root-disjoint split must not appear in a paper result or aggregate. The files
remain only as an engineering audit trail.

The current and four earlier invalidated freezes all contain the same 48
source SHA-256 values. The sorted source-inventory digest is
`811595797b7c31fb1b60b1590dc13d03b014490b70f068833dc325dfa5870420`.
The current archive is therefore sufficient to exclude the union of every
source opened during Experiment 001. Experiment 002 reparses all 48 archived
sources using the v3 semantic-root contract and also excludes the Step 0004
development archive.
