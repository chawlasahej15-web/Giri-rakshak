from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Alert

router = APIRouter(
    prefix="/api",
    tags=["Alerts"]
)


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