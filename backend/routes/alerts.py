from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from auth import require_roles
from database import get_db
from models import Alert, User
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[2]))
from alerts.twilio_service import send_configured_alert
router = APIRouter(
    prefix="/api",
    tags=["Alerts"]
)


@router.get("/alerts/recent")
def get_recent_alerts(
    limit: int = Query(default=20, ge=1, le=100),

    db: Session = Depends(get_db),
):
    
    alerts = db.query(Alert).order_by(Alert.timestamp.desc()).limit(limit).all()
    return [
        {
            "alert_id": alert.id,
            "zone_id": alert.zone_id,
            "risk_level": alert.risk_level,
            "source": alert.source,
            "message": alert.message,
            "is_active": alert.is_active,
            "timestamp": alert.timestamp,
        }
        for alert in alerts
    ]
class TriggerAlertRequest(BaseModel):
    zone_id: str
    risk_level: str
    message: str


@router.post("/trigger-alert")
def trigger_alert(payload: TriggerAlertRequest):
    sms_result = send_configured_alert(payload.message)

    return {
        "status": "sent" if sms_result.get("success") else "failed",
        "zone_id": payload.zone_id,
        "risk_level": payload.risk_level,
        "sms_result": sms_result,
    }