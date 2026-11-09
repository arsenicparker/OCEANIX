/**
 * OCEANIX Marine Intelligence Prototype - Client Application
 * Connects UI inputs to FastAPI backend and manages interactive Leaflet map layers.
 */

document.addEventListener('DOMContentLoaded', () => {
    const API_BASE = window.location.origin.includes('8000') || window.location.origin.includes('localhost')
        ? ''
        : 'http://localhost:8000';

    // DOM elements
    const apiStatusBadge = document.getElementById('apiStatusBadge');
    const apiStatusText = document.getElementById('apiStatusText');
    const predictionForm = document.getElementById('predictionForm');
    const presetSelect = document.getElementById('presetSelect');
    const resetFormBtn = document.getElementById('resetFormBtn');
    const predictSubmitBtn = document.getElementById('predictSubmitBtn');

    const resultCard = document.getElementById('resultCard');
    const suitabilityBadge = document.getElementById('suitabilityBadge');
    const predictedCatchValue = document.getElementById('predictedCatchValue');
    const resultCoordinates = document.getElementById('resultCoordinates');
    const resultModelVersion = document.getElementById('resultModelVersion');
    const resultDisclaimer = document.getElementById('resultDisclaimer');

    const errorAlert = document.getElementById('errorAlert');
    const errorMessage = document.getElementById('errorMessage');

    const viewWioBtn = document.getElementById('viewWioBtn');
    const viewKarnatakaBtn = document.getElementById('viewKarnatakaBtn');
    const toggleAdvisoriesBtn = document.getElementById('toggleAdvisoriesBtn');

    const aboutModal = document.getElementById('aboutModal');
    const openAboutModalBtn = document.getElementById('openAboutModalBtn');
    const closeAboutModalBtn = document.getElementById('closeAboutModalBtn');
    const modalDismissBtn = document.getElementById('modalDismissBtn');

    // Map & layers state
    let map = null;
    let advisoryLayerGroup = null;
    let predictionMarker = null;
    let wioBoundaryRectangle = null;
    let advisoriesVisible = true;

    // 1. Initialize Leaflet map
    function initMap() {
        map = L.map('leafletMap', {
            zoomControl: true,
            attributionControl: true,
        }).setView([2.0, 58.0], 5);

        // CartoDB Dark Matter tiles (no API key needed)
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions" target="_blank">CARTO</a>',
            subdomains: 'abcd',
            maxZoom: 18,
        }).addTo(map);

        advisoryLayerGroup = L.layerGroup().addTo(map);

        // Western Indian Ocean bounding box
        const wioBounds = [
            [-15.0, 38.0],
            [15.0, 80.0],
        ];
        wioBoundaryRectangle = L.rectangle(wioBounds, {
            color: '#818cf8',
            weight: 1.5,
            dashArray: '6, 6',
            fillColor: '#818cf8',
            fillOpacity: 0.04,
            interactive: false,
        }).addTo(map);

        // Load advisories
        loadKarnatakaAdvisories();
    }

    // 2. Load INCOIS Karnataka advisory points
    async function loadKarnatakaAdvisories() {
        try {
            const res = await fetch(`${API_BASE}/advisories/karnataka`);
            if (!res.ok) throw new Error('Could not retrieve Karnataka advisories.');
            const geojson = await res.json();

            L.geoJSON(geojson, {
                pointToLayer: (feature, latlng) => L.circleMarker(latlng, {
                    radius: 6,
                    fillColor: '#06b6d4',
                    color: '#ffffff',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.9,
                }),
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
                        </div>`;
                    layer.bindPopup(popupHtml);
                },
            }).addTo(advisoryLayerGroup);
        } catch (err) {
            console.warn('Notice: Could not load advisory points from server.', err);
        }
    }

    // 3. Health check
    async function checkApiHealth() {
        try {
            const res = await fetch(`${API_BASE}/health`);
            if (res.ok) {
                const data = await res.json();
                apiStatusBadge.className = 'status-indicator online';
                apiStatusText.textContent = data.model_loaded
                    ? `API Online (Model v${data.model_version})`
                    : 'API Online (Model Not Loaded)';
            } else {
                throw new Error('API returned non‑200');
            }
        } catch (err) {
            apiStatusBadge.className = 'status-indicator offline';
            apiStatusText.textContent = 'API Offline / Reconnecting...';
        }
    }

    // 4. Preset selection
    presetSelect.addEventListener('change', e => {
        const val = e.target.value;
        if (!val) return;
        const [lon, lat, month] = val.split(',');
        document.getElementById('longitudeInput').value = lon;
        document.getElementById('latitudeInput').value = lat;
        document.getElementById('monthInput').value = month;
    });

    // 5. Reset form
    resetFormBtn.addEventListener('click', () => {
        presetSelect.value = '';
        document.getElementById('longitudeInput').value = '52.25';
        document.getElementById('latitudeInput').value = '-2.25';
        document.getElementById('monthInput').value = '7';
        document.getElementById('sstInput').value = '';
        document.getElementById('salinityInput').value = '';
        document.getElementById('chlInput').value = '';
        document.getElementById('mldInput').value = '';
        document.getElementById('oxygenInput').value = '';
        document.getElementById('sshInput').value = '';
        resultCard.style.display = 'none';
        hideError();
    });

    // 6. Submit prediction
    predictionForm.addEventListener('submit', async e => {
        e.preventDefault();
        hideError();

        const lon = parseFloat(document.getElementById('longitudeInput').value);
        const lat = parseFloat(document.getElementById('latitudeInput').value);
        const month = parseInt(document.getElementById('monthInput').value, 10);

        const payload = { longitude: lon, latitude: lat, month: month };
        const sst = document.getElementById('sstInput').value;
        if (sst) payload.thetao = parseFloat(sst);
        const salinity = document.getElementById('salinityInput').value;
        if (salinity) payload.so = parseFloat(salinity);
        const chl = document.getElementById('chlInput').value;
        if (chl) payload.chl = parseFloat(chl);
        const mld = document.getElementById('mldInput').value;
        if (mld) payload.mlotst = parseFloat(mld);
        const o2 = document.getElementById('oxygenInput').value;
        if (o2) payload.o2 = parseFloat(o2);
        const zos = document.getElementById('sshInput').value;
        if (zos) payload.zos = parseFloat(zos);

        predictSubmitBtn.classList.add('loading');
        predictSubmitBtn.disabled = true;

        try {
            const res = await fetch(`${API_BASE}/predict`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            if (!res.ok) throw new Error('Prediction request failed');
            const data = await res.json();

            suitabilityBadge.textContent = data.suitability_tier;
            predictedCatchValue.textContent = data.predicted_catch_mt.toFixed(2);
            resultCoordinates.textContent = `${lat.toFixed(2)}°, ${lon.toFixed(2)}°`;
            resultModelVersion.textContent = data.model_version;
            resultCard.style.display = 'block';
        } catch (err) {
            showError('Failed to get prediction. Please try again.');
        } finally {
            predictSubmitBtn.classList.remove('loading');
            predictSubmitBtn.disabled = false;
        }
    });

    // 7. Error handling helpers
    function showError(msg) {
        errorMessage.textContent = msg;
        errorAlert.style.display = 'block';
    }
    function hideError() {
        errorAlert.style.display = 'none';
    }

    // 8. About modal
    openAboutModalBtn.addEventListener('click', () => aboutModal.showModal());
    closeAboutModalBtn.addEventListener('click', () => aboutModal.close());
    modalDismissBtn.addEventListener('click', () => aboutModal.close());

    // 9. Periodic health check
    setInterval(checkApiHealth, 15000);
    checkApiHealth();
    initMap();
});
