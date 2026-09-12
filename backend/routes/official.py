from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from auth import require_roles
from database import get_db
from models import Alert, CitizenReport, Notification, ReportUpdate, RiskScore, User, Zone
from schemas import AssignReportRequest, DashboardSummary, ReportOut, StatusUpdateRequest
from services import notify_citizen_report_status, utcnow

router = APIRouter(prefix="/api/official", tags=["Official Dashboard"])


@router.get("/dashboard", response_model=DashboardSummary)
def dashboard(
    current_user: User = Depends(require_roles("official")),
    db: Session = Depends(get_db),
):
    totals = db.query(func.count(CitizenReport.id)).scalar() or 0
    unread = (
        db.query(func.count(Notification.id))
        .filter(Notification.user_id == current_user.id, Notification.is_read.is_(False))
        .scalar()
        or 0
    )
    return DashboardSummary(
        total_reports=totals,
        submitted_reports=db.query(func.count(CitizenReport.id)).filter(CitizenReport.status == "submitted").scalar() or 0,
        verified_reports=db.query(func.count(CitizenReport.id)).filter(CitizenReport.status == "verified").scalar() or 0,
        in_progress_reports=db.query(func.count(CitizenReport.id)).filter(CitizenReport.status == "in_progress").scalar() or 0,
        resolved_reports=db.query(func.count(CitizenReport.id)).filter(CitizenReport.status == "resolved").scalar() or 0,
        rejected_reports=db.query(func.count(CitizenReport.id)).filter(CitizenReport.status == "rejected").scalar() or 0,
        high_priority_reports=db.query(func.count(CitizenReport.id)).filter(CitizenReport.severity.in_(["high", "critical"]), CitizenReport.status.notin_(["resolved", "rejected"])).scalar() or 0,
        active_alerts=db.query(func.count(Alert.id)).filter(Alert.is_active.is_(True)).scalar() or 0,
        zones_with_data=db.query(func.count(func.distinct(RiskScore.zone_id))).scalar() or 0,
        unread_notifications=unread,
    )


@router.get("/reports", response_model=list[ReportOut])
def official_reports(
    status_filter: str | None = Query(default=None, alias="status"),
    category: str | None = None,
    severity: str | None = None,
    zone_id: str | None = None,
    assigned_to_me: bool = False,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(require_roles("official")),
    db: Session = Depends(get_db),
):
    query = db.query(CitizenReport)
    if status_filter:
        query = query.filter(CitizenReport.status == status_filter)
    if category:
        query = query.filter(CitizenReport.category == category)
    if severity:
        query = query.filter(CitizenReport.severity == severity)
    if zone_id:
        query = query.filter(CitizenReport.zone_id == zone_id)
    if assigned_to_me:
        query = query.filter(CitizenReport.assigned_official_id == current_user.id)

    return query.order_by(CitizenReport.reported_at.desc()).offset(offset).limit(limit).all()


@router.get("/reports/{report_id}", response_model=ReportOut)
def get_report(
    report_id: int,
    current_user: User = Depends(require_roles("official")),
    db: Session = Depends(get_db),
):
    del current_user
    report = db.query(CitizenReport).filter(CitizenReport.id == report_id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.patch("/reports/{report_id}/status", response_model=ReportOut)
def update_report_status(
    report_id: int,
    payload: StatusUpdateRequest,
    current_user: User = Depends(require_roles("official")),
    db: Session = Depends(get_db),
):
    report = db.query(CitizenReport).filter(CitizenReport.id == report_id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")

    old_status = report.status
    if old_status == payload.status and not payload.note:
        return report

    report.status = payload.status
    report.updated_at = utcnow()
    if payload.status == "resolved" and payload.note:
        report.resolution_note = payload.note

    db.add(
        ReportUpdate(
            report_id=report.id,
            actor_user_id=current_user.id,
            old_status=old_status,
            new_status=payload.status,
            note=payload.note,
        )
    )

    severity = "info" if payload.status in {"verified", "in_progress"} else "success"
    if payload.status == "rejected":
        severity = "warning"
    if payload.status == "resolved":
        severity = "success"

    notify_citizen_report_status(
        db,
        report,
        title="Your Giri-Rakshak report was updated",
        message=f"Report #{report.id} status changed from {old_status} to {payload.status}." + (f" Note: {payload.note}" if payload.note else ""),
        severity=severity,
    )

    db.commit()
    db.refresh(report)
    return report


@router.patch("/reports/{report_id}/assign", response_model=ReportOut)
def assign_report(
    report_id: int,
    payload: AssignReportRequest,
    current_user: User = Depends(require_roles("official")),
    db: Session = Depends(get_db),
):
    report = db.query(CitizenReport).filter(CitizenReport.id == report_id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")

    official_id = payload.official_id if payload.official_id is not None else current_user.id
    official = db.query(User).filter(User.id == official_id, User.role == "official", User.is_active.is_(True)).first()
    if official is None:
        raise HTTPException(status_code=400, detail="Invalid official account")

    report.assigned_official_id = official.id
    report.updated_at = utcnow()

    if report.user_id:
        notify_citizen_report_status(
            db,
            report,
            title="Your report has been assigned",
            message=f"Report #{report.id} is now assigned to an official for review.",
        )

    db.commit()
    db.refresh(report)
    return report


@router.get("/zones/summary")
def zone_summary(
    current_user: User = Depends(require_roles("official")),
    db: Session = Depends(get_db),
):
    del current_user
    rows = (
        db.query(
            CitizenReport.zone_id,
            func.count(CitizenReport.id).label("report_count"),
            func.sum(case((CitizenReport.severity == "critical", 1), else_=0)).label("critical_count"),
            func.sum(case((CitizenReport.severity == "high", 1), else_=0)).label("high_count"),
        )
        .filter(CitizenReport.zone_id.isnot(None))
        .group_by(CitizenReport.zone_id)
        .order_by(func.count(CitizenReport.id).desc())
        .all()
    )
    return [
        {
            "zone_id": row.zone_id,
            "report_count": row.report_count,
            "critical_count": int(row.critical_count or 0),
            "high_count": int(row.high_count or 0),
        }
        for row in rows
    ]
