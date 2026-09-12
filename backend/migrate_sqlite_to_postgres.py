"""One-time migration from the old SQLite schema to the upgraded PostgreSQL schema.

Usage:
    export DATABASE_URL='postgresql+psycopg://...'
    python migrate_sqlite_to_postgres.py --sqlite ./giri_rakshak.db

Old records are preserved where possible. New authentication/report fields receive safe defaults.
"""

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from database import Base, SessionLocal, engine
from models import Alert, CitizenReport, RiskScore, SensorReading, Zone


def parse_dt(value):
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, datetime):
        return value
    text = str(value)
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sqlite", default="./giri_rakshak.db")
    args = parser.parse_args()

    sqlite_path = Path(args.sqlite).resolve()
    if not sqlite_path.exists():
        raise SystemExit(f"SQLite database not found: {sqlite_path}")

    Base.metadata.create_all(bind=engine)
    source = sqlite3.connect(sqlite_path)
    source.row_factory = sqlite3.Row
    target: Session = SessionLocal()

    counts = {}
    try:
        rows = source.execute("SELECT * FROM zones").fetchall()
        for row in rows:
            if target.query(Zone).filter(Zone.zone_id == row["zone_id"]).first():
                continue
            target.add(Zone(zone_id=row["zone_id"], lat=row["lat"], lon=row["lon"]))
        target.commit()
        counts["zones"] = len(rows)

        rows = source.execute("SELECT * FROM sensor_readings").fetchall()
        for row in rows:
            target.add(
                SensorReading(
                    sensor_id=row["sensor_id"],
                    lat=row["lat"],
                    lon=row["lon"],
                    tilt_deg=row["tilt_deg"],
                    moisture_pct=row["moisture_pct"],
                    displacement_cm=row["displacement_cm"],
                    timestamp=parse_dt(row["timestamp"]),
                )
            )
        target.commit()
        counts["sensor_readings"] = len(rows)

        rows = source.execute("SELECT * FROM risk_scores").fetchall()
        for row in rows:
            target.add(
                RiskScore(
                    zone_id=row["zone_id"],
                    risk_score=row["risk_score"],
                    risk_level=row["risk_level"],
                    top_factors=row["top_factors"],
                    timestamp=parse_dt(row["timestamp"]),
                )
            )
        target.commit()
        counts["risk_scores"] = len(rows)

        rows = source.execute("SELECT * FROM alerts").fetchall()
        for row in rows:
            target.add(
                Alert(
                    zone_id=row["zone_id"],
                    risk_level=row["risk_level"],
                    source="system",
                    message=row["message"],
                    is_active=True,
                    timestamp=parse_dt(row["timestamp"]),
                )
            )
        target.commit()
        counts["alerts"] = len(rows)

        rows = source.execute("SELECT * FROM citizen_reports").fetchall()
        for row in rows:
            target.add(
                CitizenReport(
                    user_id=None,
                    zone_id=None,
                    lat=row["lat"],
                    lon=row["lon"],
                    photo_path=row["photo_path"],
                    description=row["description"],
                    category="landslide",
                    severity="medium",
                    status="submitted",
                    reported_at=parse_dt(row["timestamp"]),
                    updated_at=parse_dt(row["timestamp"]),
                )
            )
        target.commit()
        counts["citizen_reports"] = len(rows)

        print(json.dumps({"status": "migrated", "tables": counts}, indent=2))
    finally:
        source.close()
        target.close()


if __name__ == "__main__":
    main()
