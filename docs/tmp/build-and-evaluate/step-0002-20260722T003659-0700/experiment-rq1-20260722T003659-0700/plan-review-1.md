# Independent RQ1 Plan Review — Round 1

**Reviewed:** 2026-07-22  
**Role:** fresh, read-only experiment-plan reviewer  
**Verdict:** **BLOCK**

The proposed architecture is appropriately minimal: reuse `agent-session`, add
only a thin repository projection, write plain rows, and render matplotlib
figures from frozen outputs. Five construct or execution defects must be fixed
before implementation.

1. **Path existence is not write durability.** Persistence must be restricted
   to artifact introductions that are observable in the trace. Existing-file
   writes have unknown content durability and cannot enter a persistence or
   three-way progress numerator. Validation of one mutation must occur before
   the same artifact's next mutation/delete; arbitrary later validation is only
   a secondary global association.
2. **Parallel worktrees cannot share identity by relative path.** Retain a
   worktree ID in the existing thin projection, key artifacts by worktree plus
   path, and query final state in the same worktree. Rename tests must cover an
   occupied destination, unseen source, unresolved previous path, and
   delete--recreate.
3. **Validation is adapter-derived, not a complete source-native set.** Narrow
   the claim to adapter-recognized successful test/check/build actions, publish
   the recognized range and vendor/effect/status coverage, and keep unknown
   status out of the success endpoint.
4. **Naive `1-KM` would mishandle competing outcomes.** A delete or superseding
   mutation is not ordinary end-of-observation censoring. Use competing-risk
   cumulative incidence or a clearly descriptive by-horizon curve; report
   denominators and risk counts. F4 must expose exact numerator/denominator and
   not call `final_path_exists` mutation durability.
5. **Longitudinal qualification is too weak.** Require at least two admitted
   sessions and one confirmed successful non-scope mutation per case; require
   at least one recognized successful validation for that panel. Report
   candidate/included/excluded sessions, exclusions, vendor/worktree coverage,
   and observation span. If fewer than four cases qualify, report coverage only
   and do not substitute projects or global path matches.

The reviewer requested one follow-up plan review after these minimum repairs.
No files were edited and no experiment was run by the reviewer.
