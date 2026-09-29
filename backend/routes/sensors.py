import json
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from database import get_db
from models import Alert, DeviceToken, SensorReading
from alerts.twilio_service import send_configured_alert
from fcm_service import send_push_notification

router = APIRouter(
    prefix="/api",
    tags=["Sensors"],
)


class SensorData(BaseModel):

    model_config = ConfigDict(
        extra="ignore"
    )

    sensor_id: str

    lat: float
    lon: float

    # MPU / TILT
    tilt_deg: float
    tilt_change_deg: float | None = None
    tilt_rate_dph: float | None = None
    tilt_sudden_change_10s_deg: float | None = None

    # ACCEL / MOVEMENT
    accel_x_g: float | None = None
    accel_y_g: float | None = None
    accel_z_g: float | None = None
    accel_magnitude_g: float | None = None
    accel_jump_g: float | None = None
    vibration_rms_g: float | None = None
    movement_ratio: float | None = None

    # SOIL
    moisture_pct: float
    moisture_change_pct: float | None = None
    moisture_rate_pph: float | None = None

    # DISTANCE
    distance_cm: float | None = None
    distance_change_cm: float | None = None
    distance_rate_cmh: float | None = None
    displacement_cm: float | None = None

    # ENVIRONMENT
    pressure_hpa: float | None = None
    temperature_c: float | None = None
    humidity_pct: float | None = None
    rainfall_mm: float | None = None

    # EDGE ALERT
    alert_level: str = "NORMAL"
    system_state: str = "NORMAL"

    timestamp: datetime


def _json_safe(value):

    if value is None:
        return None

    try:
        number = float(value)

        if (
            number != number
            or number in (
                float("inf"),
                float("-inf"),
            )
        ):
            return None

    except (TypeError, ValueError):
        return value

    return value


def _telemetry_dict(
    data: SensorData,
) -> dict:

    payload = data.model_dump()

    for field in (
        "sensor_id",
        "lat",
        "lon",
        "timestamp",
    ):
        payload.pop(field, None)

    return {
        key: _json_safe(value)
        for key, value in payload.items()
    }


def _reading_payload(
    reading: SensorReading,
) -> dict:

    telemetry = {}

    telemetry_json = getattr(
        reading,
        "telemetry_json",
        None,
    )

    if telemetry_json:

        try:
            telemetry = json.loads(
                telemetry_json
            )

        except (
            TypeError,
            json.JSONDecodeError,
        ):
            telemetry = {}

    result = {

        "id": reading.id,

        "sensor_id": reading.sensor_id,

        "lat": reading.lat,

        "lon": reading.lon,

        "tilt_deg": reading.tilt_deg,

        "moisture_pct": reading.moisture_pct,

        "displacement_cm":
            reading.displacement_cm,

        "alert_level":
            getattr(
                reading,
                "alert_level",
                None,
            ),

        "system_state":
            getattr(
                reading,
                "system_state",
                None,
            ),

        "timestamp":
            reading.timestamp.isoformat(),
    }

    result.update(
        telemetry
    )

    return result


def _severity_rank(
    level: str,
) -> int:

    return {
        "normal": 0,
        "watch": 1,
        "warning": 2,
        "critical": 3,
        "very_high": 4,
    }.get(
        str(level).strip().lower(),
        0,
    )


def _build_sensor_alert_message(
    data: SensorData,
) -> str:

    level = (
        data.alert_level
        .strip()
        .upper()
    )

    reasons = []

    if (
        data.tilt_change_deg is not None
        and abs(
            data.tilt_change_deg
        ) >= 0.5
    ):
        reasons.append(
            f"tilt change "
            f"{data.tilt_change_deg:+.2f}°"
        )

    if (
        data.tilt_rate_dph is not None
        and abs(
            data.tilt_rate_dph
        ) >= 5.0
    ):
        reasons.append(
            f"tilt rate "
            f"{data.tilt_rate_dph:+.1f}°/h"
        )

    if (
        data.tilt_sudden_change_10s_deg
        is not None
        and abs(
            data.tilt_sudden_change_10s_deg
        ) >= 0.5
    ):
        reasons.append(
            f"10s tilt change "
            f"{data.tilt_sudden_change_10s_deg:+.2f}°"
        )

    if (
        data.movement_ratio is not None
        and data.movement_ratio >= 3.0
    ):
        reasons.append(
            f"movement ratio "
            f"{data.movement_ratio:.1f}x"
        )

    if (
        data.moisture_change_pct
        is not None
        and data.moisture_change_pct >= 2.0
    ):
        reasons.append(
            f"soil change "
            f"{data.moisture_change_pct:.1f}%"
        )

    if (
        data.distance_change_cm
        is not None
        and abs(
            data.distance_change_cm
        ) >= 0.75
    ):
        reasons.append(
            f"distance change "
            f"{data.distance_change_cm:+.2f} cm"
        )

    if not reasons:
        reasons.append(
            "ESP32 edge-condition logic "
            "reported an active alert"
        )

    return (
        f"Giri-Rakshak {level} SENSOR ALERT: "
        + "; ".join(reasons)
        + f". Zone: {data.sensor_id}"
    )


