# OCEANIX Limitations and Responsible Use

## Current prototype

- The current web app displays a saved INCOIS PFZ advisory snapshot retrieved 9 Nov 2026, with reported validity through 10 Nov 2026. It does not automatically refresh. Treat it as expired after the stated validity unless a new source export has been collected and checked.
- The point records are official INCOIS advisory locations, not OCEANIX predictions, direct fish counts, or verified catch observations.
- The INCOIS point snapshot contains no environmental covariate matrix and is not sufficient for supervised ML.
- The saved WFS line export embeds 8 Nov 2026 as its source date and is kept separate from the 9 Nov advisory points.
- The app uses online OpenStreetMap tiles. It requires no CARTO key, but the basemap will not load without internet access. Attribution is shown in the map.

## Future AIML work

- Historical PFZ advisory inclusion would be a proxy target for INCOIS advisory behavior, not fish absence/presence or catch volume.
- Satellite-derived SST/chlorophyll can have cloud gaps, changing product definitions, and different spatial/time resolutions. Every join needs validation and a documented tolerance.
- The current active INCOIS ERDDAP entries inspected for this revision do not expose the recent SST/chlorophyll coverage listed in broader holdings summaries; source access must be solved before claiming a live feature feed.
- The WIO dataset is for historical skipjack catch/environment in the Western Indian Ocean. Its geography and species do not validate a Karnataka coastal model.
- The prior WIO result note shows negative R² values. A local serialized artifact exists, but it is ignored by git and is not connected to this app; do not use it as a ready prediction service.

## Safety and interpretation

- OCEANIX is not an official marine advisory, catch guarantee, navigation system, or sea-safety service.
- An advisory or model estimate does not establish that fish are present, absent, catchable, or safe to reach.
- Users must consult current official INCOIS and other relevant safety advisories before making decisions at sea.
- Every layer must show its source and date and distinguish official advisories, environmental observations, and any future model output.
