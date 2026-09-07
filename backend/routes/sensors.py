import json
import sys
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session


# ============================================================
# REPOSITORY PATH
# ============================================================

REPO_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(REPO_ROOT)
    )


# ============================================================
# BACKEND IMPORTS
# ============================================================

from database import get_db
from models import (
    SensorReading,
    Alert,
    RiskScore,
)

from ml.src.predict import predict_risk
from alerts.twilio_service import send_configured_alert

router = APIRouter(
    prefix="/api",
    tags=["Sensors"]
)


# ============================================================
# SENSOR REQUEST MODEL
# ============================================================

class SensorData(BaseModel):

    sensor_id: str

    lat: float
    lon: float

    tilt_deg: float
    moisture_pct: float
    displacement_cm: float

    timestamp: datetime


# ============================================================
# DEMO RAINFALL LOOKUP
# ============================================================

@lru_cache(maxsize=1)
def load_demo_rainfall():

    path = (
        REPO_ROOT
        / "ml"
        / "data"
        / "demo"
        / "demo_rainfall.csv"
    )

    if not path.exists():

        raise FileNotFoundError(
            f"Demo rainfall file not found:\n{path}"
        )

    df = pd.read_csv(
        path
    )

    required = [
        "zone_id",
        "rainfall_1d",
        "rainfall_3d",
        "rainfall_7d",
        "rainfall_15d",
    ]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:

        raise ValueError(
            "demo_rainfall.csv is missing columns:\n"
            + "\n".join(missing)
        )

    df["zone_id"] = (
        df["zone_id"]
        .astype(str)
    )

    if df["zone_id"].duplicated().any():

        raise ValueError(
            "Duplicate zone_id values found "
            "in demo_rainfall.csv."
        )

    return df.set_index(
        "zone_id"
    )


# ============================================================
# SENSOR ENDPOINT
# ============================================================

