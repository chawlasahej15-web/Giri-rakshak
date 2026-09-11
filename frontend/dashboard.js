// =========================================================================
// GiriRakshak SIH Early Warning System Engine
// Complete Live Regional Open-Meteo Ingestion + GSI Dendritic Ridge Heatmap
// =========================================================================

const NER_CENTER = [25.8, 93.2];
const NER_DEFAULT_ZOOM = 6;

// 1. Initialize Map
const map = L.map('map', {
  center: NER_CENTER,
  zoom: NER_DEFAULT_ZOOM,
  zoomControl: false
});

L.control.zoom({ position: 'bottomright' }).addTo(map);

// Google Maps Terrain/Roads Layer
L.tileLayer('https://mt1.google.com/vt/lyrs=p&hl=en&x={x}&y={y}&z={z}', {
  maxZoom: 18,
  attribution: '© Google Maps | GiriRakshak EWS SIH'
}).addTo(map);

// Layer Groups
const stateLayerGroup = L.layerGroup().addTo(map);
const rasterHeatmapGroup = L.layerGroup().addTo(map);
const zoneLayerGroup = L.layerGroup().addTo(map);
const hardwareMarkerGroup = L.layerGroup().addTo(map);
const citizenMarkerGroup = L.layerGroup().addTo(map);

// 2. Comprehensive 8-State Geological Coordinates & District Directory
const nerData = {
  mizoram: {
    name: "Mizoram",
    center: [23.35, 92.85],
    zoom: 9,
    boundary: [
      [24.52, 92.98], [24.25, 93.28], [23.85, 93.30], [23.00, 93.42],
      [22.18, 93.05], [21.95, 92.80], [22.45, 92.55], [23.40, 92.25],
      [24.15, 92.48], [24.45, 92.70]
    ],
    districts: {
      aizawl: {
        name: "Aizawl",
        isHardwareNode: true,
        center: [23.7307, 92.7173],
        zoom: 13,
        riskLevel: "extreme",
        riskScore: 94.2,
        alertTitle: "EXTREME CRITICAL: Laipuitlang & Ramhlun Urban Cuts",
        alertText: "Continuous physical telemetry confirms accelerating slope creep (18.2° tilt) following heavy saturation. Immediate structural danger.",
        telemetry: { tilt: 18.2, moisture: 89, rain: 114 },
        zones: [
          {
            name: "Laipuitlang Urban Slope Cut",
            riskLevel: "extreme",
            riskScore: 94.5,
            polygon: [[23.736, 92.712], [23.746, 92.721], [23.739, 92.733], [23.729, 92.722]],
            why: "Steep excavated cut angle (39°) in Surma sandstone with high pore pressure undercutting the slope toe.",
            shap: [
              { factor: "Antecedent Rain (24h)", impact: 0.45 },
              { factor: "Slope Incline (39°)", impact: 0.32 },
              { factor: "Soil Saturation (FC-28)", impact: 0.22 },
              { factor: "Structural Overburden", impact: 0.14 }
            ]
          }
        ],
        sensorCoords: [23.739, 92.719]
      },
      lunglei: {
        name: "Lunglei",
        isHardwareNode: false,
        center: [22.8878, 92.7417],
        zoom: 13,
        riskLevel: "high",
        riskScore: 68.0,
        alertTitle: "HIGH HAZARD: Lunglei Highway Corridor",
        alertText: "Live satellite & AWS precipitation indicates potential shallow mud slips along tertiary road excavations.",
        telemetry: { tilt: 8.4, moisture: 73, rain: 68 },
        zones: [
          {
            name: "Lunglei Valley Highway Section",
            riskLevel: "high",
            riskScore: 68.0,
            polygon: [[22.880, 92.733], [22.895, 92.741], [22.891, 92.754], [22.875, 92.743]],
            why: "Precipitation exceeding historical threshold for weathered clay-silt deposits.",
            shap: [
              { factor: "Precipitation Accumulation", impact: 0.35 },
              { factor: "Excavated Cut Slope", impact: 0.25 },
              { factor: "Soil Moisture Ratio", impact: 0.16 }
            ]
          }
        ]
      }
    }
  },

  nagaland: {
    name: "Nagaland",
    center: [26.1584, 94.5624],
    zoom: 8,
    boundary: [
      [27.02, 95.25], [26.85, 95.35], [26.05, 94.88], [25.55, 94.55],
      [25.52, 93.65], [25.92, 93.75], [26.50, 94.30], [26.95, 94.85]
    ],
    districts: {
      dimapur: {
        name: "Dimapur (Paglapahar)",
        isHardwareNode: false,
        center: [25.9042, 93.7279],
        zoom: 13,
        riskLevel: "extreme",
        riskScore: 86.4,
        alertTitle: "EXTREME RISK: NH-29 Paglapahar Gorge",
        alertText: "Live rainfall telemetry alerts to acute mudflow hazard along fractured Disang shale formations.",
        telemetry: { tilt: 14.1, moisture: 84, rain: 102 },
        zones: [
          {
            name: "NH-29 Paglapahar Choke",
            riskLevel: "extreme",
            riskScore: 86.4,
            polygon: [[25.892, 93.712], [25.914, 93.724], [25.910, 93.745], [25.888, 93.732]],
            why: "Unconsolidated valley strata subject to high kinetic hydraulic flow from upper ridges.",
            shap: [
              { factor: "Cumulative Rain", impact: 0.42 },
              { factor: "Unconsolidated Strata", impact: 0.30 }
            ]
          }
        ]
      },

      kohima: {
        name: "Kohima",
        isHardwareNode: false,
        center: [25.6751, 94.1086],
        zoom: 13,
        riskLevel: "very-high",
        riskScore: 74.5,
        alertTitle: "VERY HIGH RISK: Kohima Urban Ridge",
        alertText: "Model shows sub-surface saturation driving creeping subsidence on terrace residential slopes.",
        telemetry: { tilt: 8.5, moisture: 68, rain: 55 },
        zones: [
          {
            name: "Kohima Bypass Cutting",
            riskLevel: "very-high",
            riskScore: 74.5,
            polygon: [[25.666, 94.099], [25.683, 94.108], [25.680, 94.121], [25.660, 94.111]],
            why: "High residential loading on slopes steeper than 35° on weathered shale basement.",
            shap: [
              { factor: "Subsoil Saturation", impact: 0.34 },
              { factor: "Slope Gradient (35°)", impact: 0.28 }
            ]
          }
        ]
      }
    }
  },

  sikkim: {
    name: "Sikkim",
    center: [27.5330, 88.5122],
    zoom: 9,
    boundary: [
      [28.12, 88.65], [27.95, 88.88], [27.35, 88.92], [27.08, 88.75],
      [27.10, 88.10], [27.75, 88.05], [28.05, 88.35]
    ],
    districts: {
      gangtok: {
        name: "Gangtok",
        isHardwareNode: false,
        center: [27.3389, 88.6065],
        zoom: 13,
        riskLevel: "extreme",
        riskScore: 88.0,
        alertTitle: "EXTREME HAZARD: Gangtok Spur & JN Road",
        alertText: "Live open-meteo readings calculate high probability of debris flow along fractured gneiss joints.",
        telemetry: { tilt: 13.6, moisture: 82, rain: 94 },
        zones: [
          {
            name: "JN Road Slope",
            riskLevel: "extreme",
            riskScore: 88.0,
            polygon: [[27.329, 88.595], [27.348, 88.607], [27.344, 88.620], [27.325, 88.608]],
            why: "Rainfall infiltration lubricating pre-existing tectonic joint planes on a 42° slope.",
            shap: [
              { factor: "Rainfall", impact: 0.44 },
              { factor: "Slope Angle (42°)", impact: 0.32 }
            ]
          }
        ]
      }
    }
  },

  assam: {
    name: "Assam",
    center: [26.2006, 92.9376],
    zoom: 7,
    boundary: [
      [27.95, 96.00], [27.50, 95.80], [26.80, 93.80], [25.00, 93.10],
      [24.50, 92.60], [25.80, 90.00], [26.20, 89.80], [26.85, 92.10]
    ],
    districts: {
      dima_hasao: {
        name: "Dima Hasao (Haflong)",
        isHardwareNode: false,
        center: [25.1706, 93.0238],
        zoom: 13,
        riskLevel: "extreme",
        riskScore: 92.8,
        alertTitle: "EXTREME CRITICAL: Haflong Rail Link Sinking Cut",
        alertText: "Live meteorological feed triggers alert for rail embankment subsidence.",
        telemetry: { tilt: 19.5, moisture: 92, rain: 135 },
        zones: [
          {
            name: "Haflong Railway Cutting",
            riskLevel: "extreme",
            riskScore: 92.8,
            polygon: [[25.161, 93.013], [25.180, 93.023], [25.176, 93.038], [25.156, 93.024]],
            why: "Unconsolidated railway cutting slopes failing under saturated hydrostatic loading.",
            shap: [
              { factor: "Rainfall Volume", impact: 0.48 },
              { factor: "Soil Saturation", impact: 0.34 }
            ]
          }
        ]
      }
    }
  },

  meghalaya: {
    name: "Meghalaya",
    center: [25.4670, 91.3662],
    zoom: 8,
    boundary: [
      [26.15, 91.80], [25.85, 92.75], [25.10, 92.75], [25.10, 89.85],
      [25.95, 90.00], [26.05, 91.20]
    ],
    districts: {
      east_khasi_hills: {
        name: "East Khasi Hills (Sohra)",
        isHardwareNode: false,
        center: [25.2986, 91.7180],
        zoom: 13,
        riskLevel: "extreme",
        riskScore: 91.5,
        alertTitle: "EXTREME CRITICAL: Sohra Escarpment",
        alertText: "Live precipitation exceeds hazard threshold. Cascading debris slides likely on canyon flanks.",
        telemetry: { tilt: 14.2, moisture: 88, rain: 190 },
        zones: [
          {
            name: "Mawkdok Canyon Slope",
            riskLevel: "extreme",
            riskScore: 91.5,
            polygon: [[25.289, 91.706], [25.310, 91.718], [25.305, 91.732], [25.284, 91.719]],
            why: "Near-vertical sandstone cliffs experiencing shear failures after hyper-precipitation events.",
            shap: [
              { factor: "Antecedent Rain", impact: 0.54 },
              { factor: "Escarpment Incline", impact: 0.30 }
            ]
          }
        ]
      }
    }
  },

  manipur: {
    name: "Manipur",
    center: [24.8170, 93.9368],
    zoom: 8,
    boundary: [
      [25.68, 94.45], [25.20, 94.75], [24.15, 94.35], [23.85, 93.10],
      [24.50, 93.05], [25.50, 93.55]
    ],
    districts: {
      noney: {
        name: "Noney (Tupul)",
        isHardwareNode: false,
        center: [24.7937, 93.5828],
        zoom: 13,
        riskLevel: "extreme",
        riskScore: 94.8,
        alertTitle: "EXTREME CRITICAL: Tupul Railway River Basin",
        alertText: "Live feed alerts to high probability of historical slip reactivation along Ijei river cut.",
        telemetry: { tilt: 20.8, moisture: 94, rain: 128 },
        zones: [
          {
            name: "Ijei River Slide Basin",
            riskLevel: "extreme",
            riskScore: 94.8,
            polygon: [[24.784, 93.571], [24.804, 93.582], [24.800, 93.597], [24.778, 93.584]],
            why: "Heavily disturbed colluvium on steep riverbanks under continuous base undercutting.",
            shap: [
              { factor: "Historical Slip Factor", impact: 0.49 },
              { factor: "River Undercutting", impact: 0.35 }
            ]
          }
        ]
      }
    }
  },

  arunachal: {
    name: "Arunachal Pradesh",
    center: [28.2180, 94.7278],
    zoom: 7,
    boundary: [
      [29.30, 96.50], [28.00, 97.40], [27.00, 95.80], [26.85, 92.10],
      [27.50, 91.80], [28.00, 92.50], [28.80, 94.00]
    ],
    districts: {
      tawang: {
        name: "Tawang",
        isHardwareNode: false,
        center: [27.5861, 91.8594],
        zoom: 13,
        riskLevel: "high",
        riskScore: 65.0,
        alertTitle: "HIGH RISK: Sela Pass Apron",
        alertText: "Live meteorological precipitation indicates loose scree and rockfall danger.",
        telemetry: { tilt: 7.2, moisture: 64, rain: 45 },
        zones: [
          {
            name: "Sela Pass Apron",
            riskLevel: "high",
            riskScore: 65.0,
            polygon: [[27.577, 91.849], [27.596, 91.859], [27.593, 91.872], [27.572, 91.860]],
            why: "Frost shattering loosening high-elevation bedrock scree onto highway corridors.",
            shap: [
              { factor: "Elevation Gradient", impact: 0.35 },
              { factor: "Rainfall", impact: 0.24 }
            ]
          }
        ]
      }
    }
  },

  tripura: {
    name: "Tripura",
    center: [23.8315, 91.2868],
    zoom: 8,
    boundary: [
      [24.50, 92.20], [24.10, 92.40], [23.00, 91.90], [23.00, 91.30],
      [23.70, 91.15], [24.20, 91.80]
    ],
    districts: {
      dhalai: {
        name: "Dhalai (Atharamura)",
        isHardwareNode: false,
        center: [23.8520, 91.8533],
        zoom: 13,
        riskLevel: "high",
        riskScore: 62.0,
        alertTitle: "HIGH WATCH: Atharamura Range NH-08",
        alertText: "Roadside cut slopes showing minor displacement along soft sedimentary strata.",
        telemetry: { tilt: 6.8, moisture: 60, rain: 52 },
        zones: [
          {
            name: "Atharamura Range NH-08",
            riskLevel: "high",
            riskScore: 62.0,
            polygon: [[23.842, 91.842], [23.861, 91.853], [23.857, 91.866], [23.837, 91.854]],
            why: "Rainfall softening silty clay strata along road infrastructure cuttings.",
            shap: [
              { factor: "Road Excavation", impact: 0.32 },
              { factor: "Rainfall (24h)", impact: 0.24 }
            ]
          }
        ]
      }
    }
  }
};

