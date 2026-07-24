# Targeted WRITE Gate Outline

## Scope

This BUILD_AND_EVALUATE write is limited to:

1. replacing the RQ2 comparison with the independently reviewed current
   local-first result;
2. adding the Step 0072 evidence to `docs/evaluation.md` and project memory; and
3. correcting the factual provenance of CodeTrace A2 from Qwen3.6-27B to the
   actual independent Codex Agent batches plus root validation.

It does not modify the title, abstract, introduction, motivation,
contributions, thesis, four RQs, section structure, conclusion, or paper story.

## RQ2 paragraph roles

1. **Question and population:** retain all three complete public workloads,
   counts, HINT snapshot disclosure, and standard AP/MAP definition.
2. **Mechanism:** explain the local-first lexicographic candidate and the two
   information-matched baselines.
3. **Result table:** show Local+AgentProf, Local+Raw+Evidence, Local-only, and
   AgentProf-only MAP.
4. **Takeaway:** report the three positive intervals against local-only and the
   non-superiority result against matched raw+evidence; classify the experiment
   as adaptive mechanism evidence.
5. **Design connection:** retain the positive conclusion that the profile keeps
   source evidence and complements operation-local diagnosis.

## Evidence that must remain exact

- 1,756 trajectories, 27,346 operations;
- 614/400/220 target-bearing queries and 522 zero-positive trajectories;
- MAP `.8943/.5175/.3255` for Local+AgentProf;
- MAP `.8931/.5180/.3239` for Local+Raw+Evidence;
- MAP `.8632/.4106/.2087` for Local-only;
- MAP `.7906/.4324/.2593` for AgentProf-only;
- paired Local+AgentProf minus Local-only differences and intervals;
- all matched-raw intervals include zero;
- adaptive, not untouched, scope.

