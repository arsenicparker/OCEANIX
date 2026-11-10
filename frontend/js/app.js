document.addEventListener('DOMContentLoaded', () => {
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const esc = (value) => String(value ?? '').replace(/[&<>"']/g, (ch) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[ch]);
  const STORAGE = { searches: 'oceanix.searches.v2', saved: 'oceanix.saved.v2', theme: 'oceanix.theme.v1' };
  const state = {
    records: [], summary: null, map: null, heat: null, markers: null, resultMap: null,
    resultHeat: null, resultMarkers: null, currentLocation: null, currentLocationLabel: '',
    selectedFeature: null, filtered: [], lastSearch: null, toastTimer: null, environmentPoint: null,
  };

  function readStorage(key, fallback = []) {
    try {
      const value = localStorage.getItem(key);
      return value === null ? fallback : JSON.parse(value);
    }
    catch { return fallback; }
  }

  function writeStorage(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); return true; }
    catch { showToast('Browser storage is unavailable; this change will not be saved.'); return false; }
  }

  function showToast(message) {
    const toast = $('#toast');
    toast.textContent = message;
    toast.classList.add('show');
    clearTimeout(state.toastTimer);
    state.toastTimer = setTimeout(() => toast.classList.remove('show'), 2800);
  }

  function setRoute(route) {
    const target = $(`[data-view="${route}"]`);
    if (!target) return;
    $$('.view').forEach((view) => view.classList.toggle('active', view === target));
    $$('[data-route]').forEach((button) => button.classList.toggle('active', button.dataset.route === route));
    history.replaceState(null, '', `#${route}`);
    window.scrollTo({ top: 0, behavior: 'smooth' });
    if (route === 'map') {
      window.setTimeout(() => {
        state.map?.invalidateSize(true);
        if (state.map?.getContainer().clientWidth > 1 && state.map?.getContainer().clientHeight > 1) ensureHeatLayer('main');
        applyMapFilters(true);
      }, 80);
    }
    if (route === 'result') window.setTimeout(() => {
      state.resultMap?.invalidateSize(true);
      const features = state.lastSearch?.matches?.map((entry) => entry.feature) || [];
      if (state.resultMap) renderResultMap(features);
    }, 100);
    if (route === 'history') renderHistory();
  }

  function sectorName(feature) { return feature?.properties?.sector_name || 'Unknown sector'; }
  function coords(feature) {
    const [lon, lat] = feature.geometry.coordinates.map(Number);
    return [lat, lon];
  }
  function sectorFeatures(sector = '') {
    const normalized = sector.trim().toLowerCase();
    return state.records.filter((f) => !normalized || sectorName(f).toLowerCase() === normalized);
  }

  function uniqueSorted(values) { return [...new Set(values.filter(Boolean))].sort((a, b) => a.localeCompare(b)); }

  function setDataStatus(message, mode) {
    const status = $('#serviceStatus');
    status.className = `status-pill ${mode || ''}`;
    $('span:last-child', status).textContent = message;
  }

  function formatDate(value) {
    if (!value) return 'Date unavailable';
    const parsed = new Date(`${value}T12:00:00`);
    if (Number.isNaN(parsed.getTime())) return value;
    return new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }).format(parsed);
  }

  function validityLabel(value) {
    const match = String(value || '').match(/(\d{1,2}\s+[A-Z]{3}\s+\d{4})/i);
    if (match) return match[1].replace(/\b\w/g, (x) => x.toUpperCase());
    return value || 'Not recorded';
  }

  function fillSelects() {
    const sectors = uniqueSorted(state.records.map(sectorName));
    ['#findSector', '#mapSector'].forEach((selector) => {
      const select = $(selector);
      const first = select.options[0];
      select.replaceChildren(first);
      sectors.forEach((sector) => {
        const option = document.createElement('option');
        option.value = sector;
        option.textContent = sector;
        select.append(option);
      });
    });
    const centres = uniqueSorted(state.records.map((f) => f.properties?.landing_centre));
    const list = $('#centreOptions');
    centres.forEach((centre) => {
      const option = document.createElement('option');
      option.value = centre;
      list.append(option);
    });
    const conditionsLocation = $('#conditionsLocation');
    if (conditionsLocation) {
      conditionsLocation.replaceChildren(new Option('Choose a coastal advisory point', ''));
      state.records.forEach((feature, index) => {
        const p = feature.properties || {};
        const point = coords(feature);
        const label = `${p.landing_centre || 'Coast'} · ${sectorName(feature)} · ${point[0].toFixed(2)}°N, ${point[1].toFixed(2)}°E`;
        conditionsLocation.add(new Option(label, String(index)));
      });
    }
  }

  const environmentLabels = {
    sst: ['Sea surface temperature', 1], current: ['Surface current speed', 2], mld: ['Mixed layer depth', 1],
    d20: ['D20 depth', 1], wind: ['Wind speed', 1], wave_height: ['Significant wave height', 1], wave_period: ['Wave period', 1],
  };

  function setConditionCard(key, reading) {
    const card = $(`[data-env-metric="${key}"]`);
    if (!card) return;
    const value = $('strong', card);
    const detail = $('small', card);
    card.classList.toggle('disabled-metric', !reading || !Number.isFinite(Number(reading.value)));
    if (!reading || !Number.isFinite(Number(reading.value))) {
      value.textContent = 'Unavailable';
      detail.textContent = 'No verified value for this point';
      return;
    }
    const [, decimals] = environmentLabels[key];
    value.textContent = `${Number(reading.value).toFixed(decimals)} ${reading.unit || ''}`.trim();
    detail.textContent = `${reading.source || 'INCOIS'} · ${formatDate(String(reading.time || '').slice(0, 10))} ${String(reading.time || '').slice(11, 16)} UTC`;
  }

  async function loadConditions() {
    const select = $('#conditionsLocation');
    const index = Number(select.value);
    if (!select.value || !state.records[index]) {
      $('#conditionsStatusTitle').textContent = 'Choose a location';
      $('#conditionsStatusText').textContent = 'Select an official advisory point to load its environmental fields.';
      return;
    }
    const feature = state.records[index];
    const [lat, lon] = coords(feature);
    state.environmentPoint = feature;
    $('#refreshConditions').disabled = true;
    $('#refreshConditions').textContent = 'Loading…';
    $('#conditionsStatusTitle').textContent = 'Loading INCOIS point data';
    $('#conditionsStatusText').textContent = `Requesting environmental fields for ${feature.properties?.landing_centre || sectorName(feature)} (${lat.toFixed(3)}°N, ${lon.toFixed(3)}°E).`;
    $('#conditionsStatus').classList.add('is-loading');
    try {
      const response = await fetch(`/api/environment/current?lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lon)}`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'INCOIS environmental data is unavailable.');
      const readings = data.readings || {};
      Object.keys(environmentLabels).forEach((key) => setConditionCard(key, readings[key]));
      const chl = readings.chlorophyll_a;
      const chlCard = $('[data-env-metric="chlorophyll_a"]');
      if (chl) {
        chlCard.classList.toggle('disabled-metric', !chl.image_url);
        $('strong', chlCard).textContent = chl.value == null ? 'Map only' : `${Number(chl.value).toFixed(2)} ${chl.unit || 'mg/m³'}`;
        $('small', chlCard).textContent = chl.date ? `INCOIS ABIS · ${chl.date}` : 'INCOIS daily satellite product';
        if (chl.image_url) {
          $('#chlorophyllImage').src = chl.image_url;
          if (chl.colorbar_url) $('#chlorophyllColorbar').src = chl.colorbar_url;
          $('#chlorophyllImageLink').href = chl.image_url;
          $('#chlorophyllSource').href = chl.source_url || 'https://incois.gov.in/site/services/hab_products.jsp';
          $('#chlorophyllDate').textContent = chl.date ? `Satellite product · ${chl.date}` : 'Latest published daily product';
          $('#chlorophyllPanel').hidden = false;
        }
      }
      const available = Object.keys(environmentLabels).filter((key) => readings[key]).length;
      $('#conditionsStatus').classList.remove('is-error', 'is-loading');
      $('#conditionsStatusTitle').textContent = available ? `${available} INCOIS forecast fields loaded` : 'INCOIS environmental fields unavailable';
      $('#conditionsStatusText').textContent = data.errors?.length
        ? `${data.note || ''} Some products did not respond: ${data.errors.join('; ')}.`
        : (data.note || 'Values are returned for the selected point and include their own timestamps.');
      $('#environmentMeta').textContent = `Selected advisory point: ${feature.properties?.landing_centre || sectorName(feature)} · ${lat.toFixed(4)}°N, ${lon.toFixed(4)}°E. Retrieved ${new Date(data.retrieved_at).toLocaleString()}. Model forecast values and satellite products are clearly labelled.`;
    } catch (error) {
      $('#conditionsStatus').classList.remove('is-loading');
      $('#conditionsStatus').classList.add('is-error');
      $('#conditionsStatusTitle').textContent = 'Environmental data unavailable';
      $('#conditionsStatusText').textContent = `${error.message} Check the network connection and try again.`;
      showToast('Could not load environmental data');
    } finally {
      $('#refreshConditions').disabled = false;
      $('#refreshConditions').textContent = 'Refresh readings';
    }
  }

  function renderSnapshot() {
    const summary = state.summary || {};
    const date = formatDate(summary.snapshot_date);
    const validity = validityLabel(summary.forecast_validity);
    const updated = summary.source_updated_at || 'Source time unavailable';
    $('#homeSnapshotDate').textContent = date;
    $('#homePointCount').textContent = Number(summary.point_count || state.records.length).toLocaleString();
    $('#homeSectorCount').textContent = Number(summary.sector_count || 0).toLocaleString();
    $('#homeValidity').textContent = validity;
    $('#findSnapshotDate').textContent = date;
    $('#findSnapshotValidity').textContent = `Valid through ${validity}`;
    const dateSelect = $('#snapshotDateSelect');
    dateSelect.replaceChildren();
    if (summary.snapshot_date) {
      dateSelect.add(new Option(date, summary.snapshot_date));
      dateSelect.value = summary.snapshot_date;
    } else {
      dateSelect.add(new Option('No advisory dates available', ''));
      dateSelect.disabled = true;
    }
    $('#insightsDate').textContent = date;
    const banner = `INCOIS snapshot: ${date} · Forecast validity reported through ${validity}. This is saved data, not a live feed.`;
    $('#bannerText').textContent = banner;
    $('#mapSubtitle').textContent = `${state.records.length.toLocaleString()} official advisory points · ${date}`;
    setDataStatus('Snapshot loaded', 'online');
    if (summary.is_live_connection === false) $('#serviceStatus').title = 'Saved local snapshot; not a live data connection.';
    const expire = state.records[0]?.properties?.forecast_valid_to;
    if (expire) {
      const end = new Date(`${expire}T23:59:59`);
      if (!Number.isNaN(end.getTime()) && end < new Date()) $('#dataBanner').classList.add('expired');
    }
  }

  function initMap() {
    const mapMessage = $('#mapMessage');
    if (!window.L) {
      mapMessage.hidden = false;
      mapMessage.textContent = 'Map libraries did not load. The advisory list and search are still available.';
      return;
    }
    try {
      state.map = L.map('leafletMap', { zoomControl: true, preferCanvas: true }).setView([14.5, 75.5], 5);
      const tileLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 18,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      }).addTo(state.map);
      tileLayer.on('tileerror', () => {
        mapMessage.hidden = false;
        mapMessage.textContent = 'Map tiles are unavailable. Check your internet connection; advisory records remain available.';
      });
      tileLayer.on('tileload', () => { mapMessage.hidden = true; });
      state.markers = L.layerGroup().addTo(state.map);
      state.map.whenReady(() => window.setTimeout(() => state.map?.invalidateSize(true), 120));
    } catch (error) {
      console.error('Main map initialization failed:', error);
      mapMessage.hidden = false;
      mapMessage.textContent = 'The map could not start. Search and advisory details remain available.';
    }
    initResultMap();
    if (!window.L.heatLayer) {
      $('#heatToggle').disabled = true;
      mapMessage.hidden = false;
      mapMessage.textContent = 'The heat-layer library did not load. Point markers are still available.';
    }
  }

  function initResultMap() {
    if (!window.L || !$('#resultMapMini')) return;
    try {
      state.resultMap = L.map('resultMapMini', { zoomControl: false, scrollWheelZoom: false, dragging: false, attributionControl: false }).setView([14.5, 75.5], 5);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 18, attribution: '&copy; OpenStreetMap contributors' }).addTo(state.resultMap);
      state.resultMarkers = L.layerGroup().addTo(state.resultMap);
    } catch (error) {
      console.error('Result map initialization failed:', error);
    }
  }

  function ensureHeatLayer(which) {
    if (!window.L?.heatLayer) return null;
    const isResult = which === 'result';
    const map = isResult ? state.resultMap : state.map;
    const key = isResult ? 'resultHeat' : 'heat';
    if (!map) return null;
    if (state[key]) return state[key];
    const element = map.getContainer();
    if (element.clientWidth < 2 || element.clientHeight < 2) return null;
    const options = isResult
      ? { radius: 25, blur: 19, maxZoom: 9, minOpacity: 0.27 }
      : { radius: 28, blur: 21, maxZoom: 9, minOpacity: 0.28 };
    options.gradient = { 0.16: '#18b9ee', 0.48: '#19d5b1', 0.76: '#9bdd48', 1: '#ffe161' };
    try {
      state[key] = L.heatLayer([], options).addTo(map);
      return state[key];
    } catch (error) {
      console.error(`${isResult ? 'Result' : 'Main'} heat layer initialization failed:`, error);
      const message = isResult ? null : $('#mapMessage');
      if (message) {
        message.hidden = false;
        message.textContent = 'The heat layer could not start. Advisory points remain available.';
      }
      return null;
    }
  }

  function currentMapFeatures() {
    const sector = $('#mapSector').value;
    return sectorFeatures(sector);
  }

  function pointMarker(feature, radius = 6) {
    const [lat, lon] = coords(feature);
    const p = feature.properties || {};
    const marker = L.circleMarker([lat, lon], {
      radius, weight: 1.4, color: '#e6fbff', fillColor: '#10b7d2', fillOpacity: 0.96,
    });
    marker.bindPopup(`<div class="popup-title">${esc(p.landing_centre)} · ${esc(sectorName(feature))}</div><div><b>Direction:</b> ${esc(p.direction)}${Number.isFinite(Number(p.bearing_deg)) ? ` (${Number(p.bearing_deg).toFixed(0)}°)` : ''}<br><b>Distance:</b> ${esc(p.distance_min_km)}–${esc(p.distance_max_km)} km<br><b>Depth:</b> ${esc(p.depth_min_m)}–${esc(p.depth_max_m)} m<br><b>Valid:</b> ${esc(p.forecast_valid_from)} to ${esc(p.forecast_valid_to)}</div>`);
    marker.on('click', () => showSelected(feature));
    return marker;
  }

  function showSelected(feature) {
    state.selectedFeature = feature;
    const p = feature.properties || {};
    $('#selectedTitle').textContent = `${p.landing_centre || 'Advisory'} · ${sectorName(feature)}`;
    $('#selectedDetails').innerHTML = `<div class="detail-chips"><span>${esc(p.direction)} · ${esc(p.bearing_deg)}°</span><span>${esc(p.distance_min_km)}–${esc(p.distance_max_km)} km from centre</span><span>${esc(p.depth_min_m)}–${esc(p.depth_max_m)} m depth</span></div><p>Source validity: ${esc(p.forecast_valid_from)} to ${esc(p.forecast_valid_to)}. Official INCOIS advisory location.</p>`;
  }

  function applyMapFilters(fit = false) {
    if (!state.map || !state.markers) return;
    const features = currentMapFeatures();
    state.filtered = features;
    state.markers.clearLayers();
    const heatOn = $('#heatToggle').checked;
    const pointsOn = $('#pointsToggle').checked;
    if (heatOn && !state.heat && state.map.getContainer().clientWidth > 1 && state.map.getContainer().clientHeight > 1) ensureHeatLayer('main');
    if (state.heat) {
      const heatPoints = features.map((feature) => {
        const [lat, lon] = coords(feature);
        return [lat, lon, 0.72];
      });
      state.heat.setLatLngs(heatPoints);
      if (heatOn && !state.map.hasLayer(state.heat)) state.heat.addTo(state.map);
      if (!heatOn && state.map.hasLayer(state.heat)) state.map.removeLayer(state.heat);
    }
    if (pointsOn) features.forEach((feature) => pointMarker(feature).addTo(state.markers));
    const count = $('#mapPointCount');
    if (count) count.textContent = `${features.length.toLocaleString()} points`;
    const mapVisible = state.map.getContainer().clientWidth > 1 && state.map.getContainer().clientHeight > 1;
    if (fit && mapVisible && features.length) {
      const bounds = L.latLngBounds(features.map(coords));
      if (bounds.isValid()) state.map.fitBounds(bounds.pad(0.1), { maxZoom: $('#mapSector').value ? 8 : 6, animate: false });
    }
  }

  function distanceKm(a, b) {
    const radians = (n) => n * Math.PI / 180;
    const dLat = radians(b[0] - a[0]);
    const dLon = radians(b[1] - a[1]);
    const lat1 = radians(a[0]);
    const lat2 = radians(b[0]);
    const h = Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) ** 2;
    return 6371 * 2 * Math.atan2(Math.sqrt(h), Math.sqrt(1 - h));
  }

  function locateDevice() {
    const status = $('#locationStatus');
    if (!navigator.geolocation) {
      status.textContent = 'This browser does not provide device location. Select a sector or centre instead.';
      status.className = 'inline-status error';
      return;
    }
    status.textContent = 'Requesting your device location…';
    status.className = 'inline-status';
    navigator.geolocation.getCurrentPosition((position) => {
      state.currentLocation = [position.coords.latitude, position.coords.longitude];
      state.currentLocationLabel = 'Current device location';
      status.textContent = 'Location ready. Coordinates stay in memory for this search only.';
      status.className = 'inline-status success';
      showToast('Location ready for nearby advisory search');
    }, (error) => {
      const message = error.code === 1 ? 'Location permission was not granted. Select a sector or centre to continue.' : 'Could not determine your location. Try again or choose a sector.';
      status.textContent = message;
      status.className = 'inline-status error';
    }, { enableHighAccuracy: false, timeout: 10000, maximumAge: 60000 });
  }

  function buildSearch() {
    const sector = $('#findSector').value;
    const centreQuery = $('#findCentre').value.trim().toLowerCase();
    const radius = Number($('#searchRadius').value) || 100;
    if (!sector && !centreQuery && !state.currentLocation) {
      $('#locationStatus').textContent = 'Choose a coastal sector, search a landing centre, or use your current location.';
      $('#locationStatus').className = 'inline-status error';
      return;
    }
    let candidates = sectorFeatures(sector).filter((feature) => !centreQuery || String(feature.properties?.landing_centre || '').toLowerCase().includes(centreQuery));
    if (state.currentLocation) {
      candidates = candidates.map((feature) => ({ feature, distance: distanceKm(state.currentLocation, coords(feature)) })).sort((a, b) => a.distance - b.distance);
      const inRange = candidates.filter((entry) => entry.distance <= radius);
      candidates = inRange.length ? inRange : candidates.slice(0, Math.min(5, candidates.length));
    } else {
      candidates = candidates.map((feature) => ({ feature, distance: null }));
    }
    const result = {
      sector, centreQuery, radius, usedLocation: Boolean(state.currentLocation),
      locationLabel: state.currentLocationLabel, matches: candidates,
      label: state.currentLocation ? 'Current device location' : (centreQuery ? $('#findCentre').value.trim() : (sector || 'All sectors')),
      date: $('#snapshotDateSelect').value || state.summary?.snapshot_date || '',
    };
    state.lastSearch = result;
    $('#findResults').hidden = false;
    $('#resultsTitle').textContent = state.currentLocation ? 'Advisories near your location' : `Advisories for ${result.label}`;
    const outsideRange = state.currentLocation && candidates.every((entry) => entry.distance > radius);
    $('#resultsSubhead').textContent = state.currentLocation
      ? (outsideRange ? `No points within ${radius} km; showing the nearest available advisory locations.` : `Within ${radius} km of this device location · distances are approximate.`)
      : `${candidates.length} matching points in the available sector data.`;
    $('#resultsList').innerHTML = candidates.length ? candidates.slice(0, 12).map((entry, index) => renderResultRow(entry, index)).join('') : '<div class="empty-state">No advisory points match this search. Try another sector or a wider area.</div>';
    $('#resultsList').querySelectorAll('[data-result-id]').forEach((button) => button.addEventListener('click', () => {
      const found = state.records.find((f) => f.properties?.advisory_id === button.dataset.resultId);
      if (!found) return;
      $('#mapSector').value = sector || '';
      setRoute('map');
      window.setTimeout(() => {
        if (state.map) {
          const [lat, lon] = coords(found);
          state.map.setView([lat, lon], 8);
          const marker = pointMarker(found, 8).addTo(state.markers);
          marker.openPopup();
          showSelected(found);
        }
      }, 120);
    }));
    renderResultMap(candidates.map((entry) => entry.feature));
    storeRecent(result);
    renderHomeRecent();
    renderResultView();
    setRoute('result');
  }

  function renderResultRow(entry, index) {
    const feature = entry.feature;
    const p = feature.properties || {};
    const distance = entry.distance == null ? `${p.distance_min_km}–${p.distance_max_km} km from ${p.landing_centre}` : `${entry.distance.toFixed(1)} km away`;
    return `<article class="advisory-row"><span class="advisory-number">${String(index + 1).padStart(2, '0')}</span><div class="advisory-row-main"><strong>${esc(p.landing_centre)} · ${esc(sectorName(feature))}</strong><small>${esc(p.direction)} · ${esc(distance)}</small></div><button class="row-arrow" data-result-id="${esc(p.advisory_id)}" aria-label="Show ${esc(p.landing_centre)} on map"><svg><use href="#i-arrow"/></svg></button></article>`;
  }

  function renderResultMap(features) {
    if (!state.resultMap || !state.resultMarkers) return;
    state.resultMarkers.clearLayers();
    const points = features.map((feature) => {
      const [lat, lon] = coords(feature);
      return [lat, lon, 0.72];
    });
    if (!state.resultHeat && state.resultMap.getContainer().clientWidth > 1 && state.resultMap.getContainer().clientHeight > 1) ensureHeatLayer('result');
    if (state.resultHeat) state.resultHeat.setLatLngs(points);
    features.forEach((feature) => pointMarker(feature, 5).addTo(state.resultMarkers));
    const mapVisible = state.resultMap.getContainer().clientWidth > 1 && state.resultMap.getContainer().clientHeight > 1;
    if (mapVisible && features.length) {
      const bounds = L.latLngBounds(features.map(coords));
      if (bounds.isValid()) state.resultMap.fitBounds(bounds.pad(0.14), { maxZoom: 8, animate: false });
    }
    window.setTimeout(() => state.resultMap.invalidateSize(true), 90);
  }

  function renderResultView() {
    const result = state.lastSearch;
    if (!result) return;
    const matches = result.matches || [];
    $('#resultLocationLabel').textContent = `${result.label} · Snapshot ${formatDate(result.date)}`;
    $('#resultCount').textContent = `${matches.length} point${matches.length === 1 ? '' : 's'}`;
    $('#resultSummaryTitle').textContent = matches.length ? `${matches.length} advisory location${matches.length === 1 ? '' : 's'} found` : 'No matching advisory points';
    $('#resultSummaryText').textContent = result.usedLocation
      ? `Official INCOIS points nearest to your current location, using the selected ${result.radius} km search range where data is available.`
      : `Official INCOIS advisory points listed for ${result.label}.`;
  }

  function countBy(keyFn) {
    const counts = new Map();
    state.records.forEach((feature) => {
      const key = keyFn(feature);
      if (key) counts.set(key, (counts.get(key) || 0) + 1);
    });
    return [...counts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  }

  function renderBarChart(containerSelector, entries, limit = 8) {
    const container = $(containerSelector);
    if (!entries.length) { container.innerHTML = '<div class="empty-state">No records available.</div>'; return; }
    const visible = entries.slice(0, limit);
    const max = Math.max(...visible.map((entry) => entry[1]), 1);
    container.innerHTML = visible.map(([label, value]) => `<div class="bar-row"><div class="bar-label"><span>${esc(label)}</span><strong>${value}</strong></div><div class="bar-track"><span style="width:${Math.max(5, value / max * 100)}%"></span></div></div>`).join('');
  }

  function renderInsights() {
    renderBarChart('#sectorChart', countBy(sectorName), 14);
    renderBarChart('#centreChart', countBy((f) => f.properties?.landing_centre), 8);
  }

  function storeRecent(result) {
    const searches = readStorage(STORAGE.searches);
    const item = {
      id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
      label: result.label, sector: result.sector, date: result.date,
      count: result.matches.length, savedAt: new Date().toISOString(), usedLocation: result.usedLocation,
    };
    searches.unshift(item);
    writeStorage(STORAGE.searches, searches.slice(0, 20));
  }

  function renderHomeRecent() {
    const recent = readStorage(STORAGE.searches).slice(0, 3);
    const container = $('#homeRecent');
    if (!recent.length) {
      container.innerHTML = '<div class="empty-state compact">Your searches will appear here after you explore an area.</div>';
      return;
    }
    container.innerHTML = recent.map((item) => `<button class="recent-row" data-recent-id="${esc(item.id)}"><span class="recent-pin"><svg><use href="#i-pin"/></svg></span><span><strong>${esc(item.label)}</strong><small>${formatDate(item.date)} · ${Number(item.count)} advisory points</small></span><svg class="recent-arrow"><use href="#i-arrow"/></svg></button>`).join('');
    container.querySelectorAll('[data-recent-id]').forEach((button) => button.addEventListener('click', () => replayRecent(button.dataset.recentId)));
  }

  function replayRecent(id) {
    const item = readStorage(STORAGE.searches).find((entry) => entry.id === id);
    if (!item) return;
    if (item.sector) $('#findSector').value = item.sector;
    $('#findCentre').value = item.usedLocation ? '' : (item.sector ? '' : item.label);
    state.currentLocation = null;
    state.currentLocationLabel = '';
    if (item.usedLocation) {
      $('#locationStatus').textContent = 'For privacy, this device location was not saved. Tap “Use my current location” to repeat this search.';
      $('#locationStatus').className = 'inline-status';
      setRoute('find');
      return;
    }
    buildSearch();
  }

  function renderHistory() {
    const searches = readStorage(STORAGE.searches);
    const saved = readStorage(STORAGE.saved);
    $('#historySearches').innerHTML = searches.length ? searches.map((item) => `<article class="history-card"><span class="recent-pin"><svg><use href="#i-history"/></svg></span><span class="history-main"><strong>${esc(item.label)}</strong><small>${formatDate(item.date)} · ${Number(item.count)} advisory point${Number(item.count) === 1 ? '' : 's'} · ${new Date(item.savedAt).toLocaleString()}</small></span><button class="row-arrow" data-replay="${esc(item.id)}" aria-label="Repeat search"><svg><use href="#i-arrow"/></svg></button></article>`).join('') : '<div class="empty-state">No searches yet. Start by choosing a coastal sector.</div>';
    $('#historySaved').innerHTML = saved.length ? saved.map((item) => `<article class="history-card"><span class="recent-pin saved"><svg><use href="#i-bookmark"/></svg></span><span class="history-main"><strong>${esc(item.label)}</strong><small>Saved region · ${formatDate(item.date)}</small></span><button class="row-arrow" data-saved-sector="${esc(item.sector || '')}" aria-label="Search saved region"><svg><use href="#i-arrow"/></svg></button></article>`).join('') : '<div class="empty-state">No saved regions yet. Save a sector from the map.</div>';
    $('#historySearches').querySelectorAll('[data-replay]').forEach((button) => button.addEventListener('click', () => replayRecent(button.dataset.replay)));
    $('#historySaved').querySelectorAll('[data-saved-sector]').forEach((button) => button.addEventListener('click', () => {
      const sector = button.dataset.savedSector;
      if (sector) $('#findSector').value = sector;
      $('#findCentre').value = '';
      state.currentLocation = null;
      setRoute('find');
      buildSearch();
    }));
  }

  function saveCurrentRegion() {
    const sector = $('#mapSector').value;
    const label = sector || 'All coastal sectors';
    const saved = readStorage(STORAGE.saved);
    if (saved.some((item) => item.label === label)) { showToast(`${label} is already saved`); return; }
    saved.unshift({ label, sector, date: state.summary?.snapshot_date || '' });
    if (!writeStorage(STORAGE.saved, saved.slice(0, 20))) return;
    showToast(`${label} saved on this device`);
  }

  function setTheme(theme) {
    try { localStorage.setItem(STORAGE.theme, JSON.stringify(theme)); } catch { /* Theme still applies for this page view. */ }
    const resolved = theme === 'system' ? (matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark') : theme;
    document.documentElement.dataset.theme = resolved;
    $$('[data-theme-choice]').forEach((button) => button.classList.toggle('selected', button.dataset.themeChoice === theme));
  }

  async function checkLocationPermission() {
    const message = $('#settingsMessage');
    if (!navigator.geolocation) { message.textContent = 'This browser does not support location access.'; return; }
    if (!navigator.permissions?.query) { message.textContent = 'Use “Use my current location” on the Find screen to request access when needed.'; return; }
    try {
      const permission = await navigator.permissions.query({ name: 'geolocation' });
      message.textContent = `Browser location permission: ${permission.state}. You can change this in browser site settings.`;
    } catch { message.textContent = 'Use “Use my current location” on the Find screen to request access when needed.'; }
  }

  function bindEvents() {
    document.addEventListener('click', (event) => {
      const routeButton = event.target.closest('[data-route]');
      if (routeButton) {
        const route = routeButton.dataset.route;
        if (route === 'result') renderResultView();
        setRoute(route);
      }
    });
    $('#useLocation').addEventListener('click', locateDevice);
    $('#mapLocate').addEventListener('click', () => {
      setRoute('find');
      window.setTimeout(locateDevice, 100);
    });
    $('#findZonesButton').addEventListener('click', buildSearch);
    $('#findSector').addEventListener('change', () => { $('#locationStatus').textContent = ''; });
    $('#mapSector').addEventListener('change', () => applyMapFilters(true));
    $('#heatToggle').addEventListener('change', () => applyMapFilters(false));
    $('#pointsToggle').addEventListener('change', () => applyMapFilters(false));
    $('#fitMap').addEventListener('click', () => applyMapFilters(true));
    $('#saveAreaButton').addEventListener('click', saveCurrentRegion);
    $('#clearHistory').addEventListener('click', () => {
      try { localStorage.removeItem(STORAGE.searches); } catch { /* Continue with an empty visible list. */ }
      renderHistory();
      renderHomeRecent();
      showToast('Search history cleared');
    });
    $$('.history-tab').forEach((button) => button.addEventListener('click', () => {
      $$('.history-tab').forEach((tab) => tab.classList.toggle('active', tab === button));
      const searches = button.dataset.historyTab === 'searches';
      $('#historySearches').hidden = !searches;
      $('#historySaved').hidden = searches;
    }));
    $$('[data-theme-choice]').forEach((button) => button.addEventListener('click', () => setTheme(button.dataset.themeChoice)));
    $('#settingsLocation').addEventListener('click', checkLocationPermission);
    $('#conditionsLocation').addEventListener('change', () => {
      const feature = state.records[Number($('#conditionsLocation').value)];
      if (feature) {
        const [lat, lon] = coords(feature);
        $('#conditionsLocationHint').textContent = `Selected ${feature.properties?.landing_centre || sectorName(feature)} · ${lat.toFixed(4)}°N, ${lon.toFixed(4)}°E`;
        loadConditions();
      }
    });
    $('#refreshConditions').addEventListener('click', loadConditions);
  }

  async function loadData() {
    try {
      const [summaryResponse, dataResponse] = await Promise.all([
        fetch('/api/pfz/current/summary'), fetch('/api/pfz/current'),
      ]);
      if (!summaryResponse.ok || !dataResponse.ok) throw new Error('The saved INCOIS snapshot could not be loaded.');
      [state.summary, state.records] = await Promise.all([summaryResponse.json(), dataResponse.json()]).then(([summary, geojson]) => [summary, geojson.features || []]);
      fillSelects();
      renderSnapshot();
      renderInsights();
      renderHomeRecent();
      applyMapFilters(true);
    } catch (error) {
      setDataStatus('Data unavailable', 'offline');
      $('#bannerText').textContent = `${error.message} Start the OCEANIX service and reload this page.`;
      $('#dataBanner').classList.add('expired');
    }
  }

  const savedTheme = readStorage(STORAGE.theme, 'dark');
  setTheme(typeof savedTheme === 'string' ? savedTheme : 'dark');
  bindEvents();
  initMap();
  renderHomeRecent();
  loadData();
  const initialRoute = location.hash.slice(1);
  if (initialRoute && $(`[data-view="${initialRoute}"]`)) setRoute(initialRoute);
});
