"""
GiriRakshak 12-zone demo sensor simulator.

The simulator sends the exact payload expected by:

POST /api/sensor-data

Design:
- ML risk is generated independently from the demo rainfall/geospatial pipeline.
- Sensor readings act as an independent local fail-safe layer.
- Sensor thresholds are handled by the backend:
    tilt > 15 degrees
    moisture > 80 percent

This simulator deliberately creates different sensor scenarios
across the 12 demo zones so the dashboard can demonstrate:

1. ML low risk + physical sensor alert
2. ML moderate/high risk + normal sensor
3. ML high risk + sensor alert
4. ML very high risk + sensor normal
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

    # --------------------------------------------------------
    # Safe local conditions
    # --------------------------------------------------------
    "normal_low": {
        "tilt_deg": 4.5,
        "moisture_pct": 38.0,
        "displacement_cm": 0.2,
    },

    # --------------------------------------------------------
    # Normal but slightly elevated local conditions
    # --------------------------------------------------------
    "normal_moderate": {
        "tilt_deg": 6.0,
        "moisture_pct": 46.0,
        "displacement_cm": 0.5,
    },

    # --------------------------------------------------------
    # Independent tilt fail-safe
    # Tilt crosses 15° threshold
    # --------------------------------------------------------
    "tilt_fail_safe": {
        "tilt_deg": 18.0,
        "moisture_pct": 55.0,
        "displacement_cm": 1.8,
    },

    # --------------------------------------------------------
    # Elevated moisture but below 80% threshold
    # --------------------------------------------------------
    "wet_watch": {
        "tilt_deg": 8.0,
        "moisture_pct": 68.0,
        "displacement_cm": 0.9,
    },

    # --------------------------------------------------------
    # Independent moisture fail-safe
    # Moisture crosses 80% threshold
    # --------------------------------------------------------
    "moisture_fail_safe": {
        "tilt_deg": 7.0,
        "moisture_pct": 86.0,
        "displacement_cm": 1.5,
    },

    # --------------------------------------------------------
    # Both local sensor conditions abnormal
    # --------------------------------------------------------
    "critical_sensor": {
        "tilt_deg": 19.0,
        "moisture_pct": 88.0,
        "displacement_cm": 4.0,
    },

    # --------------------------------------------------------
    # Borderline but below both reactive thresholds
    # 14° < 15°
    # 76% < 80%
    # --------------------------------------------------------
    "borderline": {
        "tilt_deg": 14.0,
        "moisture_pct": 76.0,
        "displacement_cm": 2.0,
    },

    # --------------------------------------------------------
    # Elevated tilt but still below reactive threshold
    # --------------------------------------------------------
    "elevated_tilt": {
        "tilt_deg": 11.0,
        "moisture_pct": 72.0,
        "displacement_cm": 1.2,
    },
}


# ============================================================
# DEMO SCENARIO ASSIGNMENT
# ============================================================
#
# The assignment is intentionally designed to demonstrate
# ML risk and local sensor fail-safe as two independent layers.
#
# ------------------------------------------------------------
#
# DEMO_ZONE_01
# ML: LOW
# Sensor: ALERT
# -> Fail-safe catches abnormal physical tilt even though
#    the regional ML model considers the zone low risk.
#
# DEMO_ZONE_02
# ML: MODERATE
# Sensor: NORMAL
# -> Normal baseline.
#
# DEMO_ZONE_03
# ML: HIGH
# Sensor: ALERT
# -> ML and physical sensor agree.
#
# DEMO_ZONE_04
# ML: HIGH
# Sensor: NORMAL
# -> Model warns, but the local node has not crossed
#    a physical safety threshold.
#
# DEMO_ZONE_05
# ML: MODERATE
# Sensor: CRITICAL
# -> Strong fail-safe case.
#
# DEMO_ZONE_06
# ML: MODERATE
# Sensor: NORMAL / wet-watch.
#
# DEMO_ZONE_07
# ML: HIGH
# Sensor: BORDERLINE
# -> Elevated values but still below reactive thresholds.
#
# DEMO_ZONE_08
# ML: VERY HIGH
# Sensor: MOISTURE ALERT
# -> Regional model and physical moisture warning agree.
#
# DEMO_ZONE_09
# ML: HIGH
# Sensor: ELEVATED TILT
# -> Model warning with elevated local condition.
#
# DEMO_ZONE_10
# ML: HIGH
# Sensor: TILT ALERT
# -> Physical tilt confirms concern.
#
# DEMO_ZONE_11
# ML: HIGH
# Sensor: BORDERLINE
# -> Near threshold but no reactive trigger.
#
# DEMO_ZONE_12
# ML: VERY HIGH
# Sensor: NORMAL
# -> Strong example where the regional model warns while
#    local sensors are currently normal.
#
# ============================================================

ZONE_SCENARIOS = {

    "DEMO_ZONE_01": "tilt_fail_safe",

    "DEMO_ZONE_02": "normal_moderate",

    "DEMO_ZONE_03": "tilt_fail_safe",

    "DEMO_ZONE_04": "normal_low",

    "DEMO_ZONE_05": "critical_sensor",

    "DEMO_ZONE_06": "wet_watch",

    "DEMO_ZONE_07": "borderline",

    "DEMO_ZONE_08": "moisture_fail_safe",

    "DEMO_ZONE_09": "elevated_tilt",

    "DEMO_ZONE_10": "tilt_fail_safe",

    "DEMO_ZONE_11": "borderline",

    "DEMO_ZONE_12": "normal_moderate",
}


# ============================================================
# LOAD + VALIDATE
# ============================================================

def load_demo_data():
    """
    Load the 12-zone demo files.
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
            str(zone["zone_id"]),

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
    # Validation: exactly 12 zones
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

    # --------------------------------------------------------
    # Validation: every zone has a sensor scenario
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Validation: every zone has rainfall scenario
    # --------------------------------------------------------

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
    print("=" * 90)
    print("GIRIRAKSHAK — 12 ZONE FAIL-SAFE SENSOR DEMO")
    print("=" * 90)
    print()
    print(
        "Sensor safety thresholds:"
    )
    print(
        "  Tilt     > 15°"
    )
    print(
        "  Moisture > 80%"
    )
    print()
    print(
        "ML risk and physical sensor safety are evaluated"
    )
    print(
        "as independent layers."
    )
    print()

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

            reactive = bool(
                result.get(
                    "reactive_alert_triggered",
                    False
                )
            )

            ml_generated = bool(
                result.get(
                    "ml_prediction_generated",
                    False
                )
            )

            # ------------------------------------------------
            # Human-readable fail-safe explanation
            # ------------------------------------------------

            reasons = []

            if (
                payload["tilt_deg"] > 15.0
            ):
                reasons.append(
                    "TILT"
                )

            if (
                payload["moisture_pct"] > 80.0
            ):
                reasons.append(
                    "MOISTURE"
                )

            if reasons:
                sensor_status = (
                    "ALERT:" +
                    "+".join(reasons)
                )
            else:
                sensor_status = "NORMAL"

            expected_ml = str(
                rainfall_row.get(
                    "expected_risk_level",
                    "N/A"
                )
            )

            print(
                f"{zone_id:15s}"
                f" | sensor={scenario:18s}"
                f" | tilt={payload['tilt_deg']:5.1f}°"
                f" | moisture={payload['moisture_pct']:5.1f}%"
                f" | ML={expected_ml:9s}"
                f" | sensor_status={sensor_status:14s}"
                f" | reactive={str(reactive):5s}"
                f" | ml_generated={str(ml_generated):5s}"
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

    # --------------------------------------------------------
    # Footer
    # --------------------------------------------------------

    print()
    print("=" * 90)
    print("SENSOR DEMO COMPLETE")
    print("=" * 90)
    print()
    print(
        "Fail-safe examples:"
    )
    print(
        "  DEMO_ZONE_01  -> ML LOW + sensor tilt alert"
    )
    print(
        "  DEMO_ZONE_04  -> ML HIGH + sensor normal"
    )
    print(
        "  DEMO_ZONE_03  -> ML HIGH + sensor tilt alert"
    )
    print(
        "  DEMO_ZONE_08  -> ML VERY HIGH + moisture alert"
    )
    print(
        "  DEMO_ZONE_12  -> ML VERY HIGH + sensor normal"
    )
    print()


if __name__ == "__main__":
    main()