// 3. Pre-Seeded Ground Citizen Reports
const seedCitizenReports = [
  {
    coords: [23.733, 92.715],
    text: "Active 4-inch tension crack observed across Ramhlun bypass asphalt.",
    type: "Road Surface Tension Crack",
    place: "Aizawl, Mizoram"
  },
  {
    coords: [25.908, 93.731],
    text: "Loose rock boulders rolling onto road near Paglapahar bridge.",
    type: "Mud / Rock Runoff",
    place: "Dimapur, Nagaland"
  },
  {
    coords: [27.342, 88.611],
    text: "Mudflow spilling over concrete retaining barrier on JN Road.",
    type: "Mud / Rock Runoff",
    place: "Gangtok, Sikkim"
  },
  {
    coords: [25.174, 93.028],
    text: "Embankment slump observed near railway track foundation.",
    type: "Retaining Wall Tilt",
    place: "Haflong, Assam"
  }
];

// 4. Multilingual Dispatch Translations
const translations = {
  en: "Warning: High landslide hazard detected on slope cuts. Evacuate immediately.",
  mz: "Fimkhurna: He laiah hian leimin hlauhawm a awm. Kham bul atangin inthiarfihlim vat rawh u.",
  as: "সাৱধান: পাহাৰীয়া অঞ্চলত ভূমিস্খলনৰ প্ৰৱল আশংকা। অবিলম্বে সুৰক্ষিত স্থানলৈ যাওক।",
  bn: "সতর্কতা: বিপজ্জনক পাহাড়ী ঢালে ভূমিধসের সম্ভাবনা। দ্রুত নিরাপদ আশ্রয়ে যান।"
};

function getHazardColor(scoreOrLevel) {
  if (typeof scoreOrLevel === 'string') {
    switch (scoreOrLevel.toLowerCase()) {
      case 'critical':
      case 'extreme':
        return '#991b1b';
      case 'very-high':
        return '#dc2626';
      case 'high':
        return '#ea580c';
      case 'moderate':
      default:
        return '#f97316';
    }
  }

  const score = Number(scoreOrLevel) || 0;

  if (score >= 90) return '#991b1b';
  if (score >= 75) return '#dc2626';
  if (score >= 60) return '#ea580c';

  return '#f97316';
}

// 5. Chart.js Implementation
let telemetryChart;

function initChart() {
  const ctx = document.getElementById('telemetryChart').getContext('2d');

  telemetryChart = new Chart(ctx, {
    type: 'line',

    data: {
      labels: ['-20s', '-16s', '-12s', '-8s', '-4s', 'Now'],

      datasets: [
        {
          label: 'Tilt (°)',
          data: [5.0, 8.0, 11.0, 14.0, 16.0, 18.2],
          borderColor: '#ea580c',
          backgroundColor: 'rgba(234, 88, 12, 0.1)',
          tension: 0.3,
          borderWidth: 2,
          pointRadius: 3,
          fill: true
        },

        {
          label: 'Moisture (%)',
          data: [65, 70, 75, 80, 85, 89],
          borderColor: '#0284c7',
          backgroundColor: 'rgba(2, 132, 199, 0.1)',
          tension: 0.3,
          borderWidth: 2,
          pointRadius: 3,
          fill: true
        }
      ]
    },

    options: {
      responsive: true,
      maintainAspectRatio: false,

      scales: {
        x: {
          grid: {
            color: '#f1f5f9'
          },
          ticks: {
            color: '#64748b',
            font: {
              size: 9
            }
          }
        },

        y: {
          grid: {
            color: '#f1f5f9'
          },
          ticks: {
            color: '#64748b',
            font: {
              size: 9
            }
          }
        }
      },

      plugins: {
        legend: {
          labels: {
            color: '#0f172a',
            boxWidth: 10,
            font: {
              size: 9,
              weight: 'bold'
            }
          }
        }
      }
    }
  });
}

