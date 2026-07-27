# Independent result review

## Verdict

**APPROVED — no blockers.**

The independent reviewer classified the run as valid, the heterogeneity
hypothesis as supported, and the paper value as supporting evidence plus a
workload boundary. The recommended paper decision is to position the corpus as
author-associated mixed-initiative longitudinal cases: human involvement is
both a natural-use feature and a confound for autonomy, vendor, and
outcome-association claims.

## Independently checked

- 551 project-attributed memberships, 550 unique projected session IDs, and
  181,303 projected Agent actions reconcile.
- The mutation input has 13,906 rows: 771 deletes and 13,135 non-delete
  eligible rows.
- Unique-session totals are 7,804 user-role messages, 1,774,594 characters,
  and 425,434 approximate word-like tokens. Project attribution yields 7,852
  messages because one 48-message session maps to two projects.
- Unique styles are 337 startup-only, 195 guided, 17 subagent-only, and one
  other zero-human-record session.
- All 1,049 project/source mappings (1,048 unique files) are readable and
  parsed.
- A separate native metadata rescan reproduced 515 Codex subagent, 254 user,
  and 12 legacy-user files. Excluded subagent sources export zero human
  messages while their 16,846 projected actions remain in the all-action
  denominator.
- There are 7,272 unique follow-ups; 7,035 have adjacent comparable actions,
  3,479 change tool family, 2,296 have paths on both sides, 906 change path
  set, and 855 become disjoint.
- There are 634 explicit interruption/abort markers, of which 593 precede a
  later human message.
- The 6,779 activity-bearing closed intervals sum to 789.8 hours of activity
  envelope and 2,228.5 hours of post-activity inactive gap. The report
  correctly refuses to equate these with attention, CPU time, or proven Agent
  waiting.
- Reuse and validation outcome partitions close exactly to every non-delete
  denominator; zero-mutation sessions are retained.
- Guidance-density groups are constructed within project × vendor and are
  described without causal language.
- Output hashes, figure readability, and write scope passed. No Git invocation,
  `docs/paper/` write, or `rq7-heldout-20260726/` access was found.

## Non-blocking concerns and disposition

- The report did not initially summarize the explicit-interruption subset's
  next-action changes. Addressed: the report now gives the 577 comparable
  interrupted follow-ups, including tool and path switches.
- Twelve legacy Codex files lack `thread_source`; four user-role messages come
  from `exec`-origin files and cannot be distinguished as directly typed versus
  wrapper-submitted. Addressed: `native_source_app` is exported and the caveat
  is explicit in the reconstruction contract.
- “Redirected work” was stronger than the next-tool/path evidence. Addressed:
  the dataset discussion now says that the author supplied follow-up
  instructions.
- Figure 04's reuse and validation panel titles were ambiguous. Addressed with
  outcome-specific titles.
- Quantile-threshold ties make the high/low groups unequal in size. Addressed:
  the method text now states that ties are retained and groups are not forced
  to equal size.
