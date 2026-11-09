# OCEANIX Scientific & Operational Limitations

*Document Version 1.0 — Milestone M3 & M4 (Evaluation & Limitations)*  
*Prepared strictly according to Project Blueprint Section 5, 11, and 18.*

---

## 1. Executive Statement of Limitations
OCEANIX is an educational decision-support engineering prototype. It is **not** an operational fishing forecast, official marine navigation system, or safety advisory. All predictions and visualizations must be interpreted strictly within their validated scientific boundaries.

---

## 2. Specific Technical Limitations

### 2.1 Marine Dynamic Complexity & Inter-Annual Variability
- **Historical Nature**: The model is trained on historical Western Indian Ocean skipjack tuna catch data (2005–2019) from the Indian Ocean Tuna Commission (IOTC) and Copernicus Marine Service oceanographic reanalysis.
- **Ocean Dynamics**: Marine ecosystems exhibit strong non-linear responses to global climatic phenomena such as the Indian Ocean Dipole (IOD) and El Niño-Southern Oscillation (ENSO). An environmental relationship observed in historical data may not hold under novel climate anomalies or seasonal shifts.

### 2.2 Prediction Target Semantics: Not a Catch Guarantee
- **Biomass Estimate vs. Fish Presence**: A higher estimated catch biomass indicates that oceanographic conditions (SST, salinity, currents, chlorophyll-a) resemble historical locations where commercial skipjack tuna aggregations occurred. It does **not** guarantee fish presence, school density, or harvest success on any specific day.
- **No Direct Abundance Measurement**: Fisheries logbooks record landed catch under specific commercial fishing effort (purse-seine and longline), not absolute ecological stock abundance. Low or zero catch in a grid cell may reflect lack of fishing effort rather than fish absence.

### 2.3 Geographic Scope & Non-Extrapolation
- **Western Indian Ocean Scope**: The machine learning model is calibrated solely for the Western Indian Ocean domain [38.75°E–79.75°E, -14.75°S–14.75°N].
- **No Coastal Karnataka Extrapolation**: The model cannot be used to predict nearshore coastal or artisanal fisheries off Karnataka or other Indian states. Coastal Karnataka advisories are provided purely as an operational parsing demonstration of official INCOIS advisory bulletins and must not be confused with machine learning predictions.

### 2.4 Measurement Uncertainty & Cloud Cover
- Satellite-derived ocean colour (chlorophyll-a) and thermal products are subject to sensor gaps and cloud-cover masking during monsoon seasons. Reanalysis models interpolate these missing fields, introducing model-based uncertainty.

---

## 3. Ethical Guardrails & Responsible Use
1. **Safety at Sea**: OCEANIX does **not** evaluate sea-state hazards, wave height, swell, wind speed, or storm warnings. Fishers must always consult official IMD/INCOIS ocean state forecasts and port advisories before putting to sea.
2. **Attribution & Transparency**: Every map layer and API response explicitly differentiates between observed government advisories (INCOIS) and machine-learned estimates (OCEANIX model), displaying model version, date context, and uncertainty caveats.
