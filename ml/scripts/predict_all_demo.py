from pathlib import Path
import sys
import json

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(
    0,
    str(ROOT / "ml" / "src")
)

from predict import predict_risk


ZONES_FILE = (
    ROOT
    / "ml"
    / "data"
    / "demo"
    / "demo_zones.csv"
)

RAINFALL_FILE = (
    ROOT
    / "ml"
    / "data"
    / "demo"
    / "demo_rainfall.csv"
)


print("\n" + "=" * 80)
print("GIRIRAKSHAK — 12 ZONE DEMO PREDICTIONS")
print("=" * 80)


# ------------------------------------------------------------
# Load zones
# ------------------------------------------------------------

zones = pd.read_csv(
    ZONES_FILE
)

if len(zones) != 12:

    raise ValueError(
        f"Expected 12 demo zones, found {len(zones)}"
    )


# ------------------------------------------------------------
# Load rainfall scenarios
# ------------------------------------------------------------

if not RAINFALL_FILE.exists():

    raise FileNotFoundError(
        "demo_rainfall.csv not found.\n"
        "Run:\n"
        "python ml/scripts/create_demo_rainfall.py"
    )


rainfall = pd.read_csv(
    RAINFALL_FILE
).set_index(
    "zone_id"
)


# ------------------------------------------------------------
# Predict all 12
# ------------------------------------------------------------

results = []


for _, zone in zones.iterrows():

    zone_id = zone["zone_id"]

    if zone_id not in rainfall.index:

        raise ValueError(
            f"No rainfall scenario found for "
            f"{zone_id}"
        )

    r = rainfall.loc[
        zone_id
    ]


    prediction = predict_risk(
        zone_id=zone_id,

        rainfall_1d=float(
            r["rainfall_1d"]
        ),

        rainfall_3d=float(
            r["rainfall_3d"]
        ),

        rainfall_7d=float(
            r["rainfall_7d"]
        ),

        rainfall_15d=float(
            r["rainfall_15d"]
        ),

        include_explanations=False,
    )


    results.append({
        "zone_id":
            zone_id,

        "su":
            int(zone["su"]),

        "lat":
            float(zone["lat"]),

        "lon":
            float(zone["lon"]),

        "rainfall_1d":
            float(r["rainfall_1d"]),

        "rainfall_3d":
            float(r["rainfall_3d"]),

        "rainfall_7d":
            float(r["rainfall_7d"]),

        "rainfall_15d":
            float(r["rainfall_15d"]),

        "p_static":
            prediction["p_static"],

        "p_dynamic":
            prediction["p_dynamic"],

        "p_final":
            prediction["p_final"],

        "risk_score":
            prediction["risk_score"],

        "risk_level":
            prediction["risk_level"],
    })


result = pd.DataFrame(
    results
)


# ------------------------------------------------------------
# Print
# ------------------------------------------------------------

print("\n" + "-" * 80)
print("ALL 12 DEMO ZONES")
print("-" * 80)

print(
    result[
        [
            "zone_id",
            "p_static",
            "p_dynamic",
            "p_final",
            "risk_score",
            "risk_level",
        ]
    ].to_string(
        index=False
    )
)


# ------------------------------------------------------------
# Risk distribution
# ------------------------------------------------------------

print("\n" + "-" * 80)
print("RISK DISTRIBUTION")
print("-" * 80)

print(
    result["risk_level"]
    .value_counts()
    .reindex(
        [
            "Low",
            "Moderate",
            "High",
            "Very High",
        ],
        fill_value=0
    )
)


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

output = (
    ROOT
    / "ml"
    / "data"
    / "demo"
    / "demo_predictions.csv"
)

result.to_csv(
    output,
    index=False
)

print("\nSaved:")
print(output)

print("\n" + "=" * 80)
print("12-ZONE PREDICTION COMPLETE")
print("=" * 80)
