# OCEANIX Model Results

## Current status

There is **no active INCOIS model result**. The current app is an official-advisory data playground only. INCOIS supervised training remains gated on obtaining historical PFZ labels and matched environmental features. No model probability, suitability tier, or catch estimate should be shown by the app at this stage.

## Legacy WIO experiment (reference only)

The earlier project notes report a WIO skipjack Random Forest result on a chronological 2016–2019 holdout:

| Metric | Dummy median baseline | Random Forest + log1p |
|---|---:|---:|
| MAE | 37.33 MT | 35.81 MT |
| RMSE | 69.00 MT | 65.83 MT |
| R² | -0.1811 | -0.0750 |

These numbers are retained from the prior experiment documentation. A local legacy artifact exists at `models/pipeline.joblib`, but it is ignored by git and is not loaded or exposed by the current app. The artifact was not retrained or revalidated during this app revision. The lower MAE/RMSE are modest improvements over the training-median baseline. Both negative R² values mean the model still explains little holdout variance and performs below a test-mean reference on that metric. Do not call this a validated operational predictor or apply it to Karnataka.

The feature-importance values in the previous report are likewise historical notes, not evidence of causal oceanographic effects. Re-run the complete experiment from source before reusing any result in a presentation.

## Next results report

Replace this section only after an audited INCOIS dataset supports a defensible target. Include provenance, exact split, sample counts, baseline, metrics, error analysis, and target limitations. Keep official INCOIS advisory data separate from OCEANIX model output.