def _send_sensor_notifications(
    db: Session,
    alert: Alert,
) -> dict:

    sms_result = (
        send_configured_alert(
            alert.message
        )
    )

    official_devices = (
        db.query(
            DeviceToken
        )
        .filter(
            DeviceToken.role
            == "official"
        )
        .all()
    )

    push_results = []

    for device in official_devices:

        try:

            result = (
                send_push_notification(
                    token=device.token,

                    title=(
                        "Giri Rakshak: "
                        + alert.risk_level.upper()
                    ),

                    body=alert.message,

                    data={
                        "zone_id":
                            alert.zone_id,

                        "risk_level":
                            alert.risk_level,

                        "source":
                            "sensor",
                    },
                )
            )

            push_results.append({

                "device_id":
                    device.id,

                "success":
                    bool(
                        result.get(
                            "success"
                        )
                    ),

                "message_id":
                    result.get(
                        "message_id"
                    ),

                "error":
                    result.get(
                        "error"
                    ),
            })

        except Exception as exc:

            push_results.append({

                "device_id":
                    device.id,

                "success":
                    False,

                "message_id":
                    None,

                "error":
                    str(exc),
            })

    return {

        "sms_result":
            sms_result,

        "push_results":
            push_results,
    }


def _sync_sensor_alert(
    db: Session,
    data: SensorData,
) -> dict:

    current_level = (
        data.alert_level
        .strip()
        .lower()
    )

    # NORMAL closes only active sensor alerts.
    if current_level in {
        "",
        "normal",
        "none",
    }:

        closed = (
            db.query(
                Alert
            )
            .filter(

                Alert.zone_id
                == data.sensor_id,

                Alert.source
                == "sensor",

                Alert.is_active.is_(
                    True
                ),
            )
            .update(
                {
                    "is_active":
                        False,
                },
                synchronize_session=False,
            )
        )

        return {
            "created": False,
            "closed": int(closed),
            "alert": None,
        }

    active = (
        db.query(
            Alert
        )
        .filter(

            Alert.zone_id
            == data.sensor_id,

            Alert.source
            == "sensor",

            Alert.is_active.is_(
                True
            ),
        )
        .order_by(
            Alert.id.desc()
        )
        .first()
    )

    # Same level = same event.
    # Do NOT create another alert.
    if (
        active
        and
        (
            active.risk_level
            or ""
        ).lower()
        == current_level
    ):

        return {
            "created": False,
            "closed": 0,
            "alert": active,
        }

    # Severity changed.
    if active:
        active.is_active = False

    alert = Alert(

        zone_id=
            data.sensor_id,

        risk_level=
            current_level,

        source=
            "sensor",

        message=
            _build_sensor_alert_message(
                data
            ),

        is_active=
            True,

        timestamp=
            data.timestamp,
    )

    db.add(
        alert
    )

    db.flush()

    notification_result = (
        _send_sensor_notifications(
            db,
            alert,
        )
    )

    return {

        "created":
            True,

        "closed":
            1 if active else 0,

        "alert":
            alert,

        "notification_result":
            notification_result,
    }


@router.post(
    "/sensor-data"
)
def receive_sensor_data(

    data: SensorData,

    db: Session =
        Depends(get_db),
):

    displacement = (
        data.displacement_cm
    )

    if (
        displacement is None
        and data.distance_change_cm
        is not None
    ):

        displacement = abs(
            data.distance_change_cm
        )

    reading = SensorReading(

        sensor_id=
            data.sensor_id,

        lat=
            data.lat,

        lon=
            data.lon,

        tilt_deg=
            data.tilt_deg,

        moisture_pct=
            data.moisture_pct,

        displacement_cm=
            (
                displacement
                if displacement is not None
                else 0.0
            ),

        timestamp=
            data.timestamp,

        telemetry_json=
            json.dumps(
                _telemetry_dict(
                    data
                ),
                separators=(
                    ",",
                    ":",
                ),
            ),

        alert_level=
            data.alert_level
            .strip()
            .lower(),

        system_state=
            data.system_state
            .strip()
            .lower(),
    )

    db.add(
        reading
    )

    alert_result = (
        _sync_sensor_alert(
            db,
            data,
        )
    )

    db.commit()

    db.refresh(
        reading
    )

    response = {

        "status":
            "received",

        "sensor_id":
            data.sensor_id,

        "alert_created":
            bool(
                alert_result.get(
                    "created"
                )
            ),

        "active_alert_level":
            data.alert_level
            .strip()
            .lower(),

        "system_state":
            data.system_state
            .strip()
            .lower(),

        "reading":
            _reading_payload(
                reading
            ),
    }

    if (
        alert_result.get(
            "alert"
        )
        is not None
    ):

        alert = (
            alert_result[
                "alert"
            ]
        )

        response["alert"] = {

            "id":
                alert.id,

            "risk_level":
                alert.risk_level,

            "source":
                alert.source,

            "message":
                alert.message,

            "is_active":
                alert.is_active,

            "timestamp":
                (
                    alert.timestamp.isoformat()
                    if alert.timestamp
                    else None
                ),
        }

    return response


@router.get(
    "/sensor-data/latest"
)
def get_latest_sensor_data(
    db: Session =
        Depends(get_db),
):

    reading = (
        db.query(
            SensorReading
        )
        .order_by(
            SensorReading.id.desc()
        )
        .first()
    )

    if reading is None:

        return {
            "status":
                "no_data",

            "reading":
                None,
        }

    return {

        "status":
            "ok",

        "reading":
            _reading_payload(
                reading
            ),
    }


@router.get(
    "/sensor-data/latest/{sensor_id}"
)
def get_latest_sensor_data_for_zone(

    sensor_id: str,

    db: Session =
        Depends(get_db),
):

    reading = (
        db.query(
            SensorReading
        )
        .filter(
            SensorReading.sensor_id
            == sensor_id
        )
        .order_by(
            SensorReading.id.desc()
        )
        .first()
    )

    if reading is None:

        return {

            "status":
                "no_data",

            "reading":
                None,

            "sensor_id":
                sensor_id,
        }

    return {

        "status":
            "ok",

        "reading":
            _reading_payload(
                reading
            ),
    }