@router.post("/sensor-data")
def receive_sensor_data(
    data: SensorData,
    db: Session = Depends(get_db),
):

    # --------------------------------------------------------
    # 1. Reactive sensor safety layer
    # --------------------------------------------------------

    reactive_alert = (
        data.tilt_deg > 15.0
        or
        data.moisture_pct > 80.0
    )


    # --------------------------------------------------------
    # 2. Save raw sensor reading
    # --------------------------------------------------------

    reading = SensorReading(
        sensor_id=data.sensor_id,
        lat=data.lat,
        lon=data.lon,
        tilt_deg=data.tilt_deg,
        moisture_pct=data.moisture_pct,
        displacement_cm=data.displacement_cm,
        timestamp=data.timestamp,
    )

    db.add(
        reading
    )


    # --------------------------------------------------------
    # 3. Reactive alert
    # --------------------------------------------------------

    if reactive_alert:

        alert_message = (
            "Giri-Rakshak CRITICAL ALERT: "
            "Abnormal sensor threshold detected. "
            f"Zone: {data.sensor_id}"
        )

        alert = Alert(
            zone_id=data.sensor_id,
            risk_level="critical",
            message=alert_message,
            timestamp=data.timestamp,
        )

        db.add(alert)

        # Send SMS alert
        sms_result = send_configured_alert(alert_message)

        print("Reactive SMS Result:", sms_result)

    # --------------------------------------------------------
    # 4. ML prediction
    # --------------------------------------------------------

    ml_result = None
    ml_error = None


    try:

        rainfall = load_demo_rainfall()


        zone_id = str(
            data.sensor_id
        )


        if zone_id not in rainfall.index:

            raise ValueError(
                f"No rainfall scenario configured "
                f"for zone {zone_id}."
            )


        rainfall_row = (
            rainfall.loc[
                zone_id
            ]
        )


        ml_result = predict_risk(

            zone_id=zone_id,

            rainfall_1d=float(
                rainfall_row[
                    "rainfall_1d"
                ]
            ),

            rainfall_3d=float(
                rainfall_row[
                    "rainfall_3d"
                ]
            ),

            rainfall_7d=float(
                rainfall_row[
                    "rainfall_7d"
                ]
            ),

            rainfall_15d=float(
                rainfall_row[
                    "rainfall_15d"
                ]
            ),

            include_explanations=True,
        )


        # ----------------------------------------------------
        # 5. Save ML risk score
        # ----------------------------------------------------

        risk_record = RiskScore(
            zone_id=zone_id,

            risk_score=float(
                ml_result[
                    "risk_score"
                ]
            ),

            risk_level=str(
                ml_result[
                    "risk_level"
                ]
            ),

            top_factors=json.dumps(
                ml_result[
                    "top_factors"
                ]
            ),

            timestamp=data.timestamp,
        )

        db.add(
            risk_record
        )


        # ----------------------------------------------------
        # 6. ML high-risk alert
        # ----------------------------------------------------

        if (
            float(
                ml_result["p_final"]
            )
            >= 0.80
        ):

            ml_alert = Alert(
                zone_id=zone_id,

                risk_level="very_high",

                message=(
                    "ML warning: "
                    f"predicted landslide risk "
                    f"is {ml_result['risk_score']:.1f}%."
                ),

                timestamp=data.timestamp,
            )

            db.add(
                ml_alert
            )


    except Exception as exc:

        ml_error = str(
            exc
        )


    # --------------------------------------------------------
    # 7. Commit all DB changes
    # --------------------------------------------------------

    db.commit()


    # --------------------------------------------------------
    # 8. Response
    # --------------------------------------------------------

    response = {
        "status": "received",

        "reactive_alert_triggered":
            reactive_alert,

        "ml_prediction_generated":
            ml_result is not None,
    }


    if ml_result is not None:

        response.update({

            "p_static":
                ml_result[
                    "p_static"
                ],

            "p_dynamic":
                ml_result[
                    "p_dynamic"
                ],

            "p_final":
                ml_result[
                    "p_final"
                ],

            "risk_score":
                ml_result[
                    "risk_score"
                ],

            "risk_level":
                ml_result[
                    "risk_level"
                ],

        })


    if ml_error is not None:

        response[
            "ml_error"
        ] = ml_error


    return response
# ============================================================
# LATEST SENSOR READING
# ============================================================

@router.get("/sensor-data/latest")
def get_latest_sensor_data(
    db: Session = Depends(get_db),
):
    reading = (
        db.query(SensorReading)
        .order_by(SensorReading.timestamp.desc())
        .first()
    )

    if reading is None:
        return {
            "status": "no_data",
            "reading": None,
        }

    return {
        "status": "ok",
        "reading": {
            "id": reading.id,
            "sensor_id": reading.sensor_id,
            "lat": reading.lat,
            "lon": reading.lon,
            "tilt_deg": reading.tilt_deg,
            "moisture_pct": reading.moisture_pct,
            "displacement_cm": reading.displacement_cm,
            "timestamp": reading.timestamp.isoformat(),
        },
    }
# ============================================================
# LATEST SENSOR READING FOR A SPECIFIC SENSOR / ZONE
# ============================================================

@router.get("/sensor-data/latest/{sensor_id}")
def get_latest_sensor_data_for_zone(
    sensor_id: str,
    db: Session = Depends(get_db),
):
    reading = (
        db.query(SensorReading)
        .filter(SensorReading.sensor_id == sensor_id)
        .order_by(SensorReading.timestamp.desc())
        .first()
    )

    if reading is None:
        return {
            "status": "no_data",
            "reading": None,
            "sensor_id": sensor_id,
        }

    return {
        "status": "ok",
        "reading": {
            "id": reading.id,
            "sensor_id": reading.sensor_id,
            "lat": reading.lat,
            "lon": reading.lon,
            "tilt_deg": reading.tilt_deg,
            "moisture_pct": reading.moisture_pct,
            "displacement_cm": reading.displacement_cm,
            "timestamp": reading.timestamp.isoformat(),
        },
    }
