from datetime import datetime, timedelta, timezone
from math import cos, radians

from sqlalchemy import func
from sqlalchemy.orm import Session

from models import Alert, CitizenReport, Notification, User, Zone


SEVERITY_WEIGHT = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


def utcnow():
    return datetime.now(timezone.utc)


def nearest_zone(db: Session, lat: float, lon: float, max_distance_deg: float = 0.10) -> str | None:
    zones = db.query(Zone).all()
    if not zones:
        return None

    best_zone = None
    best_distance = float("inf")
    lat_scale = max(cos(radians(lat)), 0.25)

    for zone in zones:
        dx = (zone.lon - lon) * lat_scale
        dy = zone.lat - lat
        distance = (dx * dx + dy * dy) ** 0.5
        if distance < best_distance:
            best_distance = distance
            best_zone = zone

    return best_zone.zone_id if best_zone and best_distance <= max_distance_deg else None


def notify_user(
    db: Session,
    user_id: int,
    notification_type: str,
    title: str,
    message: str,
    severity: str = "info",
    report_id: int | None = None,
    alert_id: int | None = None,
):
    db.add(
        Notification(
            user_id=user_id,
            report_id=report_id,
            alert_id=alert_id,
            notification_type=notification_type,
            title=title,
            message=message,
            severity=severity,
        )
    )


def notify_officials(
    db: Session,
    notification_type: str,
    title: str,
    message: str,
    severity: str = "info",
    report_id: int | None = None,
    alert_id: int | None = None,
):
    official_ids = [
        row[0]
        for row in db.query(User.id)
        .filter(User.role == "official", User.is_active.is_(True))
        .all()
    ]
    for user_id in official_ids:
        notify_user(
            db,
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            severity=severity,
            report_id=report_id,
            alert_id=alert_id,
        )


def notify_citizen_report_status(
    db: Session,
    report: CitizenReport,
    title: str,
    message: str,
    severity: str = "info",
):
    if report.user_id:
        notify_user(
            db,
            user_id=report.user_id,
            notification_type="report_status",
            title=title,
            message=message,
            severity=severity,
            report_id=report.id,
        )


def should_create_alert(
    db: Session,
    zone_id: str,
    risk_level: str,
    cooldown_minutes: int = 10,
) -> bool:
    cutoff = utcnow() - timedelta(minutes=cooldown_minutes)
    return (
        db.query(Alert)
        .filter(
            Alert.zone_id == zone_id,
            Alert.risk_level == risk_level,
            Alert.timestamp >= cutoff,
            Alert.is_active.is_(True),
        )
        .first()
        is None
    )
