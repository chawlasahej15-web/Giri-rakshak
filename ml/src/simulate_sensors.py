"""
GiriRakshak 12-zone demo sensor simulator.

The simulator sends the exact payload expected by:

POST /api/sensor-data

Sensor values are used by the backend reactive safety layer.

ML2 prediction uses rainfall features separately.
"""

from __future__ import annotations

import argparse
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests


# ============================================================
# PATHS
# ============================================================

ML_DIR = Path(__file__).resolve().parents[1]

DEMO_ZONES_FILE = (
    ML_DIR
    / "data"
    / "demo"
    / "demo_zones.csv"
)

DEMO_RAINFALL_FILE = (
    ML_DIR
    / "data"
    / "demo"
    / "demo_rainfall.csv"
)


DEFAULT_URL = (
    "http://127.0.0.1:8000/api/sensor-data"
)


# ============================================================
# SENSOR SCENARIOS
# ============================================================

SCENARIOS = {

    "normal": {
        "tilt_deg": 5.0,
        "moisture_pct": 45.0,
        "displacement_cm": 0.5,
    },

    "tilt_alert": {
        "tilt_deg": 18.0,
        "moisture_pct": 45.0,
        "displacement_cm": 1.0,
    },

    "moisture_alert": {
        "tilt_deg": 7.0,
        "moisture_pct": 86.0,
        "displacement_cm": 1.5,
    },

    "critical": {
        "tilt_deg": 19.0,
        "moisture_pct": 88.0,
        "displacement_cm": 4.0,
    },
}


# ============================================================
# DEMO SCENARIO ASSIGNMENT
# ============================================================

ZONE_SCENARIOS = {
    "DEMO_ZONE_01": "normal",
    "DEMO_ZONE_02": "normal",

    "DEMO_ZONE_03": "tilt_alert",

    "DEMO_ZONE_04": "normal",

    "DEMO_ZONE_05": "critical",

    "DEMO_ZONE_06": "normal",

    "DEMO_ZONE_07": "normal",

    "DEMO_ZONE_08": "moisture_alert",

    "DEMO_ZONE_09": "normal",

    "DEMO_ZONE_10": "tilt_alert",

    "DEMO_ZONE_11": "normal",

    "DEMO_ZONE_12": "critical",
}


# ============================================================
# LOAD + VALIDATE
# ============================================================

def load_demo_data():
    """
    Load the six/twelve-zone demo files.
    """

    if not DEMO_ZONES_FILE.exists():

        raise FileNotFoundError(
            f"Demo zones file not found:\n"
            f"{DEMO_ZONES_FILE}"
        )

    if not DEMO_RAINFALL_FILE.exists():

        raise FileNotFoundError(
            f"Demo rainfall file not found:\n"
            f"{DEMO_RAINFALL_FILE}"
        )

    zones = pd.read_csv(
        DEMO_ZONES_FILE
    )

    rainfall = pd.read_csv(
        DEMO_RAINFALL_FILE
    )

    required_zone_columns = [
        "zone_id",
        "su",
        "lat",
        "lon",
    ]

    missing_zone_columns = [
        c
        for c in required_zone_columns
        if c not in zones.columns
    ]

    if missing_zone_columns:

        raise ValueError(
            "Missing zone columns:\n"
            + "\n".join(
                missing_zone_columns
            )
        )

    required_rainfall_columns = [
        "zone_id",
        "rainfall_1d",
        "rainfall_3d",
        "rainfall_7d",
        "rainfall_15d",
    ]

    missing_rainfall_columns = [
        c
        for c in required_rainfall_columns
        if c not in rainfall.columns
    ]

    if missing_rainfall_columns:

        raise ValueError(
            "Missing rainfall columns:\n"
            + "\n".join(
                missing_rainfall_columns
            )
        )

    return zones, rainfall


# ============================================================
# SEND SENSOR READING
# ============================================================

def send_sensor_reading(
    url: str,
    zone: dict,
    scenario: str,
    timeout: float = 5.0,
):
    """
    Send one sensor reading to the backend.
    """

    values = SCENARIOS[
        scenario
    ]

    payload = {
        "sensor_id":
            zone["zone_id"],

        "lat":
            float(zone["lat"]),

        "lon":
            float(zone["lon"]),

        "tilt_deg":
            float(
                values["tilt_deg"]
            ),

        "moisture_pct":
            float(
                values["moisture_pct"]
            ),

        "displacement_cm":
            float(
                values["displacement_cm"]
            ),

        "timestamp":
            datetime.now(
                timezone.utc
            ).isoformat(),
    }

    response = requests.post(
        url,
        json=payload,
        timeout=timeout,
    )

    response.raise_for_status()

    return payload, response.json()


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Send simulated GiriRakshak "
            "sensor data for 12 demo zones."
        )
    )

    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help=(
            "Backend /api/sensor-data URL."
        ),
    )

    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help=(
            "Seconds between zone readings."
        ),
    )

    args = parser.parse_args()

    zones, rainfall = (
        load_demo_data()
    )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    if len(zones) != 12:

        raise ValueError(
            f"Expected 12 demo zones, "
            f"found {len(zones)}."
        )

    zone_ids = (
        zones["zone_id"]
        .astype(str)
        .tolist()
    )

    missing_scenarios = [
        zone_id
        for zone_id in zone_ids
        if zone_id not in ZONE_SCENARIOS
    ]

    if missing_scenarios:

        raise ValueError(
            "No sensor scenario configured for:\n"
            + "\n".join(
                missing_scenarios
            )
        )

    rainfall_zone_ids = set(
        rainfall["zone_id"]
        .astype(str)
    )

    missing_rainfall = [
        zone_id
        for zone_id in zone_ids
        if zone_id not in rainfall_zone_ids
    ]

    if missing_rainfall:

        raise ValueError(
            "No rainfall scenario configured for:\n"
            + "\n".join(
                missing_rainfall
            )
        )


    # --------------------------------------------------------
    # Header
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("GIRIRAKSHAK — 12 ZONE SENSOR DEMO")
    print("=" * 80)


    # --------------------------------------------------------
    # Send all zones
    # --------------------------------------------------------

    for _, row in zones.iterrows():

        zone_id = str(
            row["zone_id"]
        )

        scenario = (
            ZONE_SCENARIOS[
                zone_id
            ]
        )

        rainfall_row = (
            rainfall[
                rainfall["zone_id"].astype(str)
                == zone_id
            ]
            .iloc[0]
        )


        try:

            payload, result = (
                send_sensor_reading(
                    url=args.url,
                    zone=row.to_dict(),
                    scenario=scenario,
                )
            )


            print(
                f"{zone_id:15s}"
                f" | sensor={scenario:18s}"
                f" | tilt={payload['tilt_deg']:5.1f}°"
                f" | moisture={payload['moisture_pct']:5.1f}%"
                f" | ML={rainfall_row.get('expected_risk_level', 'N/A'):9s}"
                f" | reactive="
                f"{result.get('reactive_alert_triggered')}"
                f" | ml_generated="
                f"{result.get('ml_prediction_generated')}"
            )


        except requests.RequestException as exc:

            print(
                f"{zone_id:15s}"
                f" | REQUEST FAILED"
                f" | {exc}"
            )


        except Exception as exc:

            print(
                f"{zone_id:15s}"
                f" | ERROR"
                f" | {exc}"
            )


        time.sleep(
            max(
                args.interval,
                0.0
            )
        )


    print()
    print("=" * 80)
    print("SENSOR DEMO COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
