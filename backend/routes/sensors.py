from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import SensorReading, Alert

router = APIRouter(
    prefix="/api",
    tags=["Sensors"]
)


class SensorData(BaseModel):
    sensor_id: str
    lat: float
    lon: float
    tilt_deg: float
    moisture_pct: float
    displacement_cm: float
    timestamp: datetime


@router.post("/sensor-data")
def receive_sensor_data(
    data: SensorData,
    db: Session = Depends(get_db)
):
    # Reactive safety layer:
    # Trigger immediately if physical sensor thresholds are crossed.
    reactive_alert = (
        data.tilt_deg > 15
        or data.moisture_pct > 80
    )

    # Save sensor reading to database
    reading = SensorReading(
        sensor_id=data.sensor_id,
        lat=data.lat,
        lon=data.lon,
        tilt_deg=data.tilt_deg,
        moisture_pct=data.moisture_pct,
        displacement_cm=data.displacement_cm,
        timestamp=data.timestamp
    )

    db.add(reading)
    db.commit()
    db.refresh(reading)
    if reactive_alert:
        alert = Alert(
            zone_id=data.sensor_id,
            risk_level="critical",
            message="Reactive alert: abnormal sensor threshold detected.",
            timestamp=data.timestamp
        )

        db.add(alert)
        db.commit()

    return {
    "status": "received",
    "reactive_alert_triggered": reactive_alert
    }
