import os
from pathlib import Path

from dotenv import load_dotenv
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client


# Always load the project's root .env file
ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ENV_FILE)


TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
ALERT_RECIPIENT_PHONE = os.getenv("ALERT_RECIPIENT_PHONE")


def twilio_configured() -> bool:
    return all(
        [
            TWILIO_ACCOUNT_SID,
            TWILIO_AUTH_TOKEN,
            TWILIO_PHONE_NUMBER,
        ]
    )


def send_sms(
    phone_number: str,
    message: str,
):
    """
    Send an SMS through Twilio.

    The message is passed in by the caller and is not modified here.

    Returns:
        {
            "success": bool,
            "sid": str | None,
            "error": str | None,
        }
    """

    if not twilio_configured():
        return {
            "success": False,
            "sid": None,
            "error": (
                "Twilio is not configured. "
                "Check TWILIO_ACCOUNT_SID, "
                "TWILIO_AUTH_TOKEN and "
                "TWILIO_PHONE_NUMBER in .env."
            ),
        }

    if not phone_number:
        return {
            "success": False,
            "sid": None,
            "error": "Recipient phone number is missing.",
        }

    try:
        client = Client(
            TWILIO_ACCOUNT_SID,
            TWILIO_AUTH_TOKEN,
        )

        twilio_message = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number,
        )

        print(
            f"[TWILIO] SMS sent successfully: "
            f"{twilio_message.sid}"
        )

        return {
            "success": True,
            "sid": twilio_message.sid,
            "error": None,
        }

    except TwilioRestException as exc:

        print(
            f"[TWILIO] SMS failed: "
            f"code={exc.code}, message={exc.msg}"
        )

        return {
            "success": False,
            "sid": None,
            "error": str(exc.msg),
        }

    except Exception as exc:

        print(
            f"[TWILIO] Unexpected error: {exc}"
        )

        return {
            "success": False,
            "sid": None,
            "error": str(exc),
        }


def send_configured_alert(message: str):
    """
    Send an alert to the recipient configured in .env.
    """

    return send_sms(
        ALERT_RECIPIENT_PHONE,
        message,
    )
