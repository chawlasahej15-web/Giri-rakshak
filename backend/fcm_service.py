import firebase_admin
from firebase_admin import credentials, messaging
from pathlib import Path
import json
import os


BASE_DIR = Path(__file__).resolve().parent
SERVICE_ACCOUNT_FILE = BASE_DIR / "firebase-service-account.json"


def initialize_firebase():
    if firebase_admin._apps:
        return

    # Render: read service account JSON from environment variable
    service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

    if service_account_json:
        service_account_info = json.loads(service_account_json)
        cred = credentials.Certificate(service_account_info)

    # Local development: use the local JSON file
    elif SERVICE_ACCOUNT_FILE.exists():
        cred = credentials.Certificate(str(SERVICE_ACCOUNT_FILE))

    else:
        raise FileNotFoundError(
            "Firebase credentials missing. Set FIREBASE_SERVICE_ACCOUNT_JSON "
            "on Render or provide firebase-service-account.json locally."
        )

    firebase_admin.initialize_app(cred)


initialize_firebase()


def send_push_notification(
    token: str,
    title: str,
    body: str,
    data: dict | None = None,
):
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data={str(k): str(v) for k, v in (data or {}).items()},
        token=token,
    )

    response = messaging.send(message)

    return {
        "success": True,
        "message_id": response,
    }