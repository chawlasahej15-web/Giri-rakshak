from rasterio.windows import Window
from pyproj import Transformer
import math
from pathlib import Path
import struct
import zlib
from typing import Literal

import numpy as np
import rasterio
from rasterio.warp import transform_bounds
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from rio_tiler.io import Reader
from rio_tiler.errors import TileOutsideBounds


router = APIRouter(
    prefix="/api/susceptibility",
    tags=["Susceptibility"],
)

BASE_DIR = Path(__file__).resolve().parents[1]

REGION_DIR = (
    BASE_DIR
    / "data"
    / "susceptibility"
    / "india_full"
)


MODELS = {
    "spatial": {
        "score": REGION_DIR / "spatial_score.tif",
        "percentile": REGION_DIR / "spatial_percentile.tif",
        "visual": REGION_DIR / "spatial_visual_3857.tif",
        "label": "Spatial-matched",
    },
    "hybrid": {
        "score": REGION_DIR / "hybrid_score.tif",
        "percentile": REGION_DIR / "hybrid_percentile.tif",
        "visual": REGION_DIR / "hybrid_visual_3857.tif",
        "label": "Hybrid",
    },
}


def make_colormap():
    # Final susceptibility palette:
    # Light Green -> Dark Green -> Green -> Yellow -> Orange -> Red
    # No dark-red/brown tones.
    # Red is restricted to the extreme upper tail.
    def px(score):
        return round(score * 255 / 100)

    stops = [
        (px(0),    (155, 225, 155, 60)),   # light green
        (px(45),   (65, 150, 75, 80)),     # dark green
        (px(70),   (60, 180, 80, 100)),    # green
        (px(85),   (190, 210, 75, 115)),   # green-yellow
        (px(92),   (245, 220, 60, 135)),   # yellow
        (px(96),   (245, 165, 45, 160)),   # orange
        (px(98.5), (245, 115, 55, 180)),   # strong orange-red
        (px(99.5), (230, 55, 50, 200)),    # red
        (px(100),  (205, 35, 40, 215)),    # maximum = red, NOT dark red
    ]

    cmap = {}

    for p in range(256):
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]

            if p <= p1:
                t = (
                    (p - p0) / (p1 - p0)
                    if p1 != p0
                    else 0.0
                )

                cmap[p] = tuple(
                    int(round(
                        c0[k] + t * (c1[k] - c0[k])
                    ))
                    for k in range(4)
                )
                break

    return cmap


COLORMAP = make_colormap()


def get_model(model: str):

    if model not in MODELS:
        raise HTTPException(
            status_code=404,
            detail="Use model=spatial or model=hybrid."
        )

    cfg = MODELS[model]

    if not cfg["score"].exists():
        raise HTTPException(
            status_code=503,
            detail="Susceptibility data unavailable."
        )

    if not cfg["visual"].exists():
        raise HTTPException(
            status_code=503,
            detail="Visualization raster unavailable."
        )

    return cfg


@router.get("/regions")
def regions():
    return {
        "regions": [
            {
                "id": "india_full",
                "name": "India",
                "status": "ready",
            }
        ]
    }


@router.get("/meta/{model}")
def metadata(
    model: Literal["spatial", "hybrid"]
):
    cfg = get_model(model)

    with rasterio.open(cfg["score"]) as src:
        bounds = transform_bounds(
            src.crs,
            "EPSG:4326",
            *src.bounds,
            densify_pts=21,
        )

        return {
            "region": "india_full",
            "model": model,
            "model_label": cfg["label"],
            "crs": "EPSG:4326",
            "bounds": {
                "west": bounds[0],
                "south": bounds[1],
                "east": bounds[2],
                "north": bounds[3],
            },
            "width": src.width,
            "height": src.height,
            "resolution": "1 km",
            "score_definition": (
                "Static susceptibility model score; "
                "not a calibrated real-world probability."
            ),
            "visualization": (
                "Continuous smoothed surface. "
                "Color intensity represents relative "
                "percentile within this pilot."
            ),
        }



def transparent_png_256():
    """Return a 256x256 fully transparent PNG without extra dependencies."""

    width = 256
    height = 256

    raw = b"".join(
        b"\x00" + (b"\x00\x00\x00\x00" * width)
        for _ in range(height)
    )

    def chunk(kind, data):
        return (
            struct.pack(
                ">I",
                len(data)
            )
            + kind
            + data
            + struct.pack(
                ">I",
                zlib.crc32(
                    kind + data
                ) & 0xffffffff
            )
        )

    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(
            b"IHDR",
            struct.pack(
                ">IIBBBBB",
                width,
                height,
                8,
                6,
                0,
                0,
                0,
            ),
        )
        + chunk(
            b"IDAT",
            zlib.compress(
                raw,
                level=6
            ),
        )
        + chunk(
            b"IEND",
            b"",
        )
    )

    return png


