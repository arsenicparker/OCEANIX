# OCEANIX Project Scope

*Updated 9 November 2026 to match the requested staged build.*

## Product idea

OCEANIX is an AIML project whose first deliverable is a simple, mobile-friendly web data playground. It lets a user explore official INCOIS Potential Fishing Zone advisories by sector and landing centre, inspect their coordinates and source validity, and view the points on a map. The first deliverable proves the data-to-app path before the larger screenshot-inspired UI is built.

The data playground shows source advisory records. It does not generate a catch or fishing-zone prediction, and it does not ask the user to enter ocean measurements.

## Current data route

### INCOIS PFZ advisory data

- Primary source: official INCOIS PFZ text and spreadsheet exports.
- Current local snapshot: 9 Nov 2026, for 14 sectors and 522 advisory points, with source validity through 10 Nov 2026.
- Coordinates are parsed from source DMS values and served as decimal-degree GeoJSON points.
- The map displays the advisory locations as official INCOIS data, clearly distinguished from any future OCEANIX model layer.
- The app reports a dated snapshot. It does not imply continuous live refresh.

### AIML target gate

The current INCOIS snapshot contains one advisory time, only advisory points, and no matched environmental input matrix. It is not a supervised-learning dataset. An INCOIS model requires a historical advisory archive plus matched environmental data and a defensible comparison-sample design. Any model trained on advisory history would estimate historical advisory patterns, not fish absence or guaranteed catch.

INCOIS’s holdings page indicates ongoing PFZ and satellite ocean products. However, the current-data inspection found no usable current SST/chlorophyll table in the active ERDDAP entries. Accessible ERDDAP products inspected had earlier end dates. Source access and matching feasibility remain an explicit go/no-go task.

### WIO reference route

The existing NOAA/NCEI 0306675 dataset (2005–2019 Western Indian Ocean skipjack catch/environment) remains in the repository with its raw files, prepared table, and historical model documentation. It is not shown as a Karnataka predictor and is not used by the data playground. Its use as a fallback would require a deliberate rescope because its geography and target differ from the INCOIS coastal use case.

## Prototype functionality

- Show a clear source date, source validity, point count, and sector count.
- Filter the same official advisory records in both table and map.
- Search by landing centre and zoom the selected advisory point.
- Use a keyless OpenStreetMap base layer with required attribution.
- Link to the official INCOIS PFZ service and official WebGIS.
- Show honest errors when local data or map tiles cannot load.
- Keep the historical WebGIS line snapshot out of the current point overlay because its embedded date differs by one day.

## Later main UI

After the data playground is verified, build the broader mobile-first UI inspired by the user’s screenshot: onboarding, home/dashboard, find-zone flow, results, map, ocean conditions, insights, history, About, and Settings. Each element must use real data or be clearly described as a local UI state. Prediction cards and probability/confidence indicators remain out of scope until a valid model and calibration exist.

The first target is a mobile-friendly web app. APK packaging can be evaluated after the web flow and API are stable.

## Responsible-use boundaries

- Official INCOIS advisory points are not OCEANIX predictions.
- An unlisted advisory point does not mean fish are absent.
- No screen guarantees catch, evaluates vessel safety, or gives navigation instructions.
- Show source timestamp and forecast validity near the map and data.
- If the snapshot expires or cannot be refreshed, label it historical/expired rather than current.
