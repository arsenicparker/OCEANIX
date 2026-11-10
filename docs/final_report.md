# OCEANIX Project Report — Work in Progress

## Current milestone

OCEANIX is being reset to a data-first build sequence. The first deliverable is a simple mobile-friendly web playground for official INCOIS PFZ advisory data. It demonstrates dataset provenance, coordinate parsing, filtering, and mapping. The larger UI and AIML model are later milestones.

## Verified data collected

On 9 Nov 2026, the official INCOIS spreadsheet export was collected for all 14 sectors. The prepared table has 522 advisory points, DMS-derived coordinates, and source-reported validity through 10 Nov 2026. Per-file sizes and SHA-256 checksums are in the dated manifest. An official WFS line layer was also saved, but its embedded date is 8 Nov and it remains separate from the current point layer.

Existing NOAA/NCEI WIO catch and environment files were checksum-checked. They remain as a separate historical reference and are not used by the current data playground.

## Current app behavior

- FastAPI serves the prepared INCOIS summary and GeoJSON.
- The web page filters advisory points by sector and landing centre, with a linked map and data table.
- OpenStreetMap tiles are used without a map API key and with attribution.
- The app does not accept user-entered ocean measurements or claim model predictions.

## AIML status

No INCOIS model has been trained. The current advisory snapshot is too small in time and lacks matched environmental features and comparison samples. Historical INCOIS advisory and environmental data must be obtained and audited before defining a supervised target. The old WIO report values remain historical notes; a local legacy WIO artifact exists but is ignored by git and is not connected to the app. That experiment is not applicable to Karnataka.

## Remaining work

1. Run automated checks and inspect the data playground at desktop and phone widths.
2. Verify the INCOIS historical archive and environmental-data access, then record a GO/NO-GO decision.
3. Only after the user reviews the simple prototype and the data gate passes, design and implement the screenshot-inspired main UI.

This document is not a final project report. Do not describe API, ML, deployment, or full UI milestones as complete until they have been reproduced and reviewed.
