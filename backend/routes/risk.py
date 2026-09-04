import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Zone, RiskScore

router = APIRouter(
    prefix="/api",
    tags=["Risk"]
)


@router.get("/risk-zones")
def get_risk_zones(db: Session = Depends(get_db)):
    zones = db.query(Zone).all()

    result = []

    for zone in zones:
        latest_risk = (
            db.query(RiskScore)
            .filter(RiskScore.zone_id == zone.zone_id)
            .order_by(RiskScore.timestamp.desc())
            .first()
        )

        if latest_risk:
            try:
                top_factors = json.loads(latest_risk.top_factors or "[]")
            except json.JSONDecodeError:
                top_factors = []

            result.append({
                "zone_id": zone.zone_id,
                "lat": zone.lat,
                "lon": zone.lon,
                "risk_score": latest_risk.risk_score,
                "risk_level": latest_risk.risk_level,
                "top_factors": top_factors
            })

    return result