# RepairBranch

A mechanistically-grounded counterfactual replay framework for Remaining Useful Life (RUL)
prognostics and maintenance-timing optimization, evaluated on the NASA C-MAPSS FD001
turbofan-engine degradation benchmark.

Most predictive-maintenance systems stop at predicting RUL. RepairBranch goes one step
further: it mechanistically re-simulates an engine's own observed degradation trajectory
under a counterfactual repair at a different point in time, then translates the simulated
life extension into a cost-benefit comparison across repair-timing scenarios.

## Pipeline

1. **`scripts/01_preprocess.py`** — Loads NASA C-MAPSS FD001, computes RUL labels (clipped
   at 125 cycles), drops constant sensors.
2. **`scripts/02_eda.py`** — Exploratory analysis: sensor degradation trends, RUL
   correlation, RUL distribution.
3. **`scripts/03_model.py`** — Trains a Random Forest RUL regressor on rolling-window sensor
   features, evaluated with grouped 5-fold cross-validation and the NASA PHM'08 scoring
   function.
4. **`scripts/04_counterfactual.py`** — The core contribution: `Algorithm 1`, a
   counterfactual maintenance-timing replay engine that mechanistically re-simulates each
   engine's own future degradation increments from a partially restored baseline at three
   repair timings (50%, 70%, 85% of observed life), plus an illustrative cost-benefit model.

## Results (FD001, 100 train / 100 test engines)

| Metric | Value |
|---|---|
| Test RMSE | 18.9 cycles |
| Test MAE | 13.6 cycles |
| Test R² | 0.794 |
| NASA PHM'08 score | 1044.1 |

Later repairs consistently produce larger simulated life extension (13.8 cycles at 50% life
→ 22.8 cycles at 85% life), traced to the back-loaded, accelerating shape of the observed
degradation curves.

## Repository layout

```
RepairBranch/
├── scripts/        # Full analysis pipeline (preprocessing → model → counterfactual engine)
├── figures/         # All 9 result figures used in the paper
├── tables/          # Result tables (CSV) and a consolidated Excel workbook
├── paper/           # IEEE-format research paper (.docx) and its generation script
└── README.md
```

## Dataset

This project uses NASA's C-MAPSS FD001 turbofan engine degradation dataset, publicly
available from the NASA Prognostics Data Repository. Raw data files are not included in
this repository; the preprocessing script expects `train_FD001.txt`, `test_FD001.txt`, and
`RUL_FD001.txt` in a local `data/` directory.

## Paper

The full IEEE-format research paper (`paper/RepairBranch_IEEE_Research_Paper.docx`, 8
pages) includes the complete methodology, Algorithm 1 pseudocode, all figures and tables,
and 15 references. `paper/build_paper.py` documents exactly how the paper was assembled.

## Limitations

FD001 covers a single operating condition and single fault mode; the cost figures used in
the cost-benefit analysis ($50,000 failure / $8,000 repair / $150 per cycle) are illustrative
placeholders, not figures sourced from a real maintenance program. See the paper's
Discussion section for the full limitations list.