@router.get(
    "/tiles/{model}/{z}/{x}/{y}.png"
)
def tile(
    model: Literal["spatial", "hybrid"],
    z: int,
    x: int,
    y: int,
):
    cfg = get_model(model)

    try:

        with Reader(str(cfg["visual"])) as src:

            img = src.tile(
                x,
                y,
                z,
                tilesize=256,
                indexes=1,
                resampling_method="nearest",
            )

            img.rescale(
                in_range=((0, 100),),
                out_range=((0, 255),),
                out_dtype="uint8",
            )

            body = img.render(
                img_format="PNG",
                colormap=COLORMAP,
            )

        return Response(
            content=body,
            media_type="image/png",
            headers={
                "Cache-Control":
                    "no-store, no-cache, must-revalidate, max-age=0"
            },
        )

    except TileOutsideBounds:

        # Leaflet can legitimately request tiles around the
        # edge of the susceptibility raster. Those tiles should
        # be transparent, not HTTP 500 errors.
        return Response(
            content=transparent_png_256(),
            media_type="image/png",
            headers={
                "Cache-Control":
                    "no-store, no-cache, must-revalidate, max-age=0"
            },
        )

    except Exception as exc:

        print(
            "[Susceptibility tile error]",
            repr(exc)
        )

        raise HTTPException(
            status_code=500,
            detail=f"Tile rendering failed: {exc}"
        )


