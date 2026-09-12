from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, Index
from sqlalchemy.orm import relationship

from database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, index=True)  # citizen | official
    department = Column(String(120), nullable=True)
    area = Column(String(120), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    reports = relationship(
        "CitizenReport",
        foreign_keys="CitizenReport.user_id",
        back_populates="reporter",
    )
    assigned_reports = relationship(
        "CitizenReport",
        foreign_keys="CitizenReport.assigned_official_id",
        back_populates="assigned_official",
    )
    notifications = relationship("Notification", back_populates="user")


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String(80), nullable=False, index=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    tilt_deg = Column(Float, nullable=False)
    moisture_pct = Column(Float, nullable=False)
    displacement_cm = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)

    __table_args__ = (
        Index("ix_sensor_readings_sensor_time", "sensor_id", "timestamp"),
    )


class Zone(Base):
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(String(80), unique=True, nullable=False, index=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)

    reports = relationship("CitizenReport", back_populates="zone")


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(String(80), nullable=False, index=True)
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String(30), nullable=False, index=True)
    top_factors = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(String(80), nullable=False, index=True)
    risk_level = Column(String(30), nullable=False, index=True)
    source = Column(String(30), nullable=False, default="system")  # sensor | ml | manual | citizen
    message = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)


class CitizenReport(Base):
    __tablename__ = "citizen_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    zone_id = Column(String(80), ForeignKey("zones.zone_id"), nullable=True, index=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    photo_path = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    category = Column(String(40), nullable=False, default="landslide")
    severity = Column(String(20), nullable=False, default="medium", index=True)
    status = Column(String(30), nullable=False, default="submitted", index=True)
    assigned_official_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    resolution_note = Column(Text, nullable=True)
    reported_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    reporter = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="reports",
    )
    assigned_official = relationship(
        "User",
        foreign_keys=[assigned_official_id],
        back_populates="assigned_reports",
    )
    zone = relationship("Zone", back_populates="reports")
    updates = relationship(
        "ReportUpdate",
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="ReportUpdate.created_at.desc()",
    )

    __table_args__ = (
        Index("ix_citizen_reports_status_severity", "status", "severity"),
        Index("ix_citizen_reports_zone_status", "zone_id", "status"),
    )


class ReportUpdate(Base):
    __tablename__ = "report_updates"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("citizen_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    old_status = Column(String(30), nullable=True)
    new_status = Column(String(30), nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    report = relationship("CitizenReport", back_populates="updates")
    actor = relationship("User", foreign_keys=[actor_user_id])


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    report_id = Column(Integer, ForeignKey("citizen_reports.id", ondelete="SET NULL"), nullable=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id", ondelete="SET NULL"), nullable=True, index=True)
    notification_type = Column(String(40), nullable=False, index=True)
    title = Column(String(180), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False, default="info")
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    user = relationship("User", back_populates="notifications")
