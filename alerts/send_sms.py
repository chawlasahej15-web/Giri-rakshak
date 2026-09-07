"""
Standalone Twilio SMS test for GiriRakshak.
"""

from twilio_service import send_configured_alert


if __name__ == "__main__":

    result = send_configured_alert(
        "GiriRakshak test alert: SMS pipeline is working."
    )

    print(result)