@router.get("/point")
def point(
    model: str = "spatial",
    lat: float = 0.0,
    lon: float = 0.0,
):
    """
    Return the nearest valid 1-km susceptibility cell.

    IMPORTANT:
    - Uses the RAW model score raster, not the smoothed visual raster.
    - Snaps to the nearest valid cell within 10 pixels (~10 km).
    - Returns Spatial + Hybrid score/category for the same cell.
    """

    if model not in MODELS:
        raise HTTPException(
            status_code=404,
            detail="Use model=spatial or model=hybrid."
        )

    # Dataset-specific local-excess P90 values obtained from
    # the current susceptibility dataset.
    LOCAL_EXCESS_P90 = {
        "spatial": 0.01144802,
        "hybrid": 0.00680435,
    }

    def is_valid(value, nodata):
        if not np.isfinite(value):
            return False

        if nodata is not None and np.isclose(value, nodata):
            return False

        return True

    def nearest_valid(src, click_lon, click_lat, max_radius=10):
        transformer = Transformer.from_crs(
            "EPSG:4326",
            src.crs,
            always_xy=True,
        )

        x, y = transformer.transform(
            click_lon,
            click_lat,
        )

        row, col = src.index(x, y)

        best = None

        for radius in range(max_radius + 1):

            r0 = max(0, row - radius)
            r1 = min(src.height, row + radius + 1)

            c0 = max(0, col - radius)
            c1 = min(src.width, col + radius + 1)

            if r1 <= r0 or c1 <= c0:
                continue

            window = Window(
                c0,
                r0,
                c1 - c0,
                r1 - r0,
            )

            data = src.read(
                1,
                window=window,
                masked=False,
            ).astype(np.float32)

            nodata = src.nodata

            for rr in range(data.shape[0]):
                for cc in range(data.shape[1]):

                    absolute_row = r0 + rr
                    absolute_col = c0 + cc

                    dr = absolute_row - row
                    dc = absolute_col - col

                    distance_sq = dr * dr + dc * dc

                    if distance_sq > radius * radius:
                        continue

                    value = float(data[rr, cc])

                    if not is_valid(value, nodata):
                        continue

                    candidate = {
                        "row": absolute_row,
                        "col": absolute_col,
                        "score": value,
                        "distance_pixels": math.sqrt(distance_sq),
                    }

                    if (
                        best is None
                        or candidate["distance_pixels"]
                        < best["distance_pixels"]
                    ):
                        best = candidate

            if best is not None:
                return best

        return None

    def read_value(src, row, col):
        arr = src.read(
            1,
            window=Window(col, row, 1, 1),
            masked=False,
        )

        if arr.size == 0:
            return None

        value = float(arr[0, 0])

        if not is_valid(value, src.nodata):
            return None

        return value

    def local_median(src, row, col, radius=2):
        r0 = max(0, row - radius)
        r1 = min(src.height, row + radius + 1)

        c0 = max(0, col - radius)
        c1 = min(src.width, col + radius + 1)

        window = Window(
            c0,
            r0,
            c1 - c0,
            r1 - r0,
        )

        arr = src.read(
            1,
            window=window,
            masked=False,
        ).astype(np.float32)

        nodata = src.nodata

        if nodata is not None:
            arr[np.isclose(arr, nodata)] = np.nan

        arr[~np.isfinite(arr)] = np.nan

        values = arr[np.isfinite(arr)]

        if values.size == 0:
            return None

        return float(np.median(values))

    def risk_category(name, score, percentile, src, row, col):
        if score is None:
            return "No Data"

        if percentile is None:
            # Fallback if percentile raster is unavailable.
            if score >= 0.99:
                return "Very High Risk"
            if score >= 0.95:
                return "High Risk"
            if score >= 0.90:
                return "Moderate Risk"
            return "Low Risk"

        # Regional percentile bands:
        #
        # < P90      -> Low
        # P90-P95    -> Moderate
        # P95-P99    -> High
        # >= P99 + locally elevated -> Very High
        #
        # The local-excess condition prevents broad high-score
        # plateaus from turning the entire mountain belt Very High.

        if percentile >= 99.0:
            med = local_median(src, row, col, radius=2)

            if med is not None:
                excess = score - med

                if excess >= LOCAL_EXCESS_P90[name]:
                    return "Very High Risk"

            return "High Risk"

        if percentile >= 95.0:
            return "High Risk"

        if percentile >= 90.0:
            return "Moderate Risk"

        return "Low Risk"

    # ------------------------------------------------------------
    # Find the nearest valid cell using the ACTIVE model
    # ------------------------------------------------------------
    active_cfg = get_model(model)

    with rasterio.open(str(active_cfg["score"])) as active_src:

        result = nearest_valid(
            active_src,
            lon,
            lat,
            max_radius=10,
        )

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="No valid susceptibility cell found within 10 km.",
            )

        row = int(result["row"])
        col = int(result["col"])
        distance_pixels = float(result["distance_pixels"])

        # --------------------------------------------------------
        # Cell bounds from the RAW 1-km raster
        # --------------------------------------------------------
        window = Window(
            col,
            row,
            1,
            1,
        )

        left, bottom, right, top = active_src.window_bounds(window)

        left = float(left)
        bottom = float(bottom)
        right = float(right)
        top = float(top)

        to_wgs84 = Transformer.from_crs(
            active_src.crs,
            "EPSG:4326",
            always_xy=True,
        )

        west, north = to_wgs84.transform(left, top)
        east, south = to_wgs84.transform(right, bottom)

        center_x = (left + right) / 2.0
        center_y = (bottom + top) / 2.0

        center_lon, center_lat = to_wgs84.transform(
            center_x,
            center_y,
        )

        center_lon = float(center_lon)
        center_lat = float(center_lat)

        # --------------------------------------------------------
        # Approximate snap distance in metres
        # --------------------------------------------------------
        lat1 = math.radians(float(lat))
        lat2 = math.radians(center_lat)

        dlat = math.radians(center_lat - float(lat))
        dlon = math.radians(center_lon - float(lon))

        a = (
            math.sin(dlat / 2.0) ** 2
            + math.cos(lat1)
            * math.cos(lat2)
            * math.sin(dlon / 2.0) ** 2
        )

        earth_radius_m = 6371000.0

        snap_distance_m = (
            2.0
            * earth_radius_m
            * math.asin(
                min(1.0, math.sqrt(a))
            )
        )

    # ------------------------------------------------------------
    # Read BOTH model values for this same 1-km cell
    # ------------------------------------------------------------
    model_data = {}

    for name in ("spatial", "hybrid"):

        cfg = get_model(name)

        with rasterio.open(str(cfg["score"])) as score_src:

            score = read_value(
                score_src,
                row,
                col,
            )

            model_data[name] = {
                "score": score,
                "local_median": local_median(
                    score_src,
                    row,
                    col,
                    radius=2,
                ),
            }

        with rasterio.open(str(cfg["percentile"])) as pct_src:

            percentile = read_value(
                pct_src,
                row,
                col,
            )

            if percentile is not None and percentile <= 1.0:
                percentile *= 100.0

            model_data[name]["percentile"] = percentile

        with rasterio.open(str(cfg["score"])) as score_src:

            model_data[name]["risk_level"] = risk_category(
                name,
                model_data[name]["score"],
                model_data[name]["percentile"],
                score_src,
                row,
                col,
            )

    active = model_data[model]

    return {
        "model": model,
        "model_label": active_cfg["label"],

        # Active model
        "score": active["score"],
        "percentile": active["percentile"],
        "risk_level": active["risk_level"],

        # Both models
        "spatial_score": model_data["spatial"]["score"],
        "spatial_percentile": model_data["spatial"]["percentile"],
        "spatial_risk_level": model_data["spatial"]["risk_level"],

        "hybrid_score": model_data["hybrid"]["score"],
        "hybrid_percentile": model_data["hybrid"]["percentile"],
        "hybrid_risk_level": model_data["hybrid"]["risk_level"],

        # Selected cell
        "row": row,
        "col": col,

        "cell_size_m": round(
            max(
                abs(float(right - left)),
                abs(float(top - bottom)),
            ),
            2,
        ),

        "cell_bounds": {
            "west": float(west),
            "south": float(south),
            "east": float(east),
            "north": float(north),
        },

        "cell_center": {
            "lat": center_lat,
            "lon": center_lon,
        },

        "snapped": bool(distance_pixels > 0),
        "snap_distance_m": round(float(snap_distance_m), 2),
    }

