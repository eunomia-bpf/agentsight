# Execution log

## Preparation and review

- Read the repository instructions, complete author instructions and story,
  evaluation frontier, experiment-design skill, plan template, and closest-work
  map before acting.
- Audited frozen Step 0087 and recorded why it is already the requested direct
  complete-hierarchy control in `step-0087-direct-control-audit.md`.
- Wrote `plan.md`; a fresh independent plan reviewer returned `APPROVE` in
  `plan-review.md`.
- Implemented the pinned flat backend in `flat_annotation/annotate.py` and its
  frozen downstream adapter in `flat_annotation/postprocess.py`.
- Validated both scripts with:
  `/usr/bin/python3 -m py_compile flat_annotation/annotate.py
  flat_annotation/postprocess.py`.
- Prepared and checked the exact 405-packet index and saved the only intended
  prompt-contract change in `prompt-contract.diff`.

## Operational preflight

Commands:

```text
/usr/bin/python3 flat_annotation/annotate.py preflight --timeout-seconds 1200
/usr/bin/python3 flat_annotation/postprocess.py preflight
```

The minimum-turn real Step 0087 packet completed through the actual pinned
GPT-5.6 backend, flat validator, unchanged assembly/root repair,
canonicalization, pprof production/readback, and frozen scorer. The operational
preflight used one call, 20,102 input tokens, 191 output tokens, 94 reasoning
tokens, 8.231 seconds of request time, and 1.171 seconds of downstream pipeline
time. It is not a paper result.

## Full backend run

Command:

```text
/usr/bin/python3 flat_annotation/annotate.py full --workers 4 --timeout-seconds 1200
```

The resumable run reached terminal status for all 405 trajectories. It produced
404 valid annotations and one terminal format failure. Ordinal 118 repeated an
unchanged adjacent complete path in both its initial response and its sole
ordinary format retry. The registered deterministic exception covered only an
otherwise-valid top-level session-ID mismatch and could not repair this mark
error without changing the response.

Five trajectories used the declared retry:

- ordinals 53 and 56: initial session-ID mismatch, then valid;
- ordinal 118: repeated unchanged path twice, terminal failure;
- ordinal 124: initial 1,200-second timeout, then valid;
- ordinal 160: initial repeated unchanged path, then valid.

The population accounting retained 410 model-call JSONL event streams and
stderr files, 404 accepted raw-mark files, all per-trajectory run records, and
the backend timing record. The 410 calls include ordinal 396's valid preflight
call because the resumable full command reused it as one of the 405 population
annotations. The first population request-to-terminal span is 2,064.284
seconds; the resumed full command alone is 2,030.232 seconds. No deterministic
format repair was applied.

## Terminal disposition

Commands:

```text
/usr/bin/python3 -m py_compile flat_annotation/postprocess.py
/usr/bin/python3 flat_annotation/postprocess.py incomplete
```

Because the full flat population was invalid, the full-population official
stages/scorer, assembly/canonicalization, pprof materialization, and paired
bootstrap were not run. The operational preflight scorer had run only after
its one prediction was fixed. No partial 404/405 result was interpreted. The
terminal attempt is recorded in `raw-results.json` and `results.md` as
incomplete and unscored.

No Git command was run. No prohibited paper, story, author-instruction, or
paper-submodule path was edited.

## Mechanical normalization amendment

After the complete run, the author approved deleting redundant transition
marks whose complete path is unchanged. This normalization is independent of
CodeTraceBench stages and scores and is accepted only when the expanded path
of every operation is identical before and after deletion. The full
405-trajectory pipeline and paired comparison are rerun after normalization;
no model response or per-operation semantic path changes. It removes only two
contract-invalid no-op mark boundaries.

The repair deleted starts 20 and 45 from ordinal 118, reducing its five sparse
marks to three while preserving all 47 expanded operation paths. The complete
pipeline then included all 405 trajectories. Direct hierarchy versus flat
reached B-cubed F1 0.763539 versus 0.753791 and boundary F1 0.479952 versus
0.468154. The paired hierarchy-minus-flat intervals were
[-0.003361, 0.023660] and [-0.007351, 0.031698], respectively.
