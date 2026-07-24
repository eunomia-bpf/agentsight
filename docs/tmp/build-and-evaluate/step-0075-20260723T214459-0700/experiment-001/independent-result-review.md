# Independent Result Review — Step 0075 RQ4

**Review method:** `research-experiment-design` RESULT REVIEW  
**Run-validity verdict:** **VALID**  
**Registered-hypothesis verdict:** **SUPPORTED**  
**Must-fix count:** 0 remaining; one reporting correction verified

## Independent judgment

The full execution is valid and the registered deterministic hypothesis is
supported. The retained artifacts contain three successful observations for
every registered deterministic component. The raw manifests reproduce the
complete population, the post-annotation outputs are byte-identical to the
adopted A2 inputs, all twelve profiles load in stock pprof and conserve their
registered mass, and both fixed-mark replay medians are 1.17 seconds, below
the predeclared two-second threshold.

This result has useful paper value because it replaces a fixed-input-only RQ4
statement with measured source-packet construction, deterministic
postprocessing, and fixed-mark replay costs. It still does not measure the A2
Agent/model inference component. The report preserves that limitation and
does not use the filesystem timeline to infer model time or annotation-cost
dominance.

## Population and completion audit

I independently read the three fresh packet manifests, their twelve batch
files per repetition, all assembly/canonicalization stdout records, and all
profile stdout records.

| Check | Rep 1 | Rep 2 | Rep 3 | Registered |
|---|---:|---:|---:|---:|
| Sessions | 405 | 405 | 405 | 405 |
| Unique manifest session IDs | 405 | 405 | 405 | 405 |
| Source-native turns | 17,148 | 17,148 | 17,148 | 17,148 |
| Operations | 20,866 | 20,866 | 20,866 | 20,866 |
| Packet batches | 12 | 12 | 12 | 12 |
| Sum of batch session counts | 405 | 405 | 405 | 405 |
| Sum of batch turn counts | 17,148 | 17,148 | 17,148 | 17,148 |
| Sum of batch operation counts | 20,866 | 20,866 | 20,866 | 20,866 |

The registered historical waves contain 41 and 364 unique sessions,
respectively. Their session sets are disjoint, their union has 405 members,
and that union is exactly equal to each fresh full-manifest session set. Their
turn counts sum to `3,146 + 14,002 = 17,148`, and their operation counts sum
to `5,750 + 15,116 = 20,866`.

Every assembly stdout record independently reports 405 sessions, 17,148
turns, 20,866 operations, 5,752 marks, 5,537 pre-canonical semantic names,
20,866 count mass, 494,862,929 provider-token mass, and enabled
root-only-prefix correction. Directly summing the 20,866 JSONL rows in each
materialized input reproduces 20,866 count mass and 494,862,929 token mass;
these are not accepted only from stdout.

## Timing and memory recomputation

All 21 full-run timing JSON files have exit status zero. Sorting each set of
three wall times and taking the middle value reproduces every reported median;
taking the largest RSS value reproduces every reported maximum.

| Component | Raw wall times (s) | Recomputed median (s) | Recomputed max RSS (KiB) |
|---|---:|---:|---:|
| A2 source-packet construction | 500.07 / 505.64 / 501.64 | 501.64 | 292,664 |
| A2 assembly/root repair/validation | 1.21 / 1.16 / 1.18 | 1.18 | 256,388 |
| A2 name canonicalization | 2.35 / 2.35 / 2.36 | 2.35 | 195,272 |
| Raw-action pprof | 0.10 / 0.11 / 0.10 | 0.10 | 86,008 |
| Reference-corpus recurrence pprof | 0.54 / 0.49 / 0.49 | 0.49 | 243,312 |
| A2 fixed-mark operation pprof | 1.17 / 1.17 / 1.19 | 1.17 | 320,540 |
| A2 fixed-mark token pprof | 1.19 / 1.17 / 1.17 | 1.17 | 320,432 |

The matched assembly-plus-canonicalization sums are independently
`3.56 / 3.51 / 3.54` seconds, with median 3.54 seconds. The reported
deterministic A2 accounting subtotal is also arithmetically correct:
`501.64 + 3.54 + 1.17 = 506.35` seconds. It remains correctly labeled as a
backend-specific accounting convenience rather than a matched total against
raw action or recurrence.

## Determinism and A2-equivalence audit

The three source-packet directories are byte-identical. Recomputing
`sha256sum *.json | sha256sum` inside each directory gives the reported
aggregate digest:

`0205298933ba555e1c737f6f31e649cd8a4ca60d67f58cda19a7887aa74bb2d6`.

The three fresh postprocessing outputs are mutually byte-identical and also
byte-identical to the adopted A2 profile inputs:

| Artifact | Recomputed SHA-256 | Adopted A2 equal |
|---|---|---|
| Canonical operation marks | `d8c78a552c5db9d3eb9735b15568d81b555740f7e419b7556f33323dae5d6d68` | yes |
| Canonical predictions | `a2e6162c7f97d6ccb0653fc38a2c48ee351a5281b7f60b18cc2a031ce5b18432` | yes |
| Count-width operation input | `ab6cecc511d747c275f04a8c7106144495c86c23f19777c8832507ab0217005f` | yes |
| Token-width operation input | `d9c181c0bff6a032311fbf96df0bd10a682270866b27ad646538751b70fa5a16` | yes |

Thus the replay commands' use of the adopted fixed inputs is equivalent to
using any of the three freshly reconstructed outputs.

