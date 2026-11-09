/**
 * OCEANIX Marine Intelligence Prototype - Client Application
 * Connects UI inputs to FastAPI backend and manages interactive Leaflet map layers.
 */

document.addEventListener("DOMContentLoaded", () => {
    // API Base URL (defaults to same origin in production, or localhost:8000 in dev)
    const API_BASE = window.location.origin.includes("8000") || window.location.origin.includes("localhost")
        ? ""
        : "http://localhost:8000";

    // DOM Elements
    const apiStatusBadge = document.getElementById("apiStatusBadge");
    const apiStatusText = document.getElementById("apiStatusText");
    const predictionForm = document.getElementById("predictionForm");
    const presetSelect = document.getElementById("presetSelect");
    const resetFormBtn = document.getElementById("resetFormBtn");
    const predictSubmitBtn = document.getElementById("predictSubmitBtn");

    const resultCard = document.getElementById("resultCard");
    const suitabilityBadge = document.getElementById("suitabilityBadge");
    const predictedCatchValue = document.getElementById("predictedCatchValue");
    const resultCoordinates = document.getElementById("resultCoordinates");
    const resultModelVersion = document.getElementById("resultModelVersion");
    const resultDisclaimer = document.getElementById("resultDisclaimer");

    const errorAlert = document.getElementById("errorAlert");
    const errorMessage = document.getElementById("errorMessage");

    const viewWioBtn = document.getElementById("viewWioBtn");
    const viewKarnatakaBtn = document.getElementById("viewKarnatakaBtn");
    const toggleAdvisoriesBtn = document.getElementById("toggleAdvisoriesBtn");

    const aboutModal = document.getElementById("aboutModal");
    const openAboutModalBtn = document.getElementById("openAboutModalBtn");
    const closeAboutModalBtn = document.getElementById("closeAboutModalBtn");
    const modalDismissBtn = document.getElementById("modalDismissBtn");

    // Map & Layers State
    let map = null;
    let advisoryLayerGroup = null;
    let predictionMarker = null;
    let wioBoundaryRectangle = null;
    let advisoriesVisible = true;

    // 1. Initialize Leaflet Map
    function initMap() {
        // Initial center on Western Indian Ocean
        map = L.map("leafletMap", {
            zoomControl: true,
            attributionControl: true,
        }).setView([2.0, 58.0], 5);

        // Add CartoDB Dark Matter base tiles with OpenStreetMap attribution
        L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions" target="_blank">CARTO</a>',
            subdomains: "abcd",
            maxZoom: 18,
        }).addTo(map);

        advisoryLayerGroup = L.layerGroup().addTo(map);

        // Add Western Indian Ocean Domain Bounding Box [38.0°E - 80.0°E, -15.0°S - 15.0°N]
        const wioBounds = [
            [-15.0, 38.0],
            [15.0, 80.0],
        ];
        wioBoundaryRectangle = L.rectangle(wioBounds, {
            color: "#818cf8",
            weight: 1.5,
            dashArray: "6, 6",
            fillColor: "#818cf8",
            fillOpacity: 0.04,
            interactive: false,
        }).addTo(map);

        // Fetch and load INCOIS Karnataka advisory points
        loadKarnatakaAdvisories();
    }

    // 2. Fetch and Render INCOIS Karnataka Advisories
    async function loadKarnatakaAdvisories() {
        try {
            const res = await fetch(`${API_BASE}/advisories/karnataka`);
            if (!res.ok) throw new Error("Could not retrieve Karnataka advisories.");
            const geojson = await res.json();

            L.geoJSON(geojson, {
                pointToLayer: (feature, latlng) => {
                    return L.circleMarker(latlng, {
                        radius: 6,
                        fillColor: "#06b6d4",
                        color: "#ffffff",
                        weight: 2,
                        opacity: 1,
                        fillOpacity: 0.9,
                    });
                },
                onEachFeature: (feature, layer) => {
                    const p = feature.properties;
                    const popupHtml = `
                        <div style="font-family: var(--font-sans); color: #0f172a; min-width: 220px;">
                            <div style="font-weight: 700; color: #0284c7; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; margin-bottom: 6px;">
                                🔷 INCOIS Advisory Point
                            </div>
                            <div style="font-size: 0.8rem; line-height: 1.4;">
                                <strong>Coast:</strong> ${p.landing_centre}<br>
                                <strong>Bearing:</strong> ${p.bearing_deg}° (${p.direction})<br>
                                <strong>Distance:</strong> ${p.distance_km} km<br>
                                <strong>Depth:</strong> ${p.depth_m} m<br>
                                <strong>Validity:</strong> ${p.forecast_valid_from} to ${p.forecast_valid_to}<br>
                                <span style="font-size: 0.7rem; color: #64748b; display: block; margin-top: 4px;">Source: Official INCOIS Operational Advisory (Karnataka)</span>
                            </div>
                        </div>
                    `;
                    layer.bindPopup(popupHtml);
                },
            }).addTo(advisoryLayerGroup);
        } catch (err) {
            console.warn("Notice: Could not load advisory points from server.", err);
        }
    }

    // 3. Health Check
    async function checkApiHealth() {
        try {
            const res = await fetch(`${API_BASE}/health`);
            if (res.ok) {
                const data = await res.json();
                apiStatusBadge.className = "status-indicator online";
                apiStatusText.textContent = data.model_loaded
                    ? `API Online (Model v${data.model_version})`
                    : "API Online (Model Not Loaded)";
            } else {
                throw new Error("API returned non-200");
            }
        } catch (err) {
            apiStatusBadge.className = "status-indicator offline";
            apiStatusText.textContent = "API Offline / Reconnecting...";
        }
    }

    // 4. Handle Preset Selection
    presetSelect.addEventListener("change", (e) => {
        const val = e.target.value;
        if (!val) return;
        const [lon, lat, month] = val.split(",");
        document.getElementById("longitudeInput").value = lon;
        document.getElementById("latitudeInput").value = lat;
        document.getElementById("monthInput").value = month;
    });

    // 5. Reset Form
    resetFormBtn.addEventListener("click", () => {
        presetSelect.value = "";
        document.getElementById("longitudeInput").value = "52.25";
        document.getElementById("latitudeInput").value = "-2.25";
        document.getElementById("monthInput").value = "7";
        document.getElementById("sstInput").value = "";
        document.getElementById("salinityInput").value = "";
        document.getElementById("chlInput").value = "";
        document.getElementById("mldInput").value = "";
        document.getElementById("oxygenInput").value = "";
        document.getElementById("sshInput").value = "";
        resultCard.style.display = "none";
        hideError();
    });

    // 6. Handle Prediction Form Submission
    predictionForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        hideError();

        const lon = parseFloat(document.getElementById("longitudeInput").value);
        const lat = parseFloat(document.getElementById("latitudeInput").value);
        const month = parseInt(document.getElementById("monthInput").value, 10);

        const payload = {
            longitude: lon,
            latitude: lat,
            month: month,
        };

        // Add optional features if specified
        const sst = document.getElementById("sstInput").value;
        if (sst) payload.thetao = parseFloat(sst);
        const salinity = document.getElementById("salinityInput").value;
        if (salinity) payload.so = parseFloat(salinity);
        const chl = document.getElementById("chlInput").value;
        if (chl) payload.chl = parseFloat(chl);
        const mld = document.getElementById("mldInput").value;
        if (mld) payload.mlotst = parseFloat(mld);
        const o2 = document.getElementById("oxygenInput").value;
        if (o2) payload.o2 = parseFloat(o2);
        const zos = document.getElementById("sshInput").value;
        if (zos) payload.zos = parseFloat(zos);

        // UI Loading State
        predictSubmitBtn.classList.add("loading");
        predictSubmitBtn.disabled = true;

        try {
            const res = await fetch(`${API_BASE}/predict`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                const msg = errData.detail || `Server error (${res.status})`;
                throw new Error(msg);
            }

            const data = await res.json();
            displayPredictionResult(data);
            plotPredictionOnMap(data, lat, lon);
        } catch (err) {
            showError(err.message || "Failed to calculate prediction.");
            resultCard.style.display = "none";
        } finally {
            predictSubmitBtn.classList.remove("loading");
            predictSubmitBtn.disabled = false;
        }
    });

    // 7. Render Prediction Result Card
    function displayPredictionResult(data) {
        predictedCatchValue.textContent = data.predicted_catch_biomass_mt.toFixed(1);
        suitabilityBadge.textContent = data.suitability_tier;

        if (data.suitability_tier === "High Suitability") {
            suitabilityBadge.className = "badge badge-high";
        } else if (data.suitability_tier === "Moderate Suitability") {
            suitabilityBadge.className = "badge badge-mod";
        } else {
            suitabilityBadge.className = "badge badge-low";
        }

        resultCoordinates.textContent = `${data.input_coordinates.latitude}°N/S, ${data.input_coordinates.longitude}°E (Month: ${data.input_coordinates.month})`;
        resultModelVersion.textContent = `Model v${data.model_version}`;
        resultDisclaimer.textContent = data.disclaimer;

        resultCard.style.display = "block";
    }

    // 8. Plot Prediction Marker on Map
    function plotPredictionOnMap(data, lat, lon) {
        if (predictionMarker) {
            map.removeLayer(predictionMarker);
        }

        const tierColor = data.suitability_tier === "High Suitability"
            ? "#10b981"
            : data.suitability_tier === "Moderate Suitability"
            ? "#f59e0b"
            : "#3b82f6";

        predictionMarker = L.circleMarker([lat, lon], {
            radius: 10,
            fillColor: tierColor,
            color: "#ffffff",
            weight: 3,
            opacity: 1,
            fillOpacity: 0.95,
        }).addTo(map);

        const popupHtml = `
            <div style="font-family: var(--font-sans); color: #0f172a; min-width: 220px;">
                <div style="font-weight: 700; color: ${tierColor}; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; margin-bottom: 6px;">
                    🎯 OCEANIX Model Prediction
                </div>
                <div style="font-size: 0.8rem; line-height: 1.4;">
                    <strong>Estimated Biomass:</strong> ${data.predicted_catch_biomass_mt} MT<br>
                    <strong>Classification:</strong> ${data.suitability_tier}<br>
                    <strong>Coordinates:</strong> ${lat}°N/S, ${lon}°E<br>
                    <span style="font-size: 0.7rem; color: #dc2626; display: block; margin-top: 6px; font-weight: 600;">
                        Notice: Research estimate. Not a guaranteed catch or navigational route.
                    </span>
                </div>
            </div>
        `;

        predictionMarker.bindPopup(popupHtml).openPopup();
        map.flyTo([lat, lon], 6, { duration: 1.2 });
    }

    // 9. Map Navigation Toolbar Controls
    viewWioBtn.addEventListener("click", () => {
        map.flyTo([2.0, 58.0], 5, { duration: 1 });
    });

    viewKarnatakaBtn.addEventListener("click", () => {
        map.flyTo([13.8, 74.0], 8, { duration: 1.2 });
    });

    toggleAdvisoriesBtn.addEventListener("click", () => {
        if (advisoriesVisible) {
            map.removeLayer(advisoryLayerGroup);
            toggleAdvisoriesBtn.textContent = "Show INCOIS Points";
            advisoriesVisible = false;
        } else {
            map.addLayer(advisoryLayerGroup);
            toggleAdvisoriesBtn.textContent = "Toggle INCOIS Points (24)";
            advisoriesVisible = true;
        }
    });

    // 10. Modal Event Listeners
    openAboutModalBtn.addEventListener("click", () => {
        aboutModal.style.display = "flex";
    });

    closeAboutModalBtn.addEventListener("click", () => {
        aboutModal.style.display = "none";
    });

    modalDismissBtn.addEventListener("click", () => {
        aboutModal.style.display = "none";
    });

    aboutModal.addEventListener("click", (e) => {
        if (e.target === aboutModal) {
            aboutModal.style.display = "none";
        }
    });

    // Helper Functions
    function showError(msg) {
        errorMessage.textContent = msg;
        errorAlert.style.display = "flex";
    }

    function hideError() {
        errorAlert.style.display = "none";
    }

    // Startup
    initMap();
    checkApiHealth();
    setInterval(checkApiHealth, 15000);
});

