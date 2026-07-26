# Pilot results: direct multi-level annotation vs A2

Status: **COMPLETE / VALID**

## Deterministic slice

- first 40 trajectory IDs in sorted order;
- 1,338 operations, 249 official stages, and 32 task clusters;
- source-only packets; official stages were opened only by the unchanged scorer.

## Same-slice metrics and gate

| Method | B³ P | B³ R | B³ F1 | Boundary P | Boundary R | Boundary F1 |
|---|---:|---:|---:|---:|---:|---:|
| Direct multi-level | 0.917259 | 0.637536 | 0.752235 | 0.377483 | 0.818182 | 0.516616 |
| A2 | 0.950021 | 0.507785 | 0.661825 | 0.305606 | 0.808612 | 0.443570 |
| Multi-resolution recurrence | 0.770809 | 0.601379 | 0.675634 | 0.207595 | 0.392344 | 0.271523 |

Direct minus A2 B³ F1: `+0.090410`; paired task-cluster 95% interval `[+0.048443, +0.128938]`.

Direct minus A2 boundary F1 paired task-cluster 95% interval: `[+0.033803, +0.112469]`.

Binding gate (`direct B³ F1 >= A2 B³ F1 - 0.03`): **PASS**.

## Pilot cost

- successful trajectories: 40/40;
- Codex calls: 41 (1 format retries);
- summed backend wall: 858.846 s;
- active backend wall across interrupted/resumed worker waves: 232.993 s;
- input/output tokens: 1,088,544 / 25,310.

Context only: adopted A2 retained no model token/time telemetry; its 405-trajectory artifact-time envelope was 3,261.89 s. Step 0086's 42-record automatic pass used 7,740.107 s summed backend wall, 2,674.314 s reconstructed three-worker critical path, 15,231,328 input tokens, and 311,097 output tokens.

## Validity

All 40 trajectories completed; the interrupted cache was reused only after response validation. The one invalid orphan response consumed its single format retry. Operation and token mass are conserved, canonical replay has zero adjacent display-path collisions, and both profiles load in stock pprof.

The one-trajectory recipe-check score remains diagnostic only and is not included in this pilot result.
