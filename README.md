# Performance & Variance Copilot

ECON 449 · Use case 27 · Interactive financial performance dashboard.

## Open the dashboard

Open [index.html](index.html) in a modern browser. The dashboard works without installation or an internet connection. When GitHub Pages is enabled for this repository, it can also be opened using the Pages link shown under the repository's **Settings → Pages**.

Use the navigation to explore the executive overview, revenue variance bridge, country comparison, country drill-down and methodology. Filters persist across views. Select a country in the ranking or table to drill down.

## Assignment deliverables

- [Dashboard](index.html)
- [Dummy monthly P&L dataset](dummy-pnl.csv)
- [Assignment note and calculation methodology](assignment-note.md)

The dataset is synthetic and does not represent Arçelik's actual results. Phase 1's descriptive analysis is retained. Phase 2 adds Ridge revenue forecasts, K-means country segments, and held-out evaluation against two simple baselines.

## Phase 2 submission

- [One-page model note (PDF)](model-note.pdf)
- [Reproduction instructions and five-minute demo](PHASE2.md)
- [Python training script](train_models.py) and [dependencies](requirements.txt)
- [Extended P&L dataset](model-output/updated-pnl.csv)
- [January 2026 country forecasts](model-output/country-predictions.csv)
- [Country segments](model-output/country-segments.csv)
- [Final held-out predictions](model-output/test-predictions.csv)

The original `dummy-pnl.csv` and assignment note document Phase 1. The extended P&L covers 2020–2025 and preserves all original 2023–2025 figures. Keep `model-data.js` and `phase2.js` beside `index.html` when opening it offline. Forecasts apply to January 2026 country totals; descriptive filters retain their original role.

## Share with GitHub Pages

In the repository's **Settings → Pages**, choose **Deploy from a branch**, select the default branch and the `/ (root)` folder, and save. GitHub will display the published dashboard URL when deployment completes.
