from pathlib import Path
import sys

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

OUTPUT = (
    ROOT
    / "ml"
    / "data"
    / "demo"
    / "demo_rainfall.csv"
)


# A variety of realistic cumulative-rainfall patterns.
PROFILES = []

bases = [
    (5, 15, 30, 60),
    (15, 35, 60, 100),
    (30, 70, 120, 180),
    (50, 110, 180, 260),
    (70, 140, 220, 320),
    (100, 190, 280, 380),
    (140, 250, 360, 500),
]

scales = [
    0.5,
    0.75,
    1.0,
    1.25,
    1.5,
]

for base in bases:

    for scale in scales:

        PROFILES.append({
            "rainfall_1d":
                base[0] * scale,

            "rainfall_3d":
                base[1] * scale,

            "rainfall_7d":
                base[2] * scale,

            "rainfall_15d":
                base[3] * scale,
        })


targets = [
    "Low",
    "Moderate",
    "High",
    "Very High",
    "Low",
    "Moderate",
    "High",
    "Very High",
    "Low",
    "Moderate",
    "High",
    "Very High",
]


bands = {
    "Low": 0.05,
    "Moderate": 0.25,
    "High": 0.60,
    "Very High": 0.90,
}


print("\n" + "=" * 70)
print("CREATING 12-ZONE DEMO RAINFALL")
print("=" * 70)


zones = pd.read_csv(
    ZONES_FILE
)


rows = []


for zone_id, target in zip(
    zones["zone_id"],
    targets
):

    best = None

    for profile_no, profile in enumerate(
        PROFILES,
        start=1
    ):

        result = predict_risk(
            zone_id=zone_id,
            **profile,
            include_explanations=False
        )

        p = result["p_final"]
        actual_band = result["risk_level"]

        exact = (
            actual_band == target
        )

        score = (
            0
            if exact
            else abs(
                p
                -
                bands[target]
            )
        )

        if (
            best is None
            or score < best["score"]
        ):

            best = {
                "score": score,
                "profile_no": profile_no,
                **profile,
                "p_final": p,
                "risk_level": actual_band,
            }

    rows.append({
        "zone_id": zone_id,
        "date": "2026-09-06",

        "rainfall_1d":
            best["rainfall_1d"],

        "rainfall_3d":
            best["rainfall_3d"],

        "rainfall_7d":
            best["rainfall_7d"],

        "rainfall_15d":
            best["rainfall_15d"],

        "expected_p_final":
            best["p_final"],

        "expected_risk_level":
            best["risk_level"],

        "target_risk_level":
            target,
    })


result = pd.DataFrame(
    rows
)

result.to_csv(
    OUTPUT,
    index=False
)


print("\n" + "-" * 70)
print("DEMO RAINFALL SCENARIOS")
print("-" * 70)

print(
    result.to_string(index=False)
)

print("\nSaved:")
print(OUTPUT)

print("\n" + "=" * 70)
print("DEMO RAINFALL READY")
print("=" * 70)
