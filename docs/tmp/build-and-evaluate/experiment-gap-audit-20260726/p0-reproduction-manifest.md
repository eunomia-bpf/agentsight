# P0 reproduction manifest

Date: 2026-07-26

Scope: the final-HEAD RQ1--RQ4 numbers and five figures consumed by
`docs/paper/main.tex` and `docs/paper/supplement.tex`, plus the final RQ1/RQ3
extension numbers.  Run every command below from the repository root.  The
released-row commands do not read live `$HOME` or the private native-session
exports.

## One-command number ledger

Script:

- `docs/tmp/build-and-evaluate/experiment-gap-audit-20260726/reproduce_p0_numbers.py`

Command:

```bash
python3 docs/tmp/build-and-evaluate/experiment-gap-audit-20260726/reproduce_p0_numbers.py
```

This command recomputes the corpus totals, all six RQ1
persistence/reuse/validation fractions, the RQ2 `6/6` coverage and lane
range, the RQ3 episode/repeat/concentration quantities, the RQ4 per-project
and total component/boundary counts, and the paper-facing extension
aggregates.  Its hard gates require RQ2 `6/6`, the RQ2 zero-mutation upper
endpoint `86.1%`, and RQ4 `121/111`.

## Figure commands

The following commands regenerate the five paper figures from released CSV
rows:

```bash
python3 docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/scripts/plot_rq1.py \
  --input docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq1-raw \
  --output docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq1-figures

python3 docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/scripts/plot_rq2.py \
  --input-raw docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq2/raw \
  --output docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq2

python3 docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/scripts/plot_rq3.py \
  --input-raw docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq3/raw \
  --output docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq3

python3 docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/scripts/plot_rq4.py \
  --input-raw docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq4/raw \
  --output docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq4
```

Outputs copied into the paper:

```bash
cp docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq1-figures/rq1-activity-progress.pdf \
  docs/paper/figures/rq1-activity-progress.pdf
cp docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq1-figures/rq1-progress-curves.pdf \
  docs/paper/figures/rq1-progress-curves.pdf
cp docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq2/figures/rq2-validation-dynamics.pdf \
  docs/paper/figures/rq2-validation-dynamics.pdf
cp docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq3/figures/rq3-rework-structure.pdf \
  docs/paper/figures/rq3-rework-structure.pdf
cp docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq4/figures/rq4-component-continuity.pdf \
  docs/paper/figures/rq4-component-continuity.pdf
```

The released-row render was executed into a fresh temporary directory.  For
all five PDFs, `pdftotext -layout` output exactly matched the PDFs copied into
`docs/paper/figures/`.

## Scripts

- `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/scripts/headline_rq1.py`
- `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/scripts/plot_rq1.py`
- `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/scripts/plot_rq2.py`
- `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/scripts/plot_rq3.py`
- `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/scripts/plot_rq4.py`
- `docs/tmp/build-and-evaluate/rq-extensions-20260726/analyze_rq_extensions.py`
- `docs/tmp/build-and-evaluate/experiment-gap-audit-20260726/reproduce_p0_numbers.py`

## Released input rows

RQ1:

- `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq1-raw/rq1-summary.csv`
- `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq1-raw/rq1-artifacts.csv`
- `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq1-raw/rq1-mutations.csv`

RQ2:

- `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq2/raw/rq2-trajectory.csv`
- `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq2/raw/rq2-cycles.csv`
- `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq2/raw/rq2-coverage.csv`

RQ3 repeated-mutation:

- `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq3/raw/rq3-artifact-load.csv`
- `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq3/raw/rq3-episodes.csv`
- `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq3/raw/rq3-summary.csv`

RQ4:

- `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq4/raw/rq4-components.csv`
- `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq4/raw/rq4-boundaries.csv`

RQ1/RQ3 extensions:

- `docs/tmp/build-and-evaluate/rq-extensions-final-20260726/rq-summary.json`
- `docs/tmp/build-and-evaluate/rq-extensions-final-20260726/reconciliation.csv`
- `docs/tmp/build-and-evaluate/rq-extensions-final-20260726/rq1-dormancy-summary.csv`
- `docs/tmp/build-and-evaluate/rq-extensions-final-20260726/rq1-lifecycle-episodes.csv`
- `docs/tmp/build-and-evaluate/rq-extensions-final-20260726/rq1-revivals.csv`
- `docs/tmp/build-and-evaluate/rq-extensions-final-20260726/rq3-windows.csv`
- `docs/tmp/build-and-evaluate/rq-extensions-final-20260726/rq3-turnover-summary.csv`
- `docs/tmp/build-and-evaluate/rq-extensions-final-20260726/rq3-turnover-pooled.csv`
- `docs/tmp/build-and-evaluate/rq-extensions-final-20260726/rq3-cooling.csv`
- `docs/tmp/build-and-evaluate/rq-extensions-final-20260726/rq3-cooling-pooled.csv`

## Paper-number mapping

| Paper locations | Numbers | Reproduction source |
|---|---|---|
| `main.tex:46-50,114-117,245-248`; `supplement.tex:50-54,635-636` | 551 sessions; 181,303 actions; 551/176,288 attributed; 5,746 artifacts; 13,906 rows; reuse/rho; 13,860 episodes; repeat/concentration ranges | `rq1-summary.csv`, row counts in `rq1-artifacts.csv` and `rq1-mutations.csv`, `rq3-summary.csv`, `reproduce_p0_numbers.py` |
| `main.tex:269-275,299-300`; `supplement.tex:492-501,519-520,625-627` | six persistence, reuse, validation fractions; `74.6--90.8%`; `42.0--86.7%` | `rq1-summary.csv`, `rq3-summary.csv` |
| `main.tex:277-278`; `supplement.tex:546-583` | dormancy/revival ranges, per-project fractions, transition counts, mutation-revival counts, gap median/p90 | `rq1-dormancy-summary.csv`, `rq-summary.json` |
| `main.tex:294-300`; `supplement.tex:600-617` | repaired `6/6`; seven lanes; `29.3--86.1%`; maxima `1--817`; validation fractions | `rq2-coverage.csv`, `rq2-cycles.csv`, `rq1-summary.csv` |
| `main.tex:334-336`; `supplement.tex:649-654` | 121 components, 111 boundaries, three of six reach 20 | `rq4-components.csv`, `rq4-boundaries.csv` |
| `supplement.tex:710-728` | 3,372/1,666 pairs; turnover/replacement; endpoint/continuous retention | `rq3-turnover-pooled.csv`, `rq3-cooling-pooled.csv`, `rq-summary.json` |

## Full local derivation

The source derivation used the same private final-HEAD event exports and was
also rerun successfully:

```bash
python3 docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/scripts/plot_rq2.py \
  --rq1-root docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq1-raw \
  --output docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq2
python3 docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/scripts/plot_rq3.py \
  --rq1-root docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq1-raw \
  --output docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq3
python3 docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/scripts/plot_rq4.py \
  --rq1-root docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq1-raw \
  --output docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq4
python3 docs/tmp/build-and-evaluate/rq-extensions-20260726/analyze_rq_extensions.py \
  --rq1-root docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq1-raw \
  --output docs/tmp/build-and-evaluate/rq-extensions-final-20260726
```

The private `rq1-raw/events/*.json.gz` files are local derivation inputs, not
release-package dependencies.  The released CSV rows listed above are the
clean-room inputs for the number and figure gates.
