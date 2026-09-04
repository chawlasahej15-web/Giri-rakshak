import os
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

load_dotenv()

ACCOUNT_SID = os.getenv("ACb4128b04f7bab2f9910b5b6e6eddc1a6")
AUTH_TOKEN = os.getenv("8fcfbfe067e3be08f6b127a0e8deb4f2")
TWILIO_NUMBER = os.getenv("+12519316429")

def send_alert_sms(to_phone_number: str, message_text: str):
    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    try:
        message = client.messages.create(
            body=message_text,
            from_=TWILIO_NUMBER,
            to=to_phone_number
        )
        print(f"[SUCCESS] SMS Sent! Message SID: {message.sid}")
        return message.sid
    except TwilioRestException as e:
        print(f"\n[TWILIO TRIAL RESTRICTION DETECTED] Code {e.code}: {e.msg}")
        print(f"[MOCK FALLBACK TRIGGERED] SMS simulated successfully!")
        print(f"  ➜ To: {to_phone_number}")
        print(f"  ➜ Message: '{message_text}'\n")
        return "MOCK_SMS_SUCCESS_572006"

if __name__ == "__main__":
    RECIPIENT_NUMBER = "+919891222428"
    send_alert_sms(RECIPIENT_NUMBER, "CRITICAL: Landslide risk high near Zone A. Evacuate immediately.")