// =========================================================================
// 6. Real-Time Open-Meteo Weather API Integration (All 8 NER States)
// =========================================================================

async function fetchLiveWeatherForDistrict(lat, lng) {
  try {
    const url =
      `https://api.open-meteo.com/v1/forecast?latitude=${lat}` +
      `&longitude=${lng}` +
      `&current=precipitation,soil_moisture_0_to_1cm` +
      `&daily=precipitation_sum` +
      `&timezone=auto`;

    const res = await fetch(url);

    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }

    const data = await res.json();

    const rawSoil =
      data.current?.soil_moisture_0_to_1cm ?? 0.35;

    const moistPercent =
      Math.min(
        98,
        Math.max(
          30,
          Math.round(rawSoil * 180)
        )
      );

    const dailyRain =
      data.daily?.precipitation_sum?.[0] ??
      Math.round(Math.random() * 40 + 30);

    return {
      rain: Math.round(dailyRain),
      moisture: moistPercent
    };

  } catch (err) {

    console.warn(
      `[Open-Meteo] Live API unreachable for [${lat}, ${lng}]. Using baseline.`,
      err.message
    );

    return null;
  }
}

// Synchronize all 8 NER states with live API data on load
// (Updates memory without wiping markers)
async function syncAllRegionalLiveFeeds() {

  for (const sKey of Object.keys(nerData)) {

    const state = nerData[sKey];

    for (const dKey of Object.keys(state.districts)) {

      const dist = state.districts[dKey];

      // Physical Aizawl node is handled separately.
      if (dist.isHardwareNode) {
        continue;
      }

      const live =
        await fetchLiveWeatherForDistrict(
          dist.center[0],
          dist.center[1]
        );

      if (live) {

        dist.telemetry.rain =
          live.rain;

        dist.telemetry.moisture =
          live.moisture;

        const calculatedRisk =
          Math.min(
            96,
            Math.max(
              45,
              Math.round(
                live.rain * 0.45 +
                live.moisture * 0.4
              )
            )
          );

        dist.riskScore =
          calculatedRisk;

        if (calculatedRisk >= 85) {
          dist.riskLevel = 'extreme';
        } else if (calculatedRisk >= 75) {
          dist.riskLevel = 'very-high';
        } else {
          dist.riskLevel = 'high';
        }
      }
    }
  }
}

// ===========================================
// BACKEND ML RISK DATA
// ===========================================

let backendRiskZones = [];

async function loadBackendRiskZones() {

  try {

    const response =
      await fetch(
        `${getApiBase()}/api/risk-zones`
      );

    if (!response.ok) {
      throw new Error(
        `API returned ${response.status}`
      );
    }

    const zones =
      await response.json();

    backendRiskZones =
      Array.isArray(zones)
        ? zones
        : [];

    console.log(
      'REAL BACKEND ML RISK ZONES:',
      backendRiskZones
    );

    renderBackendRiskZones(
      backendRiskZones
    );

    return backendRiskZones;

  } catch (error) {

    console.error(
      'Failed to load backend risk zones:',
      error
    );

    backendRiskZones = [];

    return [];
  }
}

// =====================================================
// LIVE ESP32 TELEMETRY
// =====================================================

let latestSensorReading = null;
let selectedBackendZoneId = null;
let telemetryViewMode = 'overview';

function getApiBase() {
  return (
    window.location.hostname === 'localhost' ||
    window.location.hostname === '127.0.0.1'
  )
    ? 'http://127.0.0.1:8000'
    : 'https://YOUR-ACTUAL-RENDER-URL.onrender.com';
}

async function loadLatestSensorTelemetryForZone(zoneId) {

  try {

    const response =
      await fetch(
        `${getApiBase()}/api/sensor-data/latest/${encodeURIComponent(zoneId)}`,
        {
          cache: 'no-store'
        }
      );

    if (!response.ok) {
      throw new Error(
        `API returned ${response.status}`
      );
    }

    const data =
      await response.json();

    if (
      data.status !== 'ok' ||
      !data.reading
    ) {

      console.warn(
        `No sensor telemetry for ${zoneId}`
      );

      return;
    }

    // Ignore stale response if user clicked
    // another zone meanwhile.
    if (
      selectedBackendZoneId !== zoneId
    ) {
      return;
    }

    const reading =
      data.reading;

    const tilt =
      Number(reading.tilt_deg);

    const moisture =
      Number(reading.moisture_pct);

    document.getElementById(
      'telemetry-card-title'
    ).innerText =
      `${zoneId} — Sensor Telemetry`;

    document.getElementById(
      'telemetry-source-desc'
    ).innerText =
      `Data Source: Sensor Simulation / ESP32 Pipeline • Updated ${formatSensorTime(reading.timestamp)}`;

    document.getElementById(
      'hardware-badge'
    ).className =
      'badge blue';

    document.getElementById(
      'hardware-badge'
    ).innerText =
      'SENSOR DATA';

    document.getElementById(
      'val-tilt'
    ).innerText =
      Number.isFinite(tilt)
        ? `${tilt.toFixed(1)}°`
        : '—';

    document.getElementById(
      'val-moisture'
    ).innerText =
      Number.isFinite(moisture)
        ? `${moisture.toFixed(1)}%`
        : '—';

    // No rainfall sensor in simulator payload.
    document.getElementById(
      'val-rain'
    ).innerText =
      '—';

    if (
      telemetryChart &&
      telemetryChart.data &&
      telemetryChart.data.datasets.length >= 2
    ) {

      const tiltData =
        telemetryChart.data.datasets[0].data;

      const moistureData =
        telemetryChart.data.datasets[1].data;

      tiltData.fill(tilt);
      moistureData.fill(moisture);

      telemetryChart.update('none');
    }

    console.log(
      `ZONE SENSOR TELEMETRY [${zoneId}]:`,
      reading
    );

  } catch (error) {

    console.warn(
      `Failed to load telemetry for ${zoneId}:`,
      error
    );
  }
}

function formatSensorTime(timestamp) {

  if (!timestamp) {
    return 'time unavailable';
  }

  const date =
    new Date(timestamp);

  if (
    Number.isNaN(
      date.getTime()
    )
  ) {
    return timestamp;
  }

  return date.toLocaleString();
}

// =====================================================
// TELEMETRY VIEW ROUTER
// =====================================================
// Overview -> no fabricated sensor values.
// Hardware view -> the physical ESP32_01 node only.
// Selected backend ML zone -> that zone's own simulator/sensor data.

async function loadLatestSensorTelemetry() {

  if (
    telemetryViewMode !== 'hardware'
  ) {
    return null;
  }

  return loadLatestSensorTelemetryBySensorId(
    'ESP32_01'
  );
}

async function loadLatestSensorTelemetryBySensorId(
  sensorId
) {

  try {

    const response =
      await fetch(
        `${getApiBase()}/api/sensor-data/latest/${encodeURIComponent(sensorId)}`,
        {
          cache: 'no-store'
        }
      );

    if (!response.ok) {
      throw new Error(
        `API returned ${response.status}`
      );
    }

    const data =
      await response.json();

    if (
      data.status !== 'ok' ||
      !data.reading
    ) {

      console.warn(
        `No sensor telemetry for ${sensorId}`
      );

      return null;
    }

    const reading =
      data.reading;

    latestSensorReading =
      reading;

    const tilt =
      Number(reading.tilt_deg);

    const moisture =
      Number(reading.moisture_pct);

    document.getElementById(
      'telemetry-card-title'
    ).innerText =
      `${sensorId} — ESP32 Edge Telemetry`;

    document.getElementById(
      'telemetry-source-desc'
    ).innerText =
      `Data Source: Physical ESP32 Sensor • Updated ${formatSensorTime(reading.timestamp)}`;

    document.getElementById(
      'hardware-badge'
    ).className =
      'badge purple';

    document.getElementById(
      'hardware-badge'
    ).innerText =
      'LIVE HARDWARE';

    document.getElementById(
      'val-tilt'
    ).innerText =
      Number.isFinite(tilt)
        ? `${tilt.toFixed(1)}°`
        : '—';

    document.getElementById(
      'val-moisture'
    ).innerText =
      Number.isFinite(moisture)
        ? `${moisture.toFixed(1)}%`
        : '—';

    document.getElementById(
      'val-rain'
    ).innerText =
      '—';

    if (
      telemetryChart &&
      telemetryChart.data &&
      telemetryChart.data.datasets.length >= 2
    ) {

      telemetryChart.data.datasets[0].data = [
        tilt,
        tilt,
        tilt,
        tilt,
        tilt,
        tilt
      ];

      telemetryChart.data.datasets[1].data = [
        moisture,
        moisture,
        moisture,
        moisture,
        moisture,
        moisture
      ];

      telemetryChart.update('none');
    }

    console.log(
      `HARDWARE SENSOR TELEMETRY [${sensorId}]:`,
      reading
    );

    return reading;

  } catch (error) {

    console.warn(
      `Failed to load telemetry for ${sensorId}:`,
      error
    );

    return null;
  }
}

