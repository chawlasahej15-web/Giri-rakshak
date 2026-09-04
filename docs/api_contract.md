# API Integration Contract

> **Single Source of Truth**: Every team member must code against the exact endpoint paths, HTTP methods, request parameters, and response structures defined below. Do not change key names without updating this document and notifying the team.

---

## Endpoints Summary

| Endpoint | Method | Called By | Request Payload / Params | Response Payload |
| :--- | :--- | :--- | :--- | :--- |
| `/api/sensor-data` | `POST` | ESP32 rig, `simulate_sensors.py` | JSON Body | `{"status": string, "reactive_alert_triggered": boolean}` |
| `/api/risk-zones` | `GET` | Dashboard (`frontend/dashboard.js`) | Query Params (optional) | Array of Risk Zone Objects |
| `/api/citizen-report` | `POST` | `frontend/report.html` | Form Data / JSON | `{"status": string, "report_id": string}` |
| `/api/alerts/recent` | `GET` | Dashboard (`frontend/dashboard.js`) | None | Array of Alert Objects |
| `/api/trigger-alert` | *Internal* | Backend risk-scoring logic (`alerts/send_sms.py`) | JSON Body | `{"status": "sent" \| "failed"}` |

---

## Detailed Endpoint Specifications

### 1. Submit Sensor Data
* **Endpoint:** `/api/sensor-data`
* **Method:** `POST`
* **Called By:** Hardware ESP32 Rig / `simulate_sensors.py`
* **Request Body:**
```json
{
  "sensor_id": "ESP32_ZONE_01",
  "lat": 30.3165,
  "lon": 78.0322,
  "tilt_deg": 12.4,
  "moisture_pct": 45.2,
  "displacement_cm": 1.2,
  "timestamp": "2026-09-04T16:00:00Z"
}