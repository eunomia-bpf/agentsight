# Real Preflight Report — RQ4 End-to-End Accounting

**Timestamp:** 2026-07-23T22:13:00-07:00  
**Status:** PASS; full execution admitted

## Scope

The registered 41-session CodeTrace long-horizon subset exercised every
approved command path:

1. fixed normalized operations plus released raw archives to source-only A2
   packets;
2. annotation assembly, root-only-prefix correction, validation, provider-token
   allocation, and name canonicalization;
3. raw-action and reference-corpus recurrence construction; and
4. fixed-mark operation- and token-width pprof construction.

Preflight timings are diagnostic and excluded from the paper result.

## Population and conservation

| Quantity | Observed |
|---|---:|
| Sessions | 41 |
| Source-native turns | 3,146 |
| Operations | 5,750 |
| A2 sparse marks after root repair | 554 |
| Operation mass | 5,750 |
| Provider-token mass | 117,303,194 |

Fresh packet export and deterministic assembly agree exactly on the session,
turn, and operation population. The root-only-prefix correction was enabled.

## Diagnostic timings

| Path | Wall time (s) | Peak RSS (KiB) |
|---|---:|---:|
| A2 source-packet construction | 105.45 | 269,812 |
| A2 assembly/root repair/validation | 0.46 | 175,308 |
| Name canonicalization | 0.33 | 65,848 |
| Raw-action pprof | 0.03 | 27,460 |
| Reference-corpus recurrence pprof | 0.43 | 243,060 |
| A2 fixed-mark operation pprof | 0.28 | 90,192 |
| A2 fixed-mark token pprof | 0.28 | 90,108 |

## Profile validation

All four `.pb.gz` artifacts load with stock `go tool pprof`.

| Profile | Reported mass | Expected mass | Result |
|---|---:|---:|---|
| Raw action | 5,750 operations | 5,750 | exact |
| Recurrence | 5,750 operations | 5,750 | exact |
| A2 operation replay | 5,750 operations | 5,750 | exact |
| A2 token replay | 117,303,194 tokens | 117,303,194 | exact |

The stock reader prints `Main binary filename not available` after `-top`
because these are language-agnostic pprof profiles rather than sampled native
binaries. It still reads the sample type, frames, and exact totals correctly;
the message is not a profile error.

## Decision

Preflight passes every registered completion condition. Proceed to three
complete 405-session repetitions for A2 packet construction, deterministic A2
postprocessing, raw-action construction, recurrence construction, and both A2
fixed-mark widths. Do not change any algorithm or input after this point.
