import os
from datetime import datetime, timedelta, timezone
from math import cos, radians

import requests
from dotenv import dotenv_values
from google import genai
from google.genai import types
from sqlalchemy import func
from sqlalchemy.orm import Session
from tinyfish import TinyFish

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

# ==============================================================================
# TinyFish + Gemini Conversational AI Integration
# ==============================================================================

def get_chatbot_response(user_query: str, user_role: str = "citizen", context_data: dict = None) -> dict:
    # 1. Bypass OS environment caching entirely by parsing the .env file directly
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    local_env = dotenv_values(env_path)
    
    tinyfish_key = local_env.get("sk-tinyfish-EDxDSSFKcTfBskFmdwcWumaqzofTgPd7")
    gemini_key = local_env.get("AQ.Ab8RN6K4p1qDlyHIanf7_yqZRnA_kBN9MPJ603ynzQVUJT7dQg")

    # Final hackathon fallback: If even this fails, uncomment the two lines below 
    # and paste your raw keys inside the quotes so you can finish your demo.
    # tinyfish_key = "sk-tinyfish-..."
    # gemini_key = "AQ..."

    if not tinyfish_key:
        return {"reply": f"Still failing to read keys. Please uncomment the fallback variables in services.py."}

    ai_client = genai.Client(api_key=gemini_key) if gemini_key else None

    try:
        tf_client = TinyFish(api_key=tinyfish_key)

        if user_role in ["official", "admin"] and any(kw in user_query.lower() for kw in ["dispatch", "report", "trigger", "alert", "portal"]):
            coords = context_data.get("coords", "27.33, 88.61") if context_data else "27.33, 88.61"
            agent_res = requests.post(
                "https://agent.tinyfish.ai/v1/automation/run",
                headers={"X-API-Key": tinyfish_key, "Content-Type": "application/json"},
                json={
                    "url": "https://ndma.gov.in",
                    "goal": f"Navigate to emergency reporting portal and submit alert for coordinates {coords} based on query: {user_query}"
                },
                timeout=30
            )
            status = agent_res.json().get("status", "Submitted") if agent_res.status_code == 200 else "Queued"
            return {"reply": f"🚨 **Emergency Action Triggered via Web Agent**\n\nTarget Coordinates: `{coords}`\nDispatch Status: `{status}`"}

        clean_input = user_query.lower().replace("i live in", "").strip()
        search_query = f"{clean_input} landslide weather road condition North East India"

        raw_retrieval_text = ""
        sources = []
        try:
            search_res = tf_client.search.query(
                query=search_query,
                recency_minutes=1440
            )
            if hasattr(search_res, "results") and search_res.results:
                raw_retrieval_text = "\n".join([f"- {r.title}: {r.snippet}" for r in search_res.results[:3]])
                sources = [r.url for r in search_res.results[:3] if hasattr(r, "url")]
        except Exception:
            raw_retrieval_text = "No live search results available."

        if ai_client:
            try:
                system_instruction = (
                    "You are Giri Rakshak AI, an empathetic and authoritative disaster safety assistant for North East India. "
                    "Synthesize the search context into concise safety advice. Keep your tone supportive and actionable."
                )
                response = ai_client.models.generate_content(
                    model='gemini-3.5-flash-lite',
                    contents=f"User Query: {user_query}\nRetrieved Search Context:\n{raw_retrieval_text}",
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.3
                    )
                )
                return {"reply": response.text.strip(), "sources": sources}
            except Exception as gemini_err:
                if any(err_code in str(gemini_err) for err_code in ["429", "RESOURCE_EXHAUSTED", "Quota"]):
                    return {"reply": f"**Giri Rakshak Live Ground Updates:**\n\n{raw_retrieval_text}", "sources": sources}
                raise gemini_err

        return {"reply": f"**Giri Rakshak Advisory Update:**\n\n{raw_retrieval_text}", "sources": sources}

    except Exception as e:
        return {"reply": f"Giri Rakshak AI service error: {str(e)}"}