import sys
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Alert

# Path setup for Twilio service
sys.path.append(str(Path(__file__).resolve().parents[2]))
from alerts.twilio_service import send_configured_alert

router = APIRouter(
    prefix="/api",
    tags=["Alerts"]
)


# ----------------------------------------------------
# 1. Pydantic Schemas
# ----------------------------------------------------
class OperationalAlertCreate(BaseModel):
    title: str
    severity: str = "warning"
    region: str = "All NER States"


class TriggerAlertRequest(BaseModel):
    zone_id: str
    risk_level: str
    message: str


# ----------------------------------------------------
# 2. Endpoints
# ----------------------------------------------------

@router.get("/alerts/recent")
def get_recent_alerts(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    alerts = db.query(Alert).order_by(Alert.timestamp.desc()).limit(limit).all()
    return [
        {
            "id": alert.id,
            "alert_id": alert.id,
            "title": alert.message,
            "message": alert.message,
            "severity": alert.risk_level or "warning",
            "risk_level": alert.risk_level or "warning",
            "region": alert.zone_id or "All NER States",
            "zone_id": alert.zone_id or "All NER States",
            "source": getattr(alert, "source", "OFFICIAL"),
            "is_active": getattr(alert, "is_active", True),
            "timestamp": alert.timestamp.strftime("%I:%M %p") if alert.timestamp else "Just now",
        }
        for alert in alerts
    ]


@router.post("/alerts", status_code=status.HTTP_201_CREATED)
def create_operational_alert(payload: OperationalAlertCreate, db: Session = Depends(get_db)):
    """Save an operational advisory to DB so all mobile devices & laptops can view it."""
    new_alert = Alert(
        zone_id=payload.region,
        risk_level=payload.severity.lower(),
        message=payload.title,
        timestamp=datetime.now(timezone.utc)
    )
    db.add(new_alert)
    db.commit()
    db.refresh(new_alert)
    return {"status": "ok", "alert_id": new_alert.id}


@router.delete("/alerts/{alert_id}")
def delete_operational_alert(alert_id: int, db: Session = Depends(get_db)):
    """Delete an operational alert across all clients."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if alert:
        db.delete(alert)
        db.commit()
    return {"status": "ok", "deleted": alert_id}


@router.post("/trigger-alert")
def trigger_alert(payload: TriggerAlertRequest):
    sms_result = send_configured_alert(payload.message)

    return {
        "status": "sent" if sms_result.get("success") else "failed",
        "zone_id": payload.zone_id,
        "risk_level": payload.risk_level,
        "sms_result": sms_result,
    }