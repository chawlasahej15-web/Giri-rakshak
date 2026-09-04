from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from database import get_db
from models import CitizenReport


router = APIRouter(
    prefix="/api",
    tags=["Reports"]
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/citizen-report")
async def create_citizen_report(
    lat: float = Form(...),
    lon: float = Form(...),
    description: str = Form(""),
    timestamp: str = Form(...),
    photo: UploadFile | None = File(None),
    db: Session = Depends(get_db)
):
    photo_path = None

    if photo:
        filename = (
            f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}_"
            f"{Path(photo.filename).name}"
        )

        file_path = UPLOAD_DIR / filename
        file_path.write_bytes(await photo.read())

        photo_path = str(file_path)

    report = CitizenReport(
        lat=lat,
        lon=lon,
        photo_path=photo_path,
        description=description,
        timestamp=datetime.fromisoformat(timestamp)
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    return {
        "status": "received",
        "report_id": report.id
    }