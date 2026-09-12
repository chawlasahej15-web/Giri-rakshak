from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from auth import require_roles
from database import get_db
from models import Alert

router = APIRouter(
    prefix="/api",
    tags=["Alerts"]
)


@router.get("/alerts/recent")
def get_recent_alerts(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_roles("official")),
    db: Session = Depends(get_db),
):
    del current_user
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
