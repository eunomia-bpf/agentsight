# WRITE task: condensation pass 3b — front-matter and Design/RW tightening

You are an autonomous writing agent working inside
`/home/yunwei37/workspace/agentsight-research-semantic-flamegraph`.
Edit EXACTLY ONE file: `docs/paper/main.tex`. No git commands. Never touch
`docs/agentpprof-paper/`. Rules identical to pass 3a: keep the thesis
sentence (3 locations, verbatim), all RQ titles, all tables, all figures,
every number, every one of the 42 unique `\cite` keys. Compress WORDING
only; every paragraph keeps its rhetorical role (problem, gap, insight,
model, system, contributions...). This paper's story spine is canonical:
do not reorder sections or paragraphs, do not merge two paragraphs into
one, do not drop a contribution. Rewritten sentences get updated Chinese
comments.

## Tighten A — Introduction (target -12 source lines)

Compress within each of paragraphs 1-6 (background, problem, structural
cause, existing solutions, model, system): remove restatements and filler
("increasingly", "in particular"), fuse subordinate clauses. Paragraph 7
(results) and 8 (contributions) may only lose filler words; their numbers
and enumerate structure stay.

## Tighten B — Design (target -10 source lines)

- The paragraph after the architecture figure ("The design has three
  explicit objects...") and the following D1-D3 mapping paragraph: fuse
  overlapping clauses.
- In "Recursive Operation Annotation": the coarse-to-fine narrative
  paragraph and the Agent-backend binary-policy paragraph repeat the
  stay/pop/push idea; state it once, keep the formal policy sentence
  intact.
- The CodeTraceBench A2-run paragraph ("The complete CodeTraceBench A2 run
  uses independent Codex Agent workers...") may move its
  representation-repair sentence to the existing appendix subsection
  `app:canonicalization` (append there), keeping one summary clause.

## Tighten C — Implementation (target -8 source lines)

Compress "Input reconstruction" and "Annotation workspace" paragraphs
(fuse enumerations; keep the three-file contract, validation guarantees,
and warning types). Keep the "Profile export" paragraph verbatim (product
boundary statement).

## Tighten D — Related Work (target -8 source lines)

Fuse sentences within each existing paragraph; every citation stays; no
comparison claim changes polarity or strength.

## Validation and deliverables

1. Compile clean; 0 undefined refs/citations; 42 cite keys; thesis x3;
   0 overfull hboxes.
2. Report: total pages, References end page, figure pages still sharing
   with body. Target: References ends on page 10 or earlier.
3. `write-report.md` in THIS directory: per-section before/after line
   counts and the page layout report.
