from datetime import datetime

from database import Base, SessionLocal, engine
from models import Zone, RiskScore

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Create a demo zone
zone = Zone(
    zone_id="AIZAWL-001",
    lat=23.7271,
    lon=92.7176
)

db.add(zone)

# Create a demo risk score
risk = RiskScore(
    zone_id="AIZAWL-001",
    risk_score=68.0,
    risk_level="moderate",
    top_factors='["High rainfall", "Slope instability", "Elevated soil moisture"]',
    timestamp=datetime.now()
)

db.add(risk)

db.commit()
db.close()

print("Demo zone and risk score added successfully.")