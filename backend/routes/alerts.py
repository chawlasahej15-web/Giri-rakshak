from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from models import Alert
from alerts.twilio_service import send_configured_alert


router = APIRouter(
    prefix="/api",
    tags=["Alerts"]
)


class TriggerAlertRequest(BaseModel):
    zone_id: str
    risk_level: str
    message: str


@router.post("/trigger-alert")
def trigger_alert(data: TriggerAlertRequest):
    alert_message = (
        f"Giri-Rakshak {data.risk_level.upper()} ALERT: "
        f"{data.message} Zone: {data.zone_id}"
    )

    result = send_configured_alert(alert_message)

    return {
        "status": "sent",
        "zone_id": data.zone_id,
        "risk_level": data.risk_level,
        "sms_result": result,
    }


@router.get("/alerts/recent")
def get_recent_alerts(db: Session = Depends(get_db)):
    alerts = (
        db.query(Alert)
        .order_by(Alert.timestamp.desc())
        .limit(20)
        .all()
    )

    return [
        {
            "alert_id": alert.id,
            "zone_id": alert.zone_id,
            "risk_level": alert.risk_level,
            "message": alert.message,
            "timestamp": alert.timestamp
        }
        for alert in alerts
    ]