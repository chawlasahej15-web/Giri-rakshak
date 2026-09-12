from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from auth import require_roles
from config import MAX_UPLOAD_MB, UPLOAD_DIR
from database import get_db
from models import CitizenReport, ReportUpdate, User
from schemas import ReportOut
from services import nearest_zone, notify_officials, notify_citizen_report_status

router = APIRouter(prefix="/api", tags=["Citizen Reports"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def save_photo(photo: UploadFile) -> str:
    if photo.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only JPG, PNG and WEBP images are allowed")

    suffix = Path(photo.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported image extension")

    content = photo.file.read()
    max_bytes = MAX_UPLOAD_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail=f"Image must be <= {MAX_UPLOAD_MB} MB")

    filename = f"{uuid4().hex}{suffix}"
    destination = UPLOAD_DIR / filename
    destination.write_bytes(content)
    return f"/uploads/reports/{filename}"


@router.post("/reports", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
@router.post("/citizen-report", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
async def create_citizen_report(
    lat: float = Form(...),
    lon: float = Form(...),
    description: str = Form(""),
    category: str = Form("landslide"),
    severity: str = Form("medium"),
    photo: UploadFile | None = File(None),
    current_user: User = Depends(require_roles("citizen")),
    db: Session = Depends(get_db),
):
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise HTTPException(status_code=400, detail="Invalid latitude/longitude")

    allowed_categories = {"landslide", "rockfall", "soil_slip", "crack", "waterlogging", "other"}
    if category not in allowed_categories:
        raise HTTPException(status_code=400, detail="Invalid report category")

    if severity not in {"low", "medium", "high", "critical"}:
        raise HTTPException(status_code=400, detail="Invalid severity")

    photo_path = save_photo(photo) if photo else None
    now = datetime.now(timezone.utc)
    zone_id = nearest_zone(db, lat, lon)

    report = CitizenReport(
        user_id=current_user.id,
        zone_id=zone_id,
        lat=lat,
        lon=lon,
        photo_path=photo_path,
        description=description.strip() or None,
        category=category,
        severity=severity,
        status="submitted",
        reported_at=now,
        updated_at=now,
    )
    db.add(report)
    db.flush()

    db.add(
        ReportUpdate(
            report_id=report.id,
            actor_user_id=current_user.id,
            old_status=None,
            new_status="submitted",
            note="Citizen submitted a new report.",
        )
    )

    notify_officials(
        db,
        notification_type="new_report",
        title="New citizen landslide report",
        message=(
            f"A {severity} severity {category} report was submitted"
            + (f" in zone {zone_id}." if zone_id else ".")
        ),
        severity=severity,
        report_id=report.id,
    )

    db.commit()
    db.refresh(report)
    return report


@router.get("/citizen/reports", response_model=list[ReportOut])
def citizen_reports(
    current_user: User = Depends(require_roles("citizen")),
    db: Session = Depends(get_db),
):
    return (
        db.query(CitizenReport)
        .filter(CitizenReport.user_id == current_user.id)
        .order_by(CitizenReport.reported_at.desc())
        .all()
    )
