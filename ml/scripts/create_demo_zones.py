from pathlib import Path

import geopandas as gpd
import pandas as pd
import xgboost as xgb


ROOT = Path(__file__).resolve().parents[2]

GPKG = (
    Path.home()
    / "Downloads"
    / "India_dataset.gpkg"
)

LAYER = "SUcovariate3857lr_final"

ZONE_FEATURES = (
    ROOT
    / "ml"
    / "data"
    / "zone_features.csv"
)

OUTPUT = (
    ROOT
    / "ml"
    / "data"
    / "demo"
    / "demo_zones.csv"
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


print("\n" + "=" * 70)
print("CREATING 12 DEMO ZONES")
print("=" * 70)


# ============================================================
# LOAD STATIC LOOKUP
# ============================================================

print("\nLoading 122K static lookup...")

lookup = pd.read_csv(
    ZONE_FEATURES
)

lookup["su"] = (
    pd.to_numeric(
        lookup["su"],
        errors="raise"
    )
    .astype(int)
)

print(
    f"Lookup SUs: {lookup['su'].nunique()}"
)


# ============================================================
# LOAD GPKG
# ============================================================

print("\nLoading GPKG...")

gdf = gpd.read_file(
    GPKG,
    layer=LAYER
)

print(
    f"GPKG rows: {len(gdf)}"
)


# ============================================================
# ONLY SUs WITH EXACTLY ONE GEOMETRY
# ============================================================

geometry_counts = (
    gdf.groupby("su")
    .size()
)

safe_sus = set(
    geometry_counts[
        geometry_counts == 1
    ].index
)

candidates = (
    lookup[
        lookup["su"].isin(
            safe_sus
        )
    ]
    .drop_duplicates("su")
    .copy()
)

print(
    "Safe candidate SUs:",
    len(candidates)
)


# ============================================================
# LOAD STATIC XGBOOST
# ============================================================

print("\nLoading static XGBoost...")

model = xgb.XGBClassifier()

model.load_model(
    str(
        ROOT
        / "ml"
        / "models"
        / "static_xgb.json"
    )
)


candidates["p_static"] = (
    model.predict_proba(
        candidates[
            STATIC_FEATURES
        ]
    )[:, 1]
)


# ============================================================
# SELECT 12 ZONES WITH VARIED STATIC RISK
# ============================================================

# Desired static probability spread.
target_scores = [
    0.05,
    0.12,
    0.20,
    0.28,
    0.36,
    0.44,
    0.52,
    0.62,
    0.72,
    0.82,
    0.90,
    0.96,
]


selected = []

remaining = candidates.copy()


for target in target_scores:

    if remaining.empty:
        break

    idx = (
        (
            remaining["p_static"]
            - target
        )
        .abs()
        .idxmin()
    )

    selected.append(
        remaining.loc[idx]
    )

    remaining = remaining.drop(
        idx
    )


selected = pd.DataFrame(
    selected
)


if len(selected) != 12:

    raise ValueError(
        f"Could only select "
        f"{len(selected)} demo zones."
    )


# ============================================================
# GET ACTUAL GPKG GEOMETRIES
# ============================================================

selected_sus = set(
    selected["su"].astype(int)
)

selected_gdf = gdf[
    gdf["su"].isin(
        selected_sus
    )
].copy()


if len(selected_gdf) != 12:

    raise ValueError(
        "Selected SUs did not map "
        "to exactly 12 unique geometries."
    )


# GPKG is in projected CRS.
# Centroids are therefore calculated here safely.
selected_gdf["centroid"] = (
    selected_gdf
    .geometry
    .centroid
)


centroids = (
    gpd.GeoSeries(
        selected_gdf["centroid"],
        crs=selected_gdf.crs
    )
    .to_crs("EPSG:4326")
)


centroid_map = {
    int(su): point
    for su, point in zip(
        selected_gdf["su"],
        centroids
    )
}


# ============================================================
# BUILD EXACTLY DEMO_ZONE_01 ... DEMO_ZONE_12
# ============================================================

rows = []

selected = (
    selected
    .sort_values("p_static")
    .reset_index(drop=True)
)


for i, row in selected.iterrows():

    su = int(row["su"])

    point = centroid_map[su]

    rows.append({
        "zone_id":
            f"DEMO_ZONE_{i + 1:02d}",

        "su":
            su,

        "lat":
            float(point.y),

        "lon":
            float(point.x),

        "p_static_reference":
            float(row["p_static"]),
    })


result = pd.DataFrame(
    rows
)


# ============================================================
# VALIDATION
# ============================================================

if len(result) != 12:
    raise ValueError(
        "Expected exactly 12 zones."
    )

expected_ids = [
    f"DEMO_ZONE_{i:02d}"
    for i in range(1, 13)
]

if result["zone_id"].tolist() != expected_ids:

    raise ValueError(
        "Demo zone IDs are not "
        "DEMO_ZONE_01 ... DEMO_ZONE_12."
    )

if result["zone_id"].duplicated().any():
    raise ValueError(
        "Duplicate zone IDs."
    )

if result["su"].duplicated().any():
    raise ValueError(
        "Duplicate demo SUs."
    )

if result[
    ["lat", "lon"]
].duplicated().any():

    raise ValueError(
        "Duplicate demo coordinates."
    )


# ============================================================
# SAVE
# ============================================================

OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

result.to_csv(
    OUTPUT,
    index=False
)


print("\n" + "-" * 70)
print("12 DEMO ZONES")
print("-" * 70)

print(
    result.to_string(
        index=False
    )
)

print("\nSaved:")
print(OUTPUT)

print("\n" + "=" * 70)
print("12 DEMO ZONES READY")
print("=" * 70)
