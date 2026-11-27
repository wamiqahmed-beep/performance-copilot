# Phase 2 reproduction and demonstration

Open `index.html` directly, or use the GitHub Pages URL. Keep `model-data.js` and `phase2.js` next to it. Python is needed only to train/regenerate exports.

## Reproduce

Use Python 3.12 and an isolated environment:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python train_models.py
```

The first run writes the extended P&L, validation results and frozen design. It does not score the reserved July–December 2025 test. Review the validation metrics and cluster evidence. Once the design is fixed, run:

```powershell
.\.venv\Scripts\python train_models.py --finalize
```

This records the final test once and generates the dashboard assets. On subsequent runs it reads the recorded final evaluation instead of testing again. A changed script or dataset fails the frozen-design check. Preserve the supplied `model-output` files as the evaluation record. A fresh reproduction in a separate directory should yield the same metrics with the pinned environment; never delete the evaluation record to tune on its results.

`model-output/frozen-design.json` contains dates, features, selected settings, seed and SHA-256 hashes. `final-evaluation.json` contains all held-out predictions, scores, coefficients and errors. A separate production fit uses all history for the January 2026 estimate; those fitted historical results are not reported as test accuracy.

## Six model rules

1. **Baselines:** previous-month and same-month-prior-year revenue. Ridge regularisation is selected by validation MAE. Final dashboard reports both comparisons whether the model wins or loses.
2. **Time split:** eligible 2021–2024 rows train; January–June 2025 validates; July–December 2025 tests. The model is fixed through the test, with lag observations becoming available each month. Countries in the same month share the split. No shuffling.
3. **Availability:** revenue lags 1/2/12, past-only rolling means 3/12, target-month calendar features, elapsed time, country, last observed FX and its latest change. Target-month actual sales, units, COGS, bridge contributions and realised FX are excluded. Budget is used to compare a prediction with the plan, not to construct the regression target.
4. **Threshold:** this is regression, not yes/no classification. Apply the assigned business rule to the continuous landing estimate: (prediction / next-month budget) − 1. Strictly greater than +5% or less than −5% triggers the forecast flag.
5. **Segments:** compare K-means k=2–4 with elbow and silhouette charts; standardise four bridge contributions relative to budget, avoid singleton groups where possible and favour fewer interpretable groups when separation is similar. Fit the scaler and cluster centres through June 2025; assign the latest trailing-year profiles using those centres. Six countries are a substantial limitation.
6. **Relationships:** preserve the original synthetic data. Earlier history extends its annual sinusoidal seasonality (13% amplitude), gradual time growth (0.8% of base per month), persistent country demand offsets, oscillating unit deviations, segment prices and time-varying FX. The learner sees observable lags/calendar/FX, not the generator's hidden formulas or future actuals. Sales mix arises from brand/channel unit differences. This smooth deterministic simulation is easier than real business data and has no unanticipated shocks. Inherited FX variation in EUR markets is illustrative, not a realistic exchange-rate series.

## Files and columns

- `dummy-pnl.csv`: unchanged Phase 1 source, 2023–2025.
- `model-output/updated-pnl.csv`: 2020–2025, 3,888 rows; original 13 columns retain their definitions in the assignment note.
- `model-output/country-predictions.csv`: target month, as-of month, country, next-month budget EUR, prediction EUR, predicted proportional gap, forecast flag, carried-forward FX assumption and segment ID.
- `model-output/country-segments.csv`: country, trailing-year revenue/budget EUR, signed volume/mix/price/FX contributions as fractions of budget, segment ID.
- `model-output/test-predictions.csv`: target month/country, actual/budget EUR, predicted EUR, signed euro error and baseline lag values.
- `model-data.js`: generated static bundle, including P&L and model results, used by the offline dashboard. No browser-side training.
- `model-note.html`: one-page printable model note.

The model pages and January forecast have fixed, explicit scopes. Country filtering applies; descriptive period/brand/channel filters do not silently change country-total forecasts or the global held-out evaluation. Predictions are unavailable for other target months rather than being fabricated from filters.

## Five-minute demo

1. **45 seconds:** overview, actual six KPI cards and descriptive filters. Explain synthetic data.
2. **60 seconds:** January landing ranking, expected gap to budget and forecast flag alongside December's actual flag. Search and click a country. Explain the difference in months and the carried-forward FX assumption.
3. **45 seconds:** country bridge, then Segments: membership, revenue value, driver profile and one action. Six-country segmentation is exploratory.
4. **90 seconds:** Model page: baseline comparison, held-out dates, largest errors and main coefficient associations. Explain past-only features and the one-time final evaluation.
5. **40 seconds:** elbow/silhouette evidence and model limitations; open/download the model note and dataset.

Checks: `node check-dashboard.cjs` validates original Phase 1 behaviour; `node check-phase2.cjs` validates all seven pages, forecast boundaries, scope and output reconciliations.
