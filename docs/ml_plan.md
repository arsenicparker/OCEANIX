# OCEANIX AIML Plan

*Updated 9 November 2026. Model development is intentionally gated on data evidence.*

## Current stage: no INCOIS model is trained

The web playground reads official INCOIS PFZ advisory points and supports map/table exploration. It does not accept user-supplied ocean measurements and does not return a model prediction. The single 9 Nov 2026 snapshot has no historical sequence, no matched environmental features, and no defensible negative/comparison labels; it cannot train or evaluate a supervised model.

## Preferred INCOIS learning task (conditional)

If a historical INCOIS archive and matching environmental data can be obtained, first consider estimating the historical INCOIS advisory pattern for a defined sector, location grid, and time window. The target must be described as an **INCOIS advisory label/pattern**, not actual fish presence or expected catch.

Before choosing the target or algorithm, establish:

1. Which historical advisory records can be retrieved in machine-readable form, for which sectors and dates, and under what use terms.
2. Which environmental variables have suitable temporal and spatial coverage for those same records.
3. How PFZ point/line advisories map to grid cells or candidate locations, with resolution and tolerances documented.
4. How comparison examples are sampled. A location not included in a PFZ advisory is an unlisted advisory cell, not verified fish absence.
5. Whether there are enough independent dates, sectors, and labels for leakage-safe evaluation.

If any item fails, do not train an ML model merely to fill the UI. Narrow the claim or pause the model stage.

## Future modeling protocol (only after an audit GO)

- Freeze a time-based holdout; group repeated dates/locations as appropriate.
- Build a simple baseline first, then one justified tabular model.
- Fit imputation and feature processing only on training data.
- Report target counts and coverage by split, class-aware metrics where applicable, and performance by time/sector where sample sizes allow.
- Keep source records and transformation logs reproducible.
- Show probabilities only if calibration is evaluated; otherwise show the model’s target output without a confidence percentage.
- Evaluate the exact intended map/display use case. Do not extrapolate from an WIO tuna model to Karnataka coastal fisheries.

## WIO model is a separate historical experiment

The repository contains a prior WIO skipjack regression plan based on NOAA/NCEI 0306675, with 2005–2015 training and 2016–2019 holdout. It is preserved as a separate historical route. It is not a substitute for Karnataka INCOIS advisories and is not wired into the current app. Any future use requires an explicit scope decision and an available serialized model artifact.
