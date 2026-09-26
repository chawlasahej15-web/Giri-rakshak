import firebase_admin
from firebase_admin import credentials, messaging
from pathlib import Path
import json
import os


BASE_DIR = Path(__file__).resolve().parent
SERVICE_ACCOUNT_FILE = BASE_DIR / "firebase-service-account.json"


def initialize_firebase():
    if firebase_admin._apps:
        return True

    service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

    try:
        if service_account_json:
            service_account_info = json.loads(service_account_json)
            cred = credentials.Certificate(service_account_info)
            firebase_admin.initialize_app(cred)
            print("Firebase initialized from environment.")
            return True

        if SERVICE_ACCOUNT_FILE.exists():
            cred = credentials.Certificate(str(SERVICE_ACCOUNT_FILE))
            firebase_admin.initialize_app(cred)
            print("Firebase initialized from local service-account file.")
            return True

        print("Firebase credentials not configured. Push notifications disabled.")
        return False

    except Exception as exc:
        print("Firebase initialization failed:", repr(exc))
        return False


def send_push_notification(
    token: str,
    title: str,
    body: str,
    data: dict | None = None,
):
    if not initialize_firebase():
        return {
            "success": False,
            "message_id": None,
            "error": "Firebase is not configured.",
        }

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
