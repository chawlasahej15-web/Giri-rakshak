from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd


ROOT = Path.home() / "Personal" / "Giri-rakshak"

GPKG = (
    Path.home()
    / "Downloads"
    / "India_dataset.gpkg"
)

LAYER = "SUcovariate3857lr_final"

OUTPUT = (
    ROOT
    / "ml"
    / "data"
    / "demo"
    / "zone_features.csv"
)


STATIC_FEATURES = [
    "Slope_mean",
    "Slope_std",
    "VCv_mean",
    "VCv_std",
    "HCv_mean",
    "HCv_std",
    "Rlf_mean",
    "Rlf_std",
    "RnSum_mean",
    "RnSum_std",
    "NDVI_mean",
    "NDVI_std",
    "Elev_mean",
    "Elev_std",
    "Asp_mean",
    "Asp_std",
    "pga_mean",
    "lcover_11",
    "lcover_14",
    "lcover_20",
    "lcover_30",
    "lcover_40",
    "lcover_50",
    "lcover_60",
    "lcover_70",
    "lcover_100",
    "lcover_110",
    "lcover_120",
    "lcover_130",
    "lcover_140",
    "lcover_190",
    "lcover_200",
    "lcover_210",
    "log_area",
    "log_perimeter",
    "compactness",
]


ZONE_ID = "AIZAWL-001"
LAT = 23.7271
LON = 92.7176


print("\n" + "=" * 70)
print("CREATING DEMO ZONE STATIC FEATURES")
print("=" * 70)

print("\nLoading GPKG...")

gdf = gpd.read_file(
    GPKG,
    layer=LAYER
)

print(
    f"GPKG rows: {len(gdf)}"
)

# ------------------------------------------------------------
# Derived static features
# ------------------------------------------------------------

gdf["log_area"] = np.log1p(
    gdf["area"]
)

gdf["log_perimeter"] = np.log1p(
    gdf["perimeter"]
)

gdf["compactness"] = (
    4
    * np.pi
    * gdf["area"]
    / (
        gdf["perimeter"] ** 2
    )
)


# ------------------------------------------------------------
# Create demo point
# ------------------------------------------------------------

point = gpd.GeoDataFrame(
    {
        "zone_id": [ZONE_ID],
        "lat": [LAT],
        "lon": [LON],
    },
    geometry=gpd.points_from_xy(
        [LON],
        [LAT]
    ),
    crs="EPSG:4326"
).to_crs(gdf.crs)


# ------------------------------------------------------------
# Find containing polygon
# ------------------------------------------------------------

print(
    f"\nFinding polygon for "
    f"{ZONE_ID}..."
)

lookup_cols = [
    "su",
    *STATIC_FEATURES,
    "geometry",
]

lookup = gdf[
    lookup_cols
].copy()

joined = gpd.sjoin(
    point,
    lookup,
    predicate="within",
    how="left"
)


# ------------------------------------------------------------
# Fallback: nearest polygon
# ------------------------------------------------------------

if joined["su"].isna().all():

    print(
        "Point is not inside a polygon."
    )

    print(
        "Using nearest polygon..."
    )

    nearest = gpd.sjoin_nearest(
        point,
        lookup,
        how="left",
        distance_col="distance_m"
    )

    joined = nearest

    distance = float(
        joined["distance_m"].iloc[0]
    )

    print(
        f"Nearest polygon distance: "
        f"{distance:.3f} m"
    )

else:

    joined["distance_m"] = 0.0

    print(
        "Point lies inside a GPKG polygon."
    )


# ------------------------------------------------------------
# Check match
# ------------------------------------------------------------

if joined["su"].isna().any():

    raise ValueError(
        "Could not identify a GPKG polygon "
        "for AIZAWL-001."
    )


# ------------------------------------------------------------
# Build output
# ------------------------------------------------------------

result = joined[
    [
        "zone_id",
        "lat",
        "lon",
        "su",
        *STATIC_FEATURES,
    ]
].copy()


# ------------------------------------------------------------
# Validate
# ------------------------------------------------------------

if len(result) != 1:

    raise ValueError(
        f"Expected exactly 1 demo row, "
        f"got {len(result)}."
    )


missing = (
    result[STATIC_FEATURES]
    .isna()
    .sum()
    .sum()
)

if missing > 0:

    raise ValueError(
        f"Static feature missing values: "
        f"{missing}"
    )


if not np.isfinite(
    result[STATIC_FEATURES]
    .to_numpy()
).all():

    raise ValueError(
        "Non-finite static feature value found."
    )


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

result.to_csv(
    OUTPUT,
    index=False
)


# ------------------------------------------------------------
# Summary
# ------------------------------------------------------------

print("\n" + "-" * 70)
print("DEMO ZONE")
print("-" * 70)

print(
    result[
        [
            "zone_id",
            "lat",
            "lon",
            "su",
        ]
    ].to_string(index=False)
)

print(
    f"\nStatic features: "
    f"{len(STATIC_FEATURES)}"
)

print(
    f"Missing values: "
    f"{missing}"
)

print("\nSaved:")
print(OUTPUT)

print("\n" + "=" * 70)
print("DEMO ZONE LOOKUP READY")
print("=" * 70)
