(() => {
    "use strict";

    const FLAG = "__giriRakshak1kmCellClick";

    const RISK_STYLE = {
        "Low Risk": {
            color: "#16a34a",
            fill: "#22c55e"
        },
        "Moderate Risk": {
            color: "#eab308",
            fill: "#facc15"
        },
        "High Risk": {
            color: "#f97316",
            fill: "#fb923c"
        },
        "Very High Risk": {
            color: "#dc2626",
            fill: "#ef4444"
        }
    };

    function findSusceptibilityLayer(map) {
        if (!map || !map._layers) return null;

        for (const layer of Object.values(map._layers)) {
            const url = layer && layer._url;

            if (
                typeof url === "string" &&
                url.includes("/api/susceptibility/tiles/")
            ) {
                return layer;
            }
        }

        return null;
    }

    function getModelFromLayer(layer) {
        if (!layer || typeof layer._url !== "string") {
            return null;
        }

        const match = layer._url.match(
            /\/api\/susceptibility\/tiles\/(spatial|hybrid)\//
        );

        return match ? match[1] : null;
    }

    function getApiOrigin(layer) {
        if (!layer || typeof layer._url !== "string") {
            return null;
        }

        try {
            return new URL(
                layer._url,
                window.location.href
            ).origin;
        } catch {
            return null;
        }
    }

    function escapeHtml(value) {
        return String(value)
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }

    function riskStyle(level) {
        return (
            RISK_STYLE[level] ||
            {
                color: "#334155",
                fill: "#94a3b8"
            }
        );
    }

    function riskBadge(level) {
        const style = riskStyle(level);

        return `
            <span style="
                display:inline-block;
                margin-top:7px;
                padding:5px 9px;
                border-radius:999px;
                background:${style.fill};
                color:#111827;
                font-size:12px;
                font-weight:900;
            ">
                ${escapeHtml(level || "No Data")}
            </span>
        `;
    }

    function inspectCell(map, event) {
        const layer = findSusceptibilityLayer(map);

        if (!layer) {
            return;
        }

        const model = getModelFromLayer(layer);
        const apiOrigin = getApiOrigin(layer);

        if (!model || !apiOrigin) {
            return;
        }

        const lat = event.latlng.lat;
        const lon = event.latlng.lng;

        const url =
            `${apiOrigin}/api/susceptibility/point` +
            `?model=${encodeURIComponent(model)}` +
            `&lat=${encodeURIComponent(lat)}` +
            `&lon=${encodeURIComponent(lon)}` +
            `&_=${Date.now()}`;

        fetch(
            url,
            {
                cache: "no-store"
            }
        )
            .then(async response => {
                if (!response.ok) {
                    let detail = `HTTP ${response.status}`;

                    try {
                        const body = await response.json();
                        if (body.detail) {
                            detail = body.detail;
                        }
                    } catch {}

                    throw new Error(detail);
                }

                return response.json();
            })
            .then(data => {

                if (!data.cell_bounds) {
                    throw new Error("Cell bounds missing");
                }

                // ------------------------------------------------
                // Remove previous selected cell
                // ------------------------------------------------
                if (map.__giriRakshakSelectedCell) {
                    map.removeLayer(
                        map.__giriRakshakSelectedCell
                    );
                }

                const level =
                    data.risk_level || "No Data";

                const style = riskStyle(level);

                const b = data.cell_bounds;

                map.__giriRakshakSelectedCell =
                    L.rectangle(
                        [
                            [b.south, b.west],
                            [b.north, b.east]
                        ],
                        {
                            color: style.color,
                            weight: 3,
                            opacity: 1,
                            fillColor: style.fill,
                            fillOpacity: 0.18,
                            interactive: false
                        }
                    ).addTo(map);

                // ------------------------------------------------
                // Sidebar sync, when those elements exist
                // ------------------------------------------------
                const scoreEl =
                    document.getElementById("sus-score");

                const pctEl =
                    document.getElementById("sus-percentile");

                const spatialEl =
                    document.getElementById("sus-spatial");

                const hybridEl =
                    document.getElementById("sus-hybrid");

                const locationEl =
                    document.getElementById("sus-location");

                const messageEl =
                    document.getElementById(
                        "sus-selection-message"
                    );

                if (scoreEl && data.score != null) {
                    scoreEl.innerText =
                        Number(data.score).toFixed(3);
                }

                if (pctEl && data.percentile != null) {
                    pctEl.innerText =
                        `${Number(data.percentile).toFixed(1)} percentile`;
                }

                if (spatialEl) {
                    spatialEl.innerText =
                        data.spatial_score != null
                            ? Number(data.spatial_score).toFixed(3)
                            : "—";
                }

                if (hybridEl) {
                    hybridEl.innerText =
                        data.hybrid_score != null
                            ? Number(data.hybrid_score).toFixed(3)
                            : "—";
                }

                if (locationEl && data.cell_center) {
                    locationEl.innerText =
                        `Location: ` +
                        `${Number(data.cell_center.lat).toFixed(5)}, ` +
                        `${Number(data.cell_center.lon).toFixed(5)}`;
                }

                if (messageEl) {
                    messageEl.innerText =
                        `${data.model_label || model} • ${level}`;
                }

                // ------------------------------------------------
                // Popup
                // ------------------------------------------------
                const snappedHtml =
                    data.snapped
                        ? `
                            <div style="
                                margin-top:8px;
                                padding:7px 9px;
                                border-radius:8px;
                                background:#f8fafc;
                                color:#64748b;
                                font-size:11px;
                                line-height:1.4;
                            ">
                                Nearest valid 1-km cell selected<br>
                                Snap distance:
                                ${Number(data.snap_distance_m).toFixed(0)} m
                            </div>
                        `
                        : "";

                const popupHtml = `
                    <div style="
                        min-width:270px;
                        font-family:Arial,sans-serif;
                    ">

                        <div style="
                            font-size:12px;
                            font-weight:900;
                            letter-spacing:.04em;
                            color:#334155;
                        ">
                            1 KM × 1 KM SUSCEPTIBILITY CELL
                        </div>

                        ${riskBadge(level)}

                        <div style="
                            margin-top:9px;
                            font-size:26px;
                            font-weight:900;
                            color:#0f172a;
                        ">
                            ${data.score != null
                                ? Number(data.score).toFixed(3)
                                : "—"}
                        </div>

                        <div style="
                            font-size:11px;
                            color:#64748b;
                        ">
                            Active ${escapeHtml(
                                model.toUpperCase()
                            )} model score
                        </div>

                        <div style="
                            margin-top:10px;
                            padding-top:9px;
                            border-top:1px solid #e2e8f0;
                            font-size:12px;
                            line-height:1.75;
                        ">
                            <b>Spatial:</b>
                            ${data.spatial_score != null
                                ? Number(data.spatial_score).toFixed(3)
                                : "—"}
                            <br>

                            <b>Spatial risk:</b>
                            ${escapeHtml(
                                data.spatial_risk_level || "—"
                            )}
                            <br>

                            <b>Hybrid:</b>
                            ${data.hybrid_score != null
                                ? Number(data.hybrid_score).toFixed(3)
                                : "—"}
                            <br>

                            <b>Hybrid risk:</b>
                            ${escapeHtml(
                                data.hybrid_risk_level || "—"
                            )}
                            <br>

                            <b>Cell:</b>
                            ${data.row} × ${data.col}
                            <br>

                            <b>Size:</b>
                            ~1 km × 1 km
                        </div>

                        <div style="
                            margin-top:7px;
                            font-size:11px;
                            color:#64748b;
                        ">
                            Center:
                            ${Number(
                                data.cell_center.lat
                            ).toFixed(5)},
                            ${Number(
                                data.cell_center.lon
                            ).toFixed(5)}
                        </div>

                        ${snappedHtml}

                    </div>
                `;

                L.popup({
                    maxWidth: 330,
                    closeButton: true
                })
                    .setLatLng(
                        [
                            data.cell_center.lat,
                            data.cell_center.lon
                        ]
                    )
                    .setContent(popupHtml)
                    .openOn(map);
            })
            .catch(error => {
                console.error(
                    "1-km susceptibility cell:",
                    error
                );

                L.popup()
                    .setLatLng(
                        [
                            event.latlng.lat,
                            event.latlng.lng
                        ]
                    )
                    .setContent(
                        `<b>Could not read this cell.</b><br>
                         ${escapeHtml(error.message)}`
                    )
                    .openOn(map);
            });
    }

    function install(map) {
        if (!map || map[FLAG]) {
            return;
        }

        map[FLAG] = true;

        map.on(
            "click",
            event => {
                inspectCell(map, event);
            }
        );
    }

    function boot() {
        if (!window.L || !L.Map) {
            setTimeout(boot, 100);
            return;
        }

        if (
            typeof L.Map.addInitHook ===
            "function"
        ) {
            L.Map.addInitHook(function () {
                install(this);
            });
        }
    }

    boot();

})();