async function refreshTelemetry() {

  if (
    telemetryViewMode === 'ml-zone' &&
    selectedBackendZoneId
  ) {

    await loadLatestSensorTelemetryForZone(
      selectedBackendZoneId
    );

    return;
  }

  if (
    telemetryViewMode === 'hardware'
  ) {

    await loadLatestSensorTelemetry();

    return;
  }

  // Overview intentionally does not show
  // a random/last simulator reading.
}

function renderBackendRiskZones(zones) {

  console.log(
    `Rendering ${zones.length} real backend risk zones`
  );

  zones.forEach(zone => {

    const lat =
      Number(zone.lat);

    const lon =
      Number(zone.lon);

    const score =
      Number(
        zone.risk_score || 0
      );

    const level =
      String(
        zone.risk_level || 'Unknown'
      );

    if (
      !Number.isFinite(lat) ||
      !Number.isFinite(lon)
    ) {

      console.warn(
        'Skipping invalid zone coordinates:',
        zone
      );

      return;
    }

    const color =
      getHazardColor(score);

    const marker =
      L.circleMarker(
        [lat, lon],
        {
          radius:
            score >= 80
              ? 12
              : score >= 60
                ? 10
                : 8,

          color: '#ffffff',
          weight: 2,
          fillColor: color,
          fillOpacity: 0.9
        }
      );

    marker.bindTooltip(
      `<b>${zone.zone_id}</b><br>` +
      `Risk: ${score.toFixed(1)}%<br>` +
      `Level: ${level.toUpperCase()}`
    );

    marker.bindPopup(
      `<div style="min-width:190px;">` +
      `<strong>${zone.zone_id}</strong><br>` +
      `Risk Score: <strong>${score.toFixed(1)}%</strong><br>` +
      `Risk Level: <strong>${level.toUpperCase()}</strong><br>` +
      `<span style="font-size:11px;color:#64748b;">REAL BACKEND ML OUTPUT</span>` +
      `</div>`
    );

    marker.on(
      'click',
      () => {
        updateBackendZoneView(
          zone
        );
      }
    );

    zoneLayerGroup.addLayer(
      marker
    );
  });

  console.log(
    `Real backend zones rendered: ${zones.length}`
  );
}

// =========================================================================
// 7. Dendritic Geological Ridge Heatmap
// =========================================================================

