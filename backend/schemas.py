from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


Role = Literal["citizen", "official"]
ReportStatus = Literal["submitted", "verified", "in_progress", "resolved", "rejected"]
Severity = Literal["low", "medium", "high", "critical"]


class RegisterCitizen(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    phone: str | None = Field(default=None, max_length=20)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
    role: Role


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: EmailStr
    phone: str | None
    role: Role
    department: str | None
    area: str | None
    is_active: bool


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    zone_id: str | None
    lat: float
    lon: float
    photo_path: str | None
    description: str | None
    category: str
    severity: str
    status: str
    assigned_official_id: int | None
    resolution_note: str | None
    reported_at: datetime
    updated_at: datetime


class StatusUpdateRequest(BaseModel):
    status: ReportStatus
    note: str | None = Field(default=None, max_length=1000)


class AssignReportRequest(BaseModel):
    official_id: int | None = None


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    report_id: int | None
    alert_id: int | None
    notification_type: str
    title: str
    message: str
    severity: str
    is_read: bool
    created_at: datetime


class DashboardSummary(BaseModel):
    total_reports: int
    submitted_reports: int
    verified_reports: int
    in_progress_reports: int
    resolved_reports: int
    rejected_reports: int
    high_priority_reports: int
    active_alerts: int
    zones_with_data: int
    unread_notifications: int
