# Giri-Rakshak Backend v2

FastAPI backend for citizen reporting + official response + sensor/ML risk monitoring.

## Main flow

Citizen registers/login -> submits photo + description + GPS -> report stored in PostgreSQL -> officials receive notification -> official verifies/assigns/updates -> citizen sees status notification.

ESP32 -> `/api/sensor-data` -> raw reading + ML risk score -> alert cooldown -> official notification.

## Important endpoints

### Auth
- `POST /api/auth/register/citizen`
- `POST /api/auth/login` with `{ "email", "password", "role": "citizen|official" }`
- `GET /api/auth/me`

### Citizen
- `POST /api/reports` multipart: `lat`, `lon`, `description`, `category`, `severity`, optional `photo`
- `GET /api/citizen/reports`
- `GET /api/notifications`
- `GET /api/notifications/unread-count`
- `PATCH /api/notifications/{id}/read`

### Official
- `GET /api/official/dashboard`
- `GET /api/official/reports`
- `GET /api/official/reports/{id}`
- `PATCH /api/official/reports/{id}/status`
- `PATCH /api/official/reports/{id}/assign`
- `GET /api/official/zones/summary`
- `GET /api/risk-zones`
- `GET /api/alerts/recent`

### Hardware / ML
- `POST /api/sensor-data`
- `GET /api/sensor-data/latest`
- `GET /api/sensor-data/latest/{sensor_id}`

## Local setup

```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8000
```

For quick local testing without PostgreSQL, omit `DATABASE_URL`; the code falls back to SQLite. For the SIH final/demo deployment, set `DATABASE_URL` to PostgreSQL.

## Seed an official demo account

```bash
python seed.py --email official@girirakshak.local --password Demo@12345
```

## SQLite -> PostgreSQL migration

First set the target PostgreSQL `DATABASE_URL`, then run:

```bash
python migrate_sqlite_to_postgres.py --sqlite ./giri_rakshak.db
```

The migration copies the old sensor, zone, risk, alert and citizen-report records and adds safe defaults for the new fields.

## Deployment note

Local uploads are served at `/uploads/...`. A production deployment on an ephemeral filesystem should later switch the storage layer to object storage (S3/Cloudinary/etc.) and keep only the URL in PostgreSQL.