function renderDendriticRidgeHeatmap() {

  rasterHeatmapGroup.clearLayers();

  const bounds = [
    [24.8, 93.1],
    [27.2, 95.3]
  ];

  const svgHeatmap = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800" width="100%" height="100%">
      <defs>
        <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="4" result="blur" />
          <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
      </defs>

      <!-- 1. Regional Blue Catchment Wash -->
      <path d="
        M 210,540
        Q 230,460 270,410
        T 340,320
        T 420,240
        T 520,150
        T 570,120
        Q 590,160 560,230
        T 510,340
        T 460,430
        T 420,530
        T 360,630
        Q 290,660 240,620
        Z"
        fill="#38bdf8"
        fill-opacity="0.38"
        filter="url(#glow)"
      />

      <path
        d="M 280,430 Q 320,380 390,360 T 480,280"
        fill="none"
        stroke="#7dd3fc"
        stroke-width="32"
        stroke-linecap="round"
        opacity="0.35"
        filter="url(#glow)"
      />

      <path
        d="M 330,520 Q 370,470 430,410 T 490,360"
        fill="none"
        stroke="#7dd3fc"
        stroke-width="26"
        stroke-linecap="round"
        opacity="0.35"
        filter="url(#glow)"
      />

      <!-- 2. Orange Buffer Slopes -->
      <g
        stroke="#ea580c"
        stroke-linecap="round"
        stroke-linejoin="round"
        fill="none"
        opacity="0.8"
        filter="url(#glow)"
      >
        <path
          d="M 240,560 Q 280,480 330,440 T 410,330 T 490,210 T 540,140"
          stroke-width="15"
        />
        <path
          d="M 330,440 Q 380,410 430,430 T 500,450"
          stroke-width="12"
        />
        <path
          d="M 410,330 Q 460,320 510,290"
          stroke-width="10"
        />
        <path
          d="M 270,590 Q 310,540 360,520 T 430,490"
          stroke-width="12"
        />
      </g>

      <!-- 3. Red Dendritic Ridge Network -->
      <g
        stroke="#991b1b"
        stroke-linecap="round"
        stroke-linejoin="round"
        fill="none"
        opacity="0.95"
      >
        <path
          d="M 240,560 Q 280,480 330,440 T 410,330 T 490,210 T 540,140"
          stroke-width="5.5"
        />

        <path
          d="M 330,440 Q 380,410 430,430 T 500,450"
          stroke-width="4.5"
        />

        <path
          d="M 365,425 Q 395,380 435,370 T 475,340"
          stroke-width="4"
        />

        <path
          d="M 410,330 Q 460,320 510,290"
          stroke-width="4"
        />

        <path
          d="M 450,270 Q 480,250 510,240"
          stroke-width="3.5"
        />

        <path
          d="M 270,590 Q 310,540 360,520 T 430,490"
          stroke-width="4.5"
        />

        <path
          d="M 305,505 Q 340,480 370,475"
          stroke-width="3.5"
        />
      </g>

      <!-- 4. Bright Red Failure Points -->
      <g
        stroke="#dc2626"
        stroke-linecap="round"
        fill="none"
        opacity="0.9"
      >
        <path
          d="M 330,440 L 365,425 L 410,330 L 450,270 L 490,210"
          stroke-width="2.5"
        />
      </g>
    </svg>
  `;

  const svgUrl =
    'data:image/svg+xml;charset=utf-8,' +
    encodeURIComponent(
      svgHeatmap
    );

  const imageOverlay =
    L.imageOverlay(
      svgUrl,
      bounds,
      {
        opacity: 0.85,
        interactive: false
      }
    );

  rasterHeatmapGroup.addLayer(
    imageOverlay
  );
}

// 8. Master Render: Boundaries, Polygons, Single Aizawl ESP Marker & Saved Reports

function renderAllNEROverview() {

  stateLayerGroup.clearLayers();
  zoneLayerGroup.clearLayers();
  hardwareMarkerGroup.clearLayers();
  citizenMarkerGroup.clearLayers();

  renderDendriticRidgeHeatmap();

  Object.keys(nerData).forEach(
    stateKey => {

      const state =
        nerData[stateKey];

      if (state.boundary) {

        const poly =
          L.polygon(
            state.boundary,
            {
              color: '#dc2626',
              weight: 1.5,
              opacity: 0.65,
              fillColor: '#ea580c',
              fillOpacity: 0.08,
              dashArray: '3, 4'
            }
          );

        poly.bindTooltip(
          `<b>${state.name}</b><br/>Regional Landslide Watch Zone`
        );

        poly.on(
          'click',
          () => {
            stateSelect.value =
              stateKey;

            populateDistricts(
              stateKey
            );

            map.flyTo(
              state.center,
              state.zoom
            );
          }
        );

        stateLayerGroup.addLayer(
          poly
        );
      }

      // Local hazard polygons intentionally disabled.
    }
  );

  // ONLY 1 PHYSICAL ESP MARKER: Aizawl, Mizoram

  const aizawlDist =
    nerData
      .mizoram
      .districts
      .aizawl;

  const espIcon =
    L.divIcon({
      html:
        `<div style="background: #7c3aed; border: 2.5px solid white; width: 16px; height: 16px; border-radius: 50%; box-shadow: 0 0 10px rgba(124, 58, 237, 0.85); cursor: pointer;"></div>`,
      iconSize: [16, 16]
    });

  const singleEspMarker =
    L.marker(
      aizawlDist.sensorCoords,
      {
        icon: espIcon
      }
    );

  singleEspMarker.bindTooltip(
    "<b>STAGE DEMONSTRATION NODE</b><br/>Aizawl ESP32 Edge Station (Live Telemetry)",
    {
      permanent: false
    }
  );

  singleEspMarker.on(
    'click',
    () => {

      stateSelect.value =
        'mizoram';

      populateDistricts(
        'mizoram'
      );

      districtSelect.value =
        'aizawl';

      updateDistrictView(
        'mizoram',
        'aizawl'
      );
    }
  );

  hardwareMarkerGroup.addLayer(
    singleEspMarker
  );

  // Render Pre-Seeded Citizen Field Reports

  seedCitizenReports.forEach(
    rep => {

      const citIcon =
        L.divIcon({
          html:
            `<div style="background: #0284c7; border: 2px solid white; width: 14px; height: 14px; border-radius: 3px; box-shadow: 0 0 6px rgba(0,0,0,0.3);"></div>`,
          iconSize: [14, 14]
        });

      const marker =
        L.marker(
          rep.coords,
          {
            icon: citIcon
          }
        );

      marker.bindPopup(
        `<b>Citizen Field Incident</b><br/>` +
        `<b>Type:</b> ${rep.type}<br/>` +
        `<b>Location:</b> ${rep.place}<br/>` +
        `<i>"${rep.text}"</i>`
      );

      citizenMarkerGroup.addLayer(
        marker
      );
    }
  );

  loadSavedCitizenReports();

  resetOverviewSidebar();

  if (
    backendRiskZones.length > 0
  ) {
    renderBackendRiskZones(
      backendRiskZones
    );
  }
}

function resetOverviewSidebar() {

  selectedBackendZoneId = null;
  telemetryViewMode = 'overview';

  document.getElementById(
    'data-source-tag'
  ).innerText =
    "REGIONAL MODEL";

  document.getElementById(
    'data-source-tag'
  ).classList.remove(
    'hardware'
  );

  document.getElementById(
    'risk-badge'
  ).className =
    'badge blue';

  document.getElementById(
    'risk-badge'
  ).innerText =
    'OVERVIEW';

  document.getElementById(
    'district-alert-title'
  ).innerText =
    "North Eastern Region (NER)";

  document.getElementById(
    'district-alert-body'
  ).innerText =
    "Surveillance active across 8 NER states. Select Aizawl to inspect the deployed physical ESP32 edge telemetry.";

  document.getElementById(
    'district-alert-box'
  ).style.borderLeftColor =
    '#0284c7';

  document.getElementById(
    'telemetry-card-title'
  ).innerText =
    "IoT Edge Telemetry";

  document.getElementById(
    'telemetry-source-desc'
  ).innerText =
    "Data Source: Regional Meteorological Model";

  document.getElementById(
    'hardware-badge'
  ).className =
    'badge gray';

  document.getElementById(
    'hardware-badge'
  ).innerText =
    'MODEL DATA';

  // Overview must not display a random/previous sensor reading.
  document.getElementById(
    'val-tilt'
  ).innerText =
    '—';

  document.getElementById(
    'val-moisture'
  ).innerText =
    '—';

  document.getElementById(
    'val-rain'
  ).innerText =
    '—';
}

function updateBackendZoneView(zone) {

  selectedBackendZoneId =
    zone.zone_id;

  telemetryViewMode =
    'ml-zone';

  const score =
    Number(
      zone.risk_score || 0
    );

  const level =
    String(
      zone.risk_level || 'unknown'
    );

  const sourceTag =
    document.getElementById(
      'data-source-tag'
    );

  const hwBadge =
    document.getElementById(
      'hardware-badge'
    );

  const cardTitle =
    document.getElementById(
      'telemetry-card-title'
    );

  const sourceDesc =
    document.getElementById(
      'telemetry-source-desc'
    );

  map.flyTo(
    [
      Number(zone.lat),
      Number(zone.lon)
    ],
    11,
    {
      duration: 1.2
    }
  );

  sourceTag.innerText =
    'LIVE ML BACKEND';

  sourceTag.classList.remove(
    'hardware'
  );

  cardTitle.innerText =
    `${zone.zone_id} — ML Risk Zone`;

  sourceDesc.innerText =
    'Data Source: FastAPI + Validated ML Fusion Pipeline';

  hwBadge.className =
    'badge blue';

  hwBadge.innerText =
    'BACKEND DATA';

  document.getElementById(
    'val-tilt'
  ).innerText =
    '—';

  document.getElementById(
    'val-moisture'
  ).innerText =
    '—';

  document.getElementById(
    'val-rain'
  ).innerText =
    '—';

  const shapZone = {

    name:
      zone.zone_id,

    riskScore:
      score.toFixed(1),

    riskLevel:
      level,

    why:
      'Risk score generated by the backend ML fusion pipeline. ' +
      'The factors below are the model features with the strongest SHAP contribution.',

    shap:
      (zone.top_factors || [])
        .map(
          f => ({
            factor:
              f.feature,

            impact:
              Number(
                f.abs_shap ||
                Math.abs(
                  f.shap_value || 0
                )
              ),

            shap_value:
              Number(
                f.shap_value || 0
              ),

            direction:
              f.direction
          })
        )
  };

  updateShapPanel(
    shapZone,
    zone.zone_id
  );

  loadLatestSensorTelemetryForZone(
    zone.zone_id
  );
}

// 9. Update View on District Selection

async function updateDistrictView(
  stateKey,
  distKey
) {

  selectedBackendZoneId = null;

  const state =
    nerData[stateKey];

  if (!state) {
    return;
  }

  const dist =
    state.districts[distKey];

  if (!dist) {
    return;
  }

  map.flyTo(
    dist.center,
    dist.zoom,
    {
      duration: 1.2
    }
  );

  const isHardware =
    !!dist.isHardwareNode;

  telemetryViewMode =
    isHardware
      ? 'hardware'
      : 'model';

  const sourceTag =
    document.getElementById(
      'data-source-tag'
    );

  const hwBadge =
    document.getElementById(
      'hardware-badge'
    );

  const cardTitle =
    document.getElementById(
      'telemetry-card-title'
    );

  const sourceDesc =
    document.getElementById(
      'telemetry-source-desc'
    );

  if (isHardware) {

    sourceTag.innerText =
      "LIVE ESP32 DEPLOYMENT";

    sourceTag.classList.add(
      'hardware'
    );

    cardTitle.innerText =
      "Aizawl — ESP32 Edge Station";

    sourceDesc.innerText =
      "Waiting for physical ESP32 telemetry...";

    hwBadge.className =
      'badge purple';

    hwBadge.innerText =
      'LIVE HARDWARE';

  } else {

    sourceTag.innerText =
      "LIVE OPEN-METEO & GIS MODEL";

    sourceTag.classList.remove(
      'hardware'
    );

    cardTitle.innerText =
      `${dist.name} — Live Feeds`;

    sourceDesc.innerText =
      "Data Source: Live IMD/Open-Meteo Satellite Precipitation";

    hwBadge.className =
      'badge gray';

    hwBadge.innerText =
      'LIVE MODEL';
  }

  // Display telemetry metrics

  if (isHardware) {

    // Never show fabricated hardware values.
    document.getElementById(
      'val-tilt'
    ).innerText =
      '—';

    document.getElementById(
      'val-moisture'
    ).innerText =
      '—';

    document.getElementById(
      'val-rain'
    ).innerText =
      '—';

  } else {

    document.getElementById(
      'val-tilt'
    ).innerText =
      `${dist.telemetry.tilt}°`;

    document.getElementById(
      'val-moisture'
    ).innerText =
      `${dist.telemetry.moisture}%`;

    document.getElementById(
      'val-rain'
    ).innerText =
      `${dist.telemetry.rain} mm`;
  }

  // Synchronize Line Chart

  if (telemetryChart) {

    if (isHardware) {

      telemetryChart.data.datasets[0].data = [
        null,
        null,
        null,
        null,
        null,
        null
      ];

      telemetryChart.data.datasets[1].data = [
        null,
        null,
        null,
        null,
        null,
        null
      ];

    } else {

      const baseTilt =
        dist.telemetry.tilt;

      const baseM =
        dist.telemetry.moisture;

      telemetryChart.data.datasets[0].data = [
        Math.max(
          0,
          baseTilt - 1.2
        ),
        Math.max(
          0,
          baseTilt - 1.0
        ),
        Math.max(
          0,
          baseTilt - 0.7
        ),
        Math.max(
          0,
          baseTilt - 0.4
        ),
        Math.max(
          0,
          baseTilt - 0.2
        ),
        baseTilt
      ];

      telemetryChart.data.datasets[1].data = [
        baseM - 5,
        baseM - 4,
        baseM - 3,
        baseM - 2,
        baseM - 1,
        baseM
      ];
    }

    telemetryChart.update();
  }

  document.getElementById(
    'district-alert-title'
  ).innerText =
    dist.alertTitle;

  document.getElementById(
    'district-alert-body'
  ).innerText =
    dist.alertText;

  const riskBadge =
    document.getElementById(
      'risk-badge'
    );

  riskBadge.innerText =
    dist.riskLevel.toUpperCase();

  const color =
    getHazardColor(
      dist.riskScore
    );

  riskBadge.style.backgroundColor =
    color;

  riskBadge.style.color =
    '#fff';

  document.getElementById(
    'district-alert-box'
  ).style.borderLeftColor =
    color;

  if (
    dist.zones.length > 0
  ) {

    updateShapPanel(
      dist.zones[0],
      dist.name
    );
  }

  if (isHardware) {

    loadLatestSensorTelemetry();
  }
}

// 10. Explainable AI (SHAP) Panel

function updateShapPanel(
  zone,
  districtName = ""
) {

  document.getElementById(
    'selected-zone-name'
  ).innerText =
    `${
      districtName
        ? districtName + ': '
        : ''
    }${zone.name}`;

  const panel =
    document.getElementById(
      'shap-details'
    );

  const color =
    getHazardColor(
      zone.riskScore
    );

  let factorsHtml =
    zone.shap
      .map(
        item => {

          const isPositive =
            item.impact > 0;

          const barWidth =
            Math.min(
              Math.abs(
                item.impact
              ) * 160,
              100
            );

          return `
            <div class="shap-bar-item">
              <div class="shap-label-row">
                <span style="color: #334155;">
                  ${item.factor}
                </span>

                <span style="color: ${color}; font-weight: bold;">
                  ${
                    isPositive
                      ? '+'
                      : ''
                  }${(
                    item.impact * 100
                  ).toFixed(0)}%
                </span>
              </div>

              <div class="shap-progress-track">
                <div
                  class="shap-progress-fill"
                  style="width: ${barWidth}%; background-color: ${color}"
                ></div>
              </div>
            </div>
          `;
        }
      )
      .join('');

  panel.innerHTML =
    `
      <div class="shap-summary-card">

        <div class="shap-summary-top">

          <div>

            <span
              style="
                font-size: 0.68rem;
                color: #64748b;
                font-weight: 700;
              "
            >
              CALCULATED FAILURE PROBABILITY
            </span>

            <div
              class="shap-score-val"
              style="color: ${color};"
            >
              ${zone.riskScore}%
              [
              ${zone.riskLevel.toUpperCase()}
              ]
            </div>

          </div>

          <span class="badge blue">
            Model: RF + SHAP
          </span>

        </div>

        <div class="shap-why-box">

          <strong>
            Why is this slope at risk?
          </strong>

          <br/>

          ${
            zone.why ||
            "Multiple geotechnical factors combined with sustained precipitation."
          }

        </div>

      </div>

      ${factorsHtml}
    `;
}

// 11. Cascading Dropdown Controls

const stateSelect =
  document.getElementById(
    'state-select'
  );

const districtSelect =
  document.getElementById(
    'district-select'
  );

function populateDistricts(
  selectedState
) {

  districtSelect.innerHTML =
    '<option value="">-- Select District --</option>';

  if (
    !selectedState ||
    !nerData[selectedState]
  ) {

    districtSelect.disabled =
      true;

    return;
  }

  const dists =
    nerData[
      selectedState
    ].districts;

  Object.keys(dists).forEach(
    distKey => {

      const opt =
        document.createElement(
          'option'
        );

      opt.value =
        distKey;

      opt.innerText =
        dists[
          distKey
        ].name +
        (
          dists[
            distKey
          ].isHardwareNode
            ? " 🟣 [Live ESP32 Station]"
            : " (Live Weather Model)"
        );

      districtSelect.appendChild(
        opt
      );
    }
  );

  districtSelect.disabled =
    false;
}

stateSelect.addEventListener(
  'change',
  e => {

    selectedBackendZoneId =
      null;

    telemetryViewMode =
      'overview';

    const selectedState =
      e.target.value;

    if (!selectedState) {

      districtSelect.innerHTML =
        '<option value="">-- Select District --</option>';

      districtSelect.disabled =
        true;

      map.flyTo(
        NER_CENTER,
        NER_DEFAULT_ZOOM
      );

      renderAllNEROverview();

      return;
    }

    populateDistricts(
      selectedState
    );

    map.flyTo(
      nerData[
        selectedState
      ].center,

      nerData[
        selectedState
      ].zoom
    );
  }
);

districtSelect.addEventListener(
  'change',
  e => {

    const selectedDist =
      e.target.value;

    const selectedState =
      stateSelect.value;

    if (
      selectedDist &&
      selectedState
    ) {

      updateDistrictView(
        selectedState,
        selectedDist
      );
    }
  }
);

document.getElementById(
  'btn-reset-view'
).addEventListener(
  'click',
  () => {

    selectedBackendZoneId =
      null;

    telemetryViewMode =
      'overview';

    stateSelect.value =
      "";

    districtSelect.innerHTML =
      '<option value="">-- Select District --</option>';

    districtSelect.disabled =
      true;

    map.flyTo(
      NER_CENTER,
      NER_DEFAULT_ZOOM
    );

    renderAllNEROverview();
  }
);

// 12. Alert Preview & Dispatch Trigger

document.getElementById(
  'lang-select'
).addEventListener(
  'change',
  e => {

    const lang =
      e.target.value;

    document.getElementById(
      'alert-preview-text'
    ).innerText =
      `"${translations[lang]}"`;
  }
);

// This remains the existing demo/manual dispatch UI.
// Actual automatic SMS integration is being handled separately.
document.getElementById('btn-trigger-alert').addEventListener('click', async () => {
  const lang = document.getElementById('lang-select').value;

  try {
    const response = await fetch(`${getApiBase()}/api/trigger-alert`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        zone_id: 'ESP32_01',
        risk_level: 'critical',
        message: translations[lang]
      })
    });

    const result = await response.json();

    if (!response.ok || !result.sms_result?.success) {
      throw new Error(result.sms_result?.error || 'SMS failed');
    }

    alert('Emergency SMS transmitted successfully.');
  } catch (error) {
    console.error('Emergency SMS error:', error);
    alert(`Emergency SMS failed: ${error.message}`);
  }
});

// =========================================================================
// 13. Citizen Field Incident Sync Engine (Listens to report.html)
// =========================================================================

function renderCitizenMarker(
  lat,
  lng,
  hazardType,
  description,
  imageBase64,
  flyTo = false
) {

  const validLat =
    parseFloat(lat);

  const validLng =
    parseFloat(lng);

  if (
    isNaN(validLat) ||
    isNaN(validLng)
  ) {

    console.warn(
      '[Citizen Sync] Invalid coordinates received:',
      lat,
      lng
    );

    return;
  }

  const citIcon =
    L.divIcon({
      html:
        `<div style="background: #0284c7; border: 2.5px solid white; width: 16px; height: 16px; border-radius: 4px; box-shadow: 0 0 10px rgba(2,132,199,0.85); cursor:pointer;"></div>`,
      iconSize: [16, 16]
    });

  const marker =
    L.marker(
      [
        validLat,
        validLng
      ],
      {
        icon: citIcon
      }
    );

  const imgHtml =
    imageBase64
      ? `
        <div style="margin-top:6px;">
          <img
            src="${imageBase64}"
            style="
              width:100%;
              height:110px;
              object-fit:cover;
              border-radius:6px;
              display:block;
            "
            alt="Field Photo"
          />
        </div>
      `
      : '';

  marker.bindPopup(
    `
      <div
        style="
          min-width: 180px;
          max-width: 220px;
        "
      >

        <span
          class="badge blue"
          style="
            margin-bottom: 4px;
            display:inline-block;
            font-size:0.65rem;
            padding:2px 6px;
            border-radius:3px;
            background:#e0f2fe;
            color:#0369a1;
            font-weight:bold;
          "
        >
          GROUND CITIZEN REPORT
        </span>

        <h4
          style="
            font-size: 0.86rem;
            color: #0f172a;
            margin: 0;
          "
        >
          ${hazardType}
        </h4>

        <p
          style="
            font-size: 0.76rem;
            color: #475569;
            margin: 4px 0 6px;
          "
        >
          "${description}"
        </p>

        ${imgHtml}

        <small
          style="
            color: #94a3b8;
            font-size: 0.65rem;
            display:block;
            margin-top:4px;
          "
        >
          GPS:
          ${validLat.toFixed(4)},
          ${validLng.toFixed(4)}
        </small>

      </div>
    `
  );

  citizenMarkerGroup.addLayer(
    marker
  );

  if (flyTo) {

    map.flyTo(
      [
        validLat,
        validLng
      ],
      Math.max(
        map.getZoom(),
        13
      ),
      {
        duration: 1.0
      }
    );

    setTimeout(
      () => {
        marker.openPopup();
      },
      1100
    );
  }
}

// Load and display all reports saved in localStorage

function loadSavedCitizenReports() {

  try {

    const storedReports =
      JSON.parse(
        localStorage.getItem(
          'giri_citizen_reports'
        ) || '[]'
      );

    const isRedirect =
      sessionStorage.getItem(
        'just_reported'
      ) === 'true';

    storedReports.forEach(
      (r, idx) => {

        const lat =
          r.lat ||
          r.latitude;

        const lng =
          r.lng ||
          r.lon ||
          r.longitude;

        const type =
          r.type ||
          r.hazard_type ||
          "Ground Incident";

        const desc =
          r.desc ||
          r.description ||
          "";

        const isLatest =
          idx ===
          storedReports.length - 1;

        renderCitizenMarker(
          lat,
          lng,
          type,
          desc,
          r.image,
          isLatest &&
          isRedirect
        );
      }
    );

    sessionStorage.removeItem(
      'just_reported'
    );

  } catch (err) {

    console.warn(
      '[Citizen Sync] Local reports load failed:',
      err
    );
  }
}

// Live Multi-Tab Sync

window.addEventListener(
  'storage',
  e => {

    if (
      e.key === 'giri_latest_report' &&
      e.newValue
    ) {

      try {

        const r =
          JSON.parse(
            e.newValue
          );

        const lat =
          r.lat ||
          r.latitude;

        const lng =
          r.lng ||
          r.lon ||
          r.longitude;

        const type =
          r.type ||
          r.hazard_type ||
          "Ground Incident";

        const desc =
          r.desc ||
          r.description ||
          "";

        renderCitizenMarker(
          lat,
          lng,
          type,
          desc,
          r.image,
          true
        );

      } catch (err) {

        console.warn(
          '[Citizen Sync] Invalid report payload:',
          err
        );
      }
    }
  }
);

// 14. Global Search & Autocomplete

const searchInput =
  document.getElementById(
    'global-search-input'
  );

const searchDropdown =
  document.getElementById(
    'search-suggestions'
  );

const searchClearBtn =
  document.getElementById(
    'search-clear-btn'
  );

function buildLocationIndex() {

  const index = [];

  Object.entries(
    nerData
  ).forEach(
    ([sKey, state]) => {

      index.push({

        type:
          'state',

        name:
          state.name,

        subText:
          'NER State Overview',

        center:
          state.center,

        zoom:
          state.zoom,

        stateKey:
          sKey
      });

      Object.entries(
        state.districts
      ).forEach(
        ([dKey, dist]) => {

          index.push({

            type:
              dist.isHardwareNode
                ? 'hardware'
                : 'district',

            name:
              dist.name,

            subText:
              dist.isHardwareNode
                ? `Physical ESP32 Station, ${state.name}`
                : `Live Weather Model, ${state.name}`,

            center:
              dist.center,

            zoom:
              dist.zoom,

            stateKey:
              sKey,

            districtKey:
              dKey
          });

          dist.zones.forEach(
            zone => {

              const midLat =
                zone.polygon.reduce(
                  (
                    sum,
                    p
                  ) =>
                    sum + p[0],
                  0
                ) /
                zone.polygon.length;

              const midLng =
                zone.polygon.reduce(
                  (
                    sum,
                    p
                  ) =>
                    sum + p[1],
                  0
                ) /
                zone.polygon.length;

              index.push({

                type:
                  'zone',

                name:
                  zone.name,

                subText:
                  `Slope Cut, ${dist.name}`,

                center:
                  [
                    midLat,
                    midLng
                  ],

                zoom:
                  14,

                stateKey:
                  sKey,

                districtKey:
                  dKey,

                zoneData:
                  zone
              });
            }
          );
        }
      );
    }
  );

  return index;
}

const locationIndex =
  buildLocationIndex();

function closeSearchSuggestions() {

  searchDropdown.classList.add(
    'hidden'
  );

  searchDropdown.innerHTML =
    '';
}

searchInput.addEventListener(
  'input',
  e => {

    const q =
      e.target.value
        .trim()
        .toLowerCase();

    if (!q) {

      closeSearchSuggestions();

      searchClearBtn.classList.add(
        'hidden'
      );

      return;
    }

    searchClearBtn.classList.remove(
      'hidden'
    );

    const matches =
      locationIndex
        .filter(
          item =>
            item.name
              .toLowerCase()
              .includes(q) ||
            item.subText
              .toLowerCase()
              .includes(q)
        )
        .slice(
          0,
          7
        );

    if (
      matches.length === 0
    ) {

      searchDropdown.innerHTML =
        `
          <div
            class="search-suggestion-item"
            style="
              cursor: default;
              color: #94a3b8;
            "
          >
            No matching locations found
          </div>
        `;

      searchDropdown.classList.remove(
        'hidden'
      );

      return;
    }

    searchDropdown.innerHTML =
      matches
        .map(
          (
            item,
            idx
          ) =>
            `
              <div
                class="search-suggestion-item"
                data-idx="${idx}"
              >

                <div
                  class="suggestion-info"
                >

                  <span
                    class="suggestion-title"
                  >
                    ${item.name}
                  </span>

                  <span
                    class="suggestion-sub"
                  >
                    ${item.subText}
                  </span>

                </div>

                <span
                  class="suggestion-badge ${item.type}"
                >
                  ${item.type}
                </span>

              </div>
            `
        )
        .join('');

    searchDropdown
      .querySelectorAll(
        '.search-suggestion-item'
      )
      .forEach(
        (
          el,
          i
        ) => {

          el.addEventListener(
            'click',
            () =>
              handleLocationSelect(
                matches[i]
              )
          );
        }
      );

    searchDropdown.classList.remove(
      'hidden'
    );
  }
);

function handleLocationSelect(
  loc
) {

  searchInput.value =
    loc.name;

  closeSearchSuggestions();

  if (
    loc.type === 'state'
  ) {

    stateSelect.value =
      loc.stateKey;

    populateDistricts(
      loc.stateKey
    );

    map.flyTo(
      loc.center,
      loc.zoom,
      {
        duration: 1.2
      }
    );

  } else if (
    loc.type === 'district' ||
    loc.type === 'hardware' ||
    loc.type === 'zone'
  ) {

    stateSelect.value =
      loc.stateKey;

    populateDistricts(
      loc.stateKey
    );

    districtSelect.value =
      loc.districtKey;

    updateDistrictView(
      loc.stateKey,
      loc.districtKey
    );

    if (
      loc.type === 'zone'
    ) {

      map.flyTo(
        loc.center,
        loc.zoom,
        {
          duration: 1.2
        }
      );

      updateShapPanel(
        loc.zoneData,
        loc.name
      );
    }
  }
}

searchClearBtn.addEventListener(
  'click',
  () => {

    searchInput.value =
      '';

    closeSearchSuggestions();

    searchClearBtn.classList.add(
      'hidden'
    );

    searchInput.focus();
  }
);

document.addEventListener(
  'click',
  e => {

    if (
      !e.target.closest(
        '.nav-search-container'
      )
    ) {

      closeSearchSuggestions();
    }
  }
);

map.on(
  'click dragstart',
  closeSearchSuggestions
);

// ============================================================
// LIVE SENSOR ALERT MONITOR
// ============================================================

let latestSeenAlertId = 0;
let liveAlertPollTimer = null;
let liveAlertMonitorInitialized = false;

function ensureLiveSensorAlertUI() {

  if (
    document.getElementById(
      'live-sensor-alert'
    )
  ) {
    return;
  }

  const styleId =
    'live-sensor-alert-runtime-style';

  if (
    !document.getElementById(
      styleId
    )
  ) {

    const style =
      document.createElement(
        'style'
      );

    style.id =
      styleId;

    style.textContent =
      `
        .live-sensor-alert {
          position: fixed;
          top: 82px;
          right: 24px;
          width: min(
            390px,
            calc(100vw - 32px)
          );

          display: flex;
          align-items: flex-start;

          gap: 12px;

          padding: 16px 18px;

          background: #ffffff;

          border: 2px solid #dc2626;
          border-left: 6px solid #dc2626;

          border-radius: 12px;

          box-shadow:
            0 12px 30px rgba(
              0,
              0,
              0,
              .18
            ),
            0 0 0 4px rgba(
              220,
              38,
              38,
              .08
            );

          z-index: 99999;

          animation:
            liveAlertIn
            .28s
            ease-out;
        }

        .live-sensor-alert.hidden {
          display: none;
        }

        .live-alert-icon {
          font-size: 27px;
          line-height: 1;
          margin-top: 2px;
        }

        .live-alert-content {
          flex: 1;
          min-width: 0;
        }

        .live-alert-title {
          font-size: .72rem;
          font-weight: 800;
          letter-spacing: .08em;
          color: #b91c1c;
          margin-bottom: 4px;
        }

        .live-alert-zone {
          font-size: 1rem;
          font-weight: 800;
          color: #111827;
          margin-bottom: 4px;
        }

        .live-alert-message {
          font-size: .85rem;
          line-height: 1.4;
          color: #374151;
        }

        .live-alert-reading {
          margin-top: 8px;
          font-size: .78rem;
          font-weight: 700;
          color: #991b1b;
        }

        .live-alert-time {
          margin-top: 7px;
          font-size: .72rem;
          color: #6b7280;
        }

        .live-alert-close {
          border: 0;
          background: transparent;
          color: #6b7280;
          font-size: 24px;
          line-height: 1;
          cursor: pointer;
          padding: 0 2px;
        }

        .live-alert-close:hover {
          color: #111827;
        }

        @keyframes liveAlertIn {

          from {
            opacity: 0;
            transform:
              translateY(-12px)
              translateX(12px);
          }

          to {
            opacity: 1;
            transform:
              translateY(0)
              translateX(0);
          }
        }

        @media (
          max-width: 700px
        ) {

          .live-sensor-alert {
            top: 70px;
            right: 12px;
            width:
              calc(100vw - 24px);
          }
        }
      `;

    document.head.appendChild(
      style
    );
  }

  const alertBox =
    document.createElement(
      'div'
    );

  alertBox.id =
    'live-sensor-alert';

  alertBox.className =
    'live-sensor-alert hidden';

  alertBox.innerHTML =
    `
      <div class="live-alert-icon">
        🚨
      </div>

      <div class="live-alert-content">

        <div
          class="live-alert-title"
        >
          LIVE SENSOR ALERT
        </div>

        <div
          id="live-alert-zone"
          class="live-alert-zone"
        >
          ESP32 Edge Node
        </div>

        <div
          id="live-alert-message"
          class="live-alert-message"
        >
          Reactive safety threshold exceeded.
        </div>

        <div
          id="live-alert-reading"
          class="live-alert-reading"
        ></div>

        <div
          id="live-alert-time"
          class="live-alert-time"
        >
          Detected just now
        </div>

      </div>

      <button
        id="live-alert-close"
        class="live-alert-close"
        aria-label="Close alert"
      >
        ×
      </button>
    `;

  document.body.appendChild(
    alertBox
  );

  document.getElementById(
    'live-alert-close'
  ).addEventListener(
    'click',
    () => {
      hideLiveSensorAlert();
    }
  );
}

function showLiveSensorAlert(
  alert,
  reading = null
) {

  ensureLiveSensorAlertUI();

  const alertBox =
    document.getElementById(
      'live-sensor-alert'
    );

  const zoneEl =
    document.getElementById(
      'live-alert-zone'
    );

  const messageEl =
    document.getElementById(
      'live-alert-message'
    );

  const readingEl =
    document.getElementById(
      'live-alert-reading'
    );

  const timeEl =
    document.getElementById(
      'live-alert-time'
    );

  if (
    !alertBox ||
    !zoneEl ||
    !messageEl ||
    !readingEl ||
    !timeEl
  ) {
    return;
  }

  const zoneId =
    alert.zone_id ||
    alert.sensor_id ||
    'ESP32 Edge Node';

  zoneEl.innerText =
    `${zoneId} — Reactive Safety Alert`;

  messageEl.innerText =
    alert.message ||
    'Reactive safety threshold exceeded.';

  if (reading) {

    const tilt =
      Number(
        reading.tilt_deg
      );

    const moisture =
      Number(
        reading.moisture_pct
      );

    const parts = [];

    if (
      Number.isFinite(
        tilt
      )
    ) {

      parts.push(
        `Tilt ${tilt.toFixed(1)}°`
      );
    }

    if (
      Number.isFinite(
        moisture
      )
    ) {

      parts.push(
        `Moisture ${moisture.toFixed(1)}%`
      );
    }

    readingEl.innerText =
      parts.length
        ? parts.join(
            '  •  '
          )
        : '';

    latestSensorReading =
      reading;

    // When the real ESP32 triggers an alert,
    // immediately show physical telemetry.
    if (
      zoneId ===
      'ESP32_01'
    ) {

      telemetryViewMode =
        'hardware';

      selectedBackendZoneId =
        null;

      document.getElementById(
        'data-source-tag'
      ).innerText =
        'LIVE ESP32 DEPLOYMENT';

      document.getElementById(
        'data-source-tag'
      ).classList.add(
        'hardware'
      );

      document.getElementById(
        'telemetry-card-title'
      ).innerText =
        'ESP32_01 — ESP32 Edge Telemetry';

      document.getElementById(
        'telemetry-source-desc'
      ).innerText =
        `Data Source: Physical ESP32 Sensor • Updated ${formatSensorTime(reading.timestamp)}`;

      document.getElementById(
        'hardware-badge'
      ).className =
        'badge purple';

      document.getElementById(
        'hardware-badge'
      ).innerText =
        'LIVE HARDWARE';

      document.getElementById(
        'val-tilt'
      ).innerText =
        Number.isFinite(
          tilt
        )
          ? `${tilt.toFixed(1)}°`
          : '—';

      document.getElementById(
        'val-moisture'
      ).innerText =
        Number.isFinite(
          moisture
        )
          ? `${moisture.toFixed(1)}%`
          : '—';

      document.getElementById(
        'val-rain'
      ).innerText =
        '—';
    }

  } else {

    readingEl.innerText =
      '';
  }

  timeEl.innerText =
    alert.timestamp
      ? `Detected: ${formatSensorTime(alert.timestamp)}`
      : 'Detected just now';

  alertBox.classList.remove(
    'hidden'
  );
}

function hideLiveSensorAlert() {

  const alertBox =
    document.getElementById(
      'live-sensor-alert'
    );

  if (alertBox) {

    alertBox.classList.add(
      'hidden'
    );
  }
}

async function fetchRecentAlerts() {

  const response =
    await fetch(
      `${getApiBase()}/api/alerts/recent`,
      {
        cache: 'no-store'
      }
    );

  if (!response.ok) {

    throw new Error(
      `Alerts API returned ${response.status}`
    );
  }

  const alerts =
    await response.json();

  return Array.isArray(
    alerts
  )
    ? alerts
    : [];
}

function isReactiveSensorAlert(alert) {
  const message =
    String(alert?.message || '');

  const level =
    String(alert?.risk_level || '')
      .toLowerCase();

  const zoneId =
    String(alert?.zone_id || '');

  const isHardwareAlert =
    /abnormal sensor threshold detected/i.test(message) ||
    /reactive alert/i.test(message);

  return (
    zoneId === 'ESP32_01' &&
    level === 'critical' &&
    isHardwareAlert
  );
}
async function pollLiveSensorAlerts() {

  try {

    const alerts =
      await fetchRecentAlerts();

    const sensorAlerts =
      alerts.filter(
        isReactiveSensorAlert
      );

    // No alerts yet.
    // Still mark monitor as initialized so
    // the first new ESP32 alert is shown.
    if (
      sensorAlerts.length === 0
    ) {

      liveAlertMonitorInitialized =
        true;

      return;
    }

    const latestAlert =
      sensorAlerts[0];

    const alertId =
      Number(
        latestAlert.alert_id || 0
      );

    // On first poll with existing alerts,
    // establish a baseline so old alerts aren't
    // presented as live.
    if (
      !liveAlertMonitorInitialized
    ) {

      latestSeenAlertId =
        alertId;

      liveAlertMonitorInitialized =
        true;

      return;
    }

    if (
      alertId > 0 &&
      alertId <=
        latestSeenAlertId
    ) {

      return;
    }

    if (
      alertId > 0
    ) {

      latestSeenAlertId =
        alertId;
    }

    let reading =
      null;

    const zoneId =
      latestAlert.zone_id;

    if (zoneId) {

      try {

        const sensorResponse =
          await fetch(
            `${getApiBase()}/api/sensor-data/latest/${encodeURIComponent(zoneId)}`,
            {
              cache: 'no-store'
            }
          );

        if (
          sensorResponse.ok
        ) {

          const sensorData =
            await sensorResponse.json();

          if (
            sensorData.status ===
              'ok' &&
            sensorData.reading
          ) {

            reading =
              sensorData.reading;
          }
        }

      } catch (sensorError) {

        console.warn(
          '[Live Alert] Sensor reading unavailable:',
          sensorError
        );
      }
    }

    showLiveSensorAlert(
      latestAlert,
      reading
    );

    console.log(
      '[LIVE SENSOR ALERT]',
      latestAlert,
      reading
    );

  } catch (error) {

    console.warn(
      '[Live Alert] Alert polling failed:',
      error
    );
  }
}

function startLiveSensorAlertMonitoring() {

  ensureLiveSensorAlertUI();

  pollLiveSensorAlerts();

  liveAlertPollTimer =
    setInterval(
      pollLiveSensorAlerts,
      3000
    );
}

// 16. Boot System & Fetch Live Feeds

initChart();

renderAllNEROverview();

loadBackendRiskZones();

syncAllRegionalLiveFeeds();

// Load the correct telemetry source for the current view.
refreshTelemetry();

// Start live sensor alert monitoring.
startLiveSensorAlertMonitoring();

// A selected ML zone keeps showing that zone's own sensor data.
setInterval(
  () => {
    refreshTelemetry();
  },
  3000
);

setTimeout(
  () => {
    map.invalidateSize();
  },
  200
);

window.addEventListener(
  'resize',
  () => {
    map.invalidateSize();
  }
);
