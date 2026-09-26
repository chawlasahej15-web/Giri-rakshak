(() => {
  const REGION = "india_full";

  const susState = {
    active: false,
    model: "spatial",
    layer: null,
    marker: null,
    metadata: null
  };

  function apiBase() {
    if (
      window.location.hostname === "localhost" ||
      window.location.hostname === "127.0.0.1" ||
      window.location.protocol === "file:"
    ) {
      return "http://127.0.0.1:8000";
    }

    return typeof getApiBase === "function"
      ? getApiBase()
      : "";
  }

  function byId(id) {
    return document.getElementById(id);
  }

  function addUI() {
    const controls = document.querySelector(".filter-controls");
    if (!controls || byId("susceptibility-mode")) return;

    const box = document.createElement("div");
    box.className = "control-group";
    box.id = "susceptibility-mode";

    box.innerHTML = `
      <label>Map Mode</label>

      <div class="sus-toggle">
        <button type="button" id="ner-mode-btn" class="sus-btn active">
          NER EWS
        </button>

        <button type="button" id="sus-mode-btn" class="sus-btn">
          Susceptibility
        </button>
      </div>
    `;

    controls.prepend(box);

    const modelBox = document.createElement("div");
    modelBox.className = "control-group";
    modelBox.id = "sus-model-box";
    modelBox.style.display = "none";

    modelBox.innerHTML = `
      <label>Susceptibility Model</label>

      <div class="sus-toggle">
        <button
          type="button"
          class="sus-btn active"
          data-sus-model="spatial">
          Spatial-matched
        </button>

        <button
          type="button"
          class="sus-btn"
          data-sus-model="hybrid">
          Hybrid
        </button>
      </div>

      <small class="sus-help">
        India · 1-km grid
      </small>
    `;

    controls.appendChild(modelBox);

    byId("ner-mode-btn").onclick = () => setMode(false);
    byId("sus-mode-btn").onclick = () => setMode(true);

    document.querySelectorAll("[data-sus-model]").forEach(btn => {
      btn.onclick = () => {
        susState.model = btn.dataset.susModel;

        document.querySelectorAll("[data-sus-model]").forEach(b => {
          b.classList.toggle(
            "active",
            b.dataset.susModel === susState.model
          );
        });

        if (susState.active) {
          loadSusceptibilityLayer();
        }
      };
    });
  }

  function addSidebarCard() {
    const sidebar = byId("dashboard-sidebar");
    if (!sidebar || byId("susceptibility-analysis-card")) return;

    const card = document.createElement("section");
    card.className = "card";
    card.id = "susceptibility-analysis-card";
    card.style.display = "none";

    card.innerHTML = `
      <div class="card-header">
        <div>
          <h3>Static Susceptibility</h3>
          <div class="sus-subtitle">
            India
          </div>
        </div>
        <span class="badge blue">1-KM GRID</span>
      </div>

      <div id="sus-selection-message" class="sus-selection-message">
        Click a location on the map to inspect the model.
      </div>

      <div class="sus-main-score">
        <div class="sus-label">Selected Model Score</div>
        <div id="sus-score">—</div>
        <span id="sus-percentile">—</span>
      </div>

      <div class="sus-compare">
        <div>
          <span>Spatial-matched</span>
          <strong id="sus-spatial">—</strong>
        </div>

        <div>
          <span>Hybrid</span>
          <strong id="sus-hybrid">—</strong>
        </div>
      </div>

      <div id="sus-location" class="sus-location">
        Location: —
      </div>

      <div class="sus-note">
        Model score, not calibrated real-world probability.
        Color intensity is a relative visualization of scores
        within this pilot region.
      </div>
    `;

    sidebar.prepend(card);
  }

  function showNERSidebar() {
    const ids = [
      "routes-avoid-card",
      "public-alerts-card",
      "telemetry-card",
      "district-alert-box"
    ];

    ids.forEach(id => {
      const node = byId(id);
      if (node) node.style.display = "";
    });

    const oldInference = byId("selected-zone-name");
    if (oldInference) {
      const section = oldInference.closest("section.card");
      if (section) section.style.display = "";
    }

    const susCard = byId("susceptibility-analysis-card");
    if (susCard) susCard.style.display = "none";
  }

  function showSusSidebar() {
    const ids = [
      "routes-avoid-card",
      "public-alerts-card",
      "telemetry-card",
      "district-alert-box"
    ];

    ids.forEach(id => {
      const node = byId(id);
      if (node) node.style.display = "none";
    });

    const oldInference = byId("selected-zone-name");
    if (oldInference) {
      const section = oldInference.closest("section.card");
      if (section) section.style.display = "none";
    }

    const susCard = byId("susceptibility-analysis-card");
    if (susCard) susCard.style.display = "";
  }

  function updateLegend() {
    const legend = document.querySelector(".map-legend");
    if (!legend) return;

    if (!susState.active) {
      legend.innerHTML = `
        <h4>Landslide Hazard Scale</h4>
        <div class="legend-item"><span class="dot watch"></span> Moderate (Orange)</div>
        <div class="legend-item"><span class="dot high"></span> High Hazard (Deep Orange)</div>
        <div class="legend-item"><span class="dot very-high"></span> Very High (Red)</div>
        <div class="legend-item"><span class="dot extreme"></span> Critical / Immediate Risk (Dark Red)</div>
        <hr />
        <div class="legend-item"><span class="dot sensor"></span> <b>Aizawl ESP32 Edge Station</b> (Demo Node)</div>
        <div class="legend-item"><span class="dot citizen"></span> Ground Incident Pin</div>
        <div class="legend-note">Other districts display regional meteorological risk models.</div>
      `;
      return;
    }

    legend.innerHTML = `
      <h4>Static Susceptibility</h4>

      <div class="sus-gradient"></div>

      <div class="sus-gradient-labels">
        <span>Lower score</span>
        <span>Higher score</span>
      </div>

      <div class="legend-note">
        Continuous 1-km susceptibility surface.
        Darker colors indicate higher relative score within this pilot.
      </div>
    `;
  }

  async function loadMetadata() {
    const res = await fetch(
      `${apiBase()}/api/susceptibility/meta/${susState.model}`
    );

    if (!res.ok) {
      throw new Error(`Metadata failed: ${res.status}`);
    }

    return res.json();
  }

  async function loadSusceptibilityLayer() {
    try {
      const meta = await loadMetadata();
      susState.metadata = meta;

      if (susState.layer) {
        map.removeLayer(susState.layer);
        susState.layer = null;
      }

      const url =
        `${apiBase()}/api/susceptibility/tiles/` +
        `${susState.model}/{z}/{x}/{y}.png`;

      const b = meta.bounds;

      susState.layer = L.tileLayer(url, {
        tileSize: 256,

        minZoom: 5,
        maxZoom: 19,
        maxNativeZoom: 8,

        opacity: 0.82,

        updateWhenIdle: true,
        updateWhenZooming: false,
        keepBuffer: 8,

        noWrap: true,

        attribution: "Giri Rakshak · Static Susceptibility",

        bounds: [
          [b.south, b.west],
          [b.north, b.east]
        ]
      }).addTo(map);

      map.fitBounds(
        [
          [b.south, b.west],
          [b.north, b.east]
        ],
        {
          padding: [30, 30],
          maxZoom: 8
        }
      );

      const subtitle = byId("current-forecast-date");
      if (subtitle) {
        subtitle.innerText =
          "Static Susceptibility · India";
      }

    } catch (err) {
      console.error("Susceptibility layer error:", err);

      const msg = byId("sus-selection-message");
      if (msg) {
        msg.innerText =
          "Susceptibility map could not be loaded. Check backend.";
      }
    }
  }

  function removeSusLayer() {
    if (susState.layer) {
      map.removeLayer(susState.layer);
      susState.layer = null;
    }

    if (susState.marker) {
      map.removeLayer(susState.marker);
      susState.marker = null;
    }
  }

  async function setMode(active) {
    susState.active = active;

    byId("ner-mode-btn")?.classList.toggle("active", !active);
    byId("sus-mode-btn")?.classList.toggle("active", active);

    const modelBox = byId("sus-model-box");
    if (modelBox) {
      modelBox.style.display = active ? "" : "none";
    }

    const stateSelect = byId("state-select");
    const districtSelect = byId("district-select");
    const resetBtn = byId("btn-reset-view");

    if (active) {
      if (stateSelect) stateSelect.disabled = true;
      if (districtSelect) districtSelect.disabled = true;

      // Remove old NER demo layers.
      stateLayerGroup.clearLayers();
      zoneLayerGroup.clearLayers();
      hardwareMarkerGroup.clearLayers();
      citizenMarkerGroup.clearLayers();

      if (heatLayerInstance) {
        map.removeLayer(heatLayerInstance);
        heatLayerInstance = null;
      }

      showSusSidebar();
      updateLegend();

      await loadSusceptibilityLayer();

    } else {
      if (stateSelect) stateSelect.disabled = false;
      if (districtSelect) districtSelect.disabled = true;

      removeSusLayer();
      showNERSidebar();
      updateLegend();

      if (typeof renderAllNEROverview === "function") {
        renderAllNEROverview();
      }

      map.flyTo(
        NER_CENTER,
        NER_DEFAULT_ZOOM,
        { duration: 0.8 }
      );
    }
  }

  async function inspectCell(lat, lon) {
    try {
      const res = await fetch(
        `${apiBase()}/api/susceptibility/point` +
        `?lon=${encodeURIComponent(lon)}` +
        `&lat=${encodeURIComponent(lat)}`
      );

      if (!res.ok) {
        throw new Error(`Point failed: ${res.status}`);
      }

      const data = await res.json();

      const active = data[susState.model];

      if (!active || active.score == null) {
        byId("sus-selection-message").innerText =
          "No susceptibility value available at this location.";
        return;
      }

      byId("sus-score").innerText =
        Number(active.score).toFixed(3);

      byId("sus-percentile").innerText =
        `${Number(active.percentile).toFixed(1)} percentile`;

      byId("sus-spatial").innerText =
        data.spatial?.score != null
          ? Number(data.spatial.score).toFixed(3)
          : "—";

      byId("sus-hybrid").innerText =
        data.hybrid?.score != null
          ? Number(data.hybrid.score).toFixed(3)
          : "—";

      byId("sus-location").innerText =
        `Location: ${lat.toFixed(5)}, ${lon.toFixed(5)}`;

      byId("sus-selection-message").innerText =
        `${active.model_label} selected`;

      if (susState.marker) {
        map.removeLayer(susState.marker);
      }

      susState.marker = L.circleMarker(
        [lat, lon],
        {
          radius: 7,
          color: "#ffffff",
          weight: 2,
          fillColor: "#111827",
          fillOpacity: 0.95
        }
      ).addTo(map);

    } catch (err) {
      console.error("Susceptibility point error:", err);

      byId("sus-selection-message").innerText =
        "Could not read this cell.";
    }
  }

  function init() {
    addUI();
    addSidebarCard();
    updateLegend();

  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