## Independent stock-pprof audit

I ran `go tool pprof -top` on every one of the twelve full profiles rather
than relying on the producer stdout. All twelve load successfully. The stock
reader reports the following sample types and totals in all three repetitions:

| Method | Stock sample type | Stock total | Unique stacks from producer | Bytes | Recomputed profile SHA-256 |
|---|---|---:|---:|---:|---|
| Raw action | operations | 20,866 | 9 | 11,225 | `479b703bfefb1abeeb9f617ca90e8f1a39e7cd0494615895c378307588aec1bb` |
| Recurrence | operations | 20,866 | 534 | 21,804 | `f4aa4ca237fb4e8deca3ae4df877801207bffba7c06f4411ad0e41a3f2242197` |
| A2 operation | operations | 20,866 | 19,874 | 789,333 | `e6789fb2e6e07575b65a46a1399cb5c14c81d00b4c59422fbcd43c66942f695b` |
| A2 token | tokens | 494,862,929 | 19,874 | 852,435 | `e5d3d5ac714cff926003f21178c8215b401d19b9496203955fe8a0ac9b454f4a` |

Within each method, all three profile hashes and sizes are identical. The
stock reader's `Main binary filename not available` diagnostic is expected
for these language-agnostic profiles and does not prevent it from decoding
the sample type, frames, or exact total.

## Historical mtime-envelope judgment

The retained mtimes, batch counts, and coverage reproduce the report:

| Wave | Start mtime | Last nonempty annotation mtime | Recomputed span | Annotation files / sessions |
|---|---|---|---:|---:|
| Long horizon | 2026-07-22 13:59:35.601683047 -0700 | 2026-07-22 14:08:38.771010548 -0700 | 543.169327501 s | 3 / 41 |
| Complement | 2026-07-22 15:00:35.493725941 -0700 | 2026-07-22 15:45:54.215905994 -0700 | 2,718.722180053 s | 12 / 364 |
| Sum | — | — | 3,261.891507554 s | 15 / 405 |

All fifteen annotation files are nonempty and collectively contain one row
for each of 405 unique sessions. Those rows exactly match their corresponding
packet-manifest session sets. The report's rounded `543.17`, `2,718.72`, and
`3,261.89` seconds are correct.

The phrase **historical artifact-time workflow envelope** is honest in the
full report because it is immediately defined as mutable filesystem metadata,
the two waves are reported separately before their sum, and the text states
that the value mixes unknown inference, dispatch, scheduling, parallelism,
idle time, and file writing. Crucially, it is called neither Agent/model time
nor a lower bound, and it is not added to the fresh stopwatch measurements.
It therefore provides artifact chronology only; it does not close the A2
inference-cost gap.

## Cost/quality row audit

Every cost value in the main cost/quality table matches the recomputed timing
medians. The recurrence quality values `0.662740 / 0.265571` and A2 values
`0.704113 / 0.393916` match the independently reviewed complete RQ3 results.

The originally submitted raw row did **not** pair the timed method with its
corresponding quality result:

- The registered and executed RQ4 command uses `--stack action`. Its input has
  nine unique `fields.action` values, and producer stdout confirms
  `stack: "action"` and nine unique profile stacks.
- The reported B-cubed `.541` is the rounded `0.541070` score for the different
  `raw_action_key_change` control. In the same input, that key is stored as
  `fields.action_detail` and has 400 unique values.
- The already completed matched score for the actually timed coarse
  `action_change` control is B-cubed F1 `0.473242` and exact-boundary F1
  `0.267524`.

The raw component remains a legitimate non-semantic serialization control,
and this mismatch did not enter the registered hypothesis. During review, the
result table was corrected to **Coarse action**, B-cubed F1 `0.473242`, and
exact-boundary F1 `0.267524`. The corrected row now matches the timed method
and its completed quality score.

## Registered decision

The three registered support conditions all pass:

1. **Population and A2 reproduction:** pass. Fresh source adaptation and
   postprocessing reproduce the complete population and adopted A2 files.
2. **Readable, mass-conserving profiles:** pass. All twelve profiles load in
   stock pprof and conserve exact operation or token mass.
3. **Replay threshold:** pass. Both fixed-mark replay medians are 1.17 seconds,
   below the registered two-second threshold.

The registered deterministic hypothesis is therefore **SUPPORTED**. This is
not support for a claim about A2 Agent-inference latency, total online
profiling cost, live-capture overhead, pricing, or universal hardware scaling.

## Research value, paper impact, and next decision

- **Research value:** useful supporting RQ4 evidence. It closes the
  deterministic construction/replay accounting gap on the complete real
  population.
- **Paper impact:** the paper may report the measured 501.64-second source
  adaptation, 3.54-second deterministic postprocessing, and 1.17-second
  fixed-mark replay decomposition, with the host and warm-cache scope.
- **Remaining evidence gap:** A2 model/provider inference time and usage remain
  unavailable. The 54.36-minute artifact chronology is not a substitute.
- **Next paper decision:** proceed to WRITE. The single table correction has
  been verified; no new experiment or model run is required.

## Resolved must-fix

1. The raw cost/quality row had to be made method-consistent. The timed
   `--stack action` control is now labeled **Coarse action** and paired with
   its matched quality values, B-cubed F1 `0.473242` and exact-boundary F1
   `0.267524`, while retaining its non-semantic control role.

**Correction verified; zero must-fixes remain.**
