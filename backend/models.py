from sqlalchemy import Column, Integer, Float, String, DateTime, Text
from database import Base


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    tilt_deg = Column(Float, nullable=False)
    moisture_pct = Column(Float, nullable=False)
    displacement_cm = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)


class Zone(Base):
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(String, unique=True, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(String, nullable=False)
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String, nullable=False)
    top_factors = Column(Text, nullable=True)
    timestamp = Column(DateTime, nullable=False)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(String, nullable=False)
    risk_level = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False)


class CitizenReport(Base):
    __tablename__ = "citizen_reports"

    id = Column(Integer, primary_key=True, index=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    photo_path = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    timestamp = Column(DateTime, nullable=False)