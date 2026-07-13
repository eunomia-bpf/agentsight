# Real Preflight Report: RQ2 Hodoscope Representation Choice

**Timestamp:** 2026-07-12  
**Plan:** `experiment-plan.md`, approved after three serial reviews  
**Run type:** one real end-to-end seed; not a paper result  
**Status:** PASS

## Actual Inputs

- Hodoscope paper source commit:
  `71d416be5ded11a4a65d671efdf602e4564e0803`.
- Hodoscope source commit:
  `e9b6930d4a0149cf76b15190a85dc9d9ff78a860`.
- Hugging Face dataset revision:
  `17c395e8c6ce8a4148251064079e31686c422390`.
- Downloaded official files: all five
  `analysis_files/swebench/*.hodoscope.json` files, about 251MB.
- Python 3.12.3; NumPy 2.5.1; scikit-learn 1.9.0; HDBSCAN 0.8.44;
  psutil 7.2.2; Bokeh 3.9.1.
- Comparative runner:
  `script/hodoscope_representation_eval.py`.

The SHA-256 digests of the five official analysis files are retained in the
terminal transcript and can be regenerated from the artifact directory.

## Installation Deviation And Repair

Installing the published `hodoscope==0.2.4` dependency set initially failed:
the package declares Python 3.11+, but its unconstrained optional `pacmap`
dependency resolved through `numba==0.53.1` to `llvmlite==0.36.0`, which only
supports Python below 3.10.

This was a runner defect, not a scientific-plan change. The repaired environment
uses the exact pinned Hodoscope source and installs only dependencies exercised
by the official Table 2 path and comparative extension. PaCMAP, TriMAP, UMAP,
Docent fetching, and LLM APIs are not used: the planned projection is official
t-SNE and the official summaries/embeddings are already released. The real
preflight was rerun from the beginning after repair.

## Expanded Command

```bash
<loop>/artifacts/venv/bin/python \
  script/hodoscope_representation_eval.py \
  --mode preflight \
  --paper-root <loop>/artifacts/hodoscope_paper-71d416be5ded11a4a65d671efdf602e4564e0803 \
  --data-root <loop>/artifacts/hodoscope-data \
  --out-dir <loop>/raw \
  --seeds 10 \
  --bootstrap-seed 20260712
```

Here `<loop>` is
`docs/tmp/cycle-0001-20260711T164850-0700/01-experiment-gate/loop-rq2-02`.

## Official Inventory Check

The real decoded files exactly matched the plan and paper repository:

| Quantity | Observed |
|---|---:|
| Total actions | 11,855 |
| Four reference cohorts | 7,849 |
| iQuest target actions | 4,006 |
| Published iQuest oracle positives | 132 |
| Embedding matrix | 11,855 x 3,072 |

Per-cohort actions were iQuest 4,006; Qwen3-Coder 3,756; DeepSeek 2,161;
o3 1,236; and GPT-4.1 696.

## Real Seed Path

Official seed 1 selected 50% of every cohort:

| Quantity | Observed |
|---|---:|
| Paired sample actions | 5,927 |
| Reference actions | 3,924 |
| Target actions | 2,003 |
| Target oracle positives | 65 |

The run actually decoded 3,072-dimensional embeddings, executed Hodoscope's
balanced t-SNE, KDE density contrast and FPS, built the flat/native/recursive
representations, and materialized all four complete action orders.

## Path Results — Not Confirmatory Evidence

| Method | First-hit rank | Target fraction | Characters | Hits@20 | Method runtime |
|---|---:|---:|---:|---:|---:|
| Hodoscope | 3 | 0.150% | 8,692 | 1 | 0.93s after shared t-SNE |
| Flat semantic | 4 | 0.200% | 7,170 | 1 | 30.54s |
| Native turn | 103 | 5.142% | 236,920 | 0 | 0.28s |
| Recursive semantic | 4 | 0.200% | 7,399 | 1 | 34.02s |

Peak process RSS reached about 1.44GB. These values establish only that the
real metric and mechanism paths engage. They are not interpreted because the
approved experiment requires ten paired seeds and the complete-corpus phase.

## Correctness Checks

- Every method wrote exactly 2,003 target rows.
- Every action key was unique within every permutation.
- Every unscored ranking contained no `oracle_positive` field.
- The scored copy was written only after the complete unscored permutation.
- Independent recomputation from each scored permutation reproduced ranks
  3/4/103/4 exactly.
- Hodoscope's first hit was inside its unchanged official top-500 prefix.
- Non-Hodoscope rows use `null`, not a false claim, for official-prefix status.
- All action keys resolve to stored real action text and source order.

## Preflight Decision

The official data, oracle, projection, Hodoscope baseline, all three matched
representations, complete-permutation contract, raw output paths, and metric
recomputation are executable. The approved plan advances to FULL RUN without
changing the RQ, oracle, scoring, hierarchy, or interpretation rules.
