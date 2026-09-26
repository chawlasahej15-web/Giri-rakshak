from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import DeviceToken

router = APIRouter(
    prefix="/api",
    tags=["Devices"]
)


class DeviceTokenRequest(BaseModel):
    token: str
    role: str = "official"


@router.post("/devices/register")
def register_device(
    payload: DeviceTokenRequest,
    db: Session = Depends(get_db),
):
    existing_token = (
        db.query(DeviceToken)
        .filter(DeviceToken.token == payload.token)
        .first()
    )

    if existing_token:
        existing_token.role = payload.role
        db.commit()

        return {
            "status": "ok",
            "message": "Device token updated successfully"
        }

    new_device = DeviceToken(
        token=payload.token,
        role=payload.role,
    )

    db.add(new_device)
    db.commit()
    db.refresh(new_device)

    return {
        "status": "ok",
        "message": "Device token registered successfully",
        "device_id": new_device.id
    }