from collections import defaultdict
from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.assignment import Assignment
from app.models.satisfaction import Satisfaction
from app.models.schedule_week import ScheduleWeek
from app.models.shift import Shift
from app.models.user import User
from app.models.user_message import UserMessage
from app.services.assignment_service import run_assignment_algorithm
from app.services.satisfaction_service import calculate_satisfaction, get_latest_satisfaction_map
from app.services.user_service import get_user_by_username
from app.services.week_service import get_or_create_next_week, get_week_shifts

router = APIRouter(prefix="/assignments", tags=["assignments"])
templates = Jinja2Templates(directory="app/templates")

DAY_NAMES = ["שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת", "ראשון"]


def _admin_access(request: Request):
    username = request.cookies.get("username")
    role = request.cookies.get("role")
    return username and role in ["admin", "shift_manager"]


def _get_selected_week(db: Session, request: Request):
    week_id = request.query_params.get("week_id")
    if week_id:
        try:
            found = db.query(ScheduleWeek).filter(ScheduleWeek.id == int(week_id)).first()
            if found:
                return found
        except ValueError:
            pass
    return get_or_create_next_week(db)


@router.get("/admin", response_class=HTMLResponse)
def assignments_admin_page(request: Request, db: Session = Depends(get_db)):
    if not _admin_access(request):
        return RedirectResponse(url="/auth/login", status_code=303)

    week = _get_selected_week(db, request)
    shifts = get_week_shifts(db, week.id)
    users = db.query(User).filter(User.is_active == True).order_by(User.full_name.asc()).all()
    assignments = db.query(Assignment).filter(Assignment.week_id == week.id).all()
    satisfaction_map = get_latest_satisfaction_map(db, week.id)
    weeks_history = db.query(ScheduleWeek).order_by(ScheduleWeek.week_start_date.desc()).limit(12).all()

    users_map = {u.id: u for u in users}
    shift_assignments = defaultdict(list)
    for a in assignments:
        u = users_map.get(a.user_id)
        shift_assignments[a.shift_id].append({
            "assignment_id": a.id,
            "user_id": a.user_id,
            "user_name": u.full_name if u else f"User {a.user_id}",
            "locked": a.locked,
        })

    days = []
    seen_dates = set()
    for shift in shifts:
        if shift.shift_date not in seen_dates:
            seen_dates.add(shift.shift_date)
            days.append({
                "date_obj": shift.shift_date,
                "day_name": DAY_NAMES[shift.shift_date.weekday()],
                "date_text": shift.shift_date.strftime("%d/%m/%Y"),
            })

    table_rows = []
    for shift_type, shift_type_label in [("day", "יום"), ("night", "לילה")]:
        cells = []
        for day in days:
            current_shift = next((s for s in shifts if s.shift_date == day["date_obj"] and s.shift_type == shift_type), None)
            if current_shift:
                cells.append({
                    "shift_id": current_shift.id,
                    "capacity": current_shift.capacity,
                    "assigned_users": shift_assignments.get(current_shift.id, []),
                })
            else:
                cells.append({"shift_id": None, "capacity": 0, "assigned_users": []})
        table_rows.append({"shift_type_label": shift_type_label, "cells": cells})

    return templates.TemplateResponse(
        request,
        "assignments_admin.html",
        {
            "week": week,
            "weeks_history": weeks_history,
            "days": days,
            "table_rows": table_rows,
            "users": users,
            "satisfaction_map": satisfaction_map,
            "success": request.query_params.get("success"),
        },
    )


@router.post("/run")
def run_assignments(request: Request, week_id: int = Form(...), db: Session = Depends(get_db)):
    if not _admin_access(request):
        return RedirectResponse(url="/auth/login", status_code=303)

    week = db.query(ScheduleWeek).filter(ScheduleWeek.id == week_id).first()
    if not week:
        return RedirectResponse(url="/assignments/admin", status_code=303)

    run_assignment_algorithm(db, week.id)
    return RedirectResponse(url=f"/assignments/admin?week_id={week.id}&success=ran", status_code=303)


@router.post("/publish")
def publish_assignments(request: Request, week_id: int = Form(...), db: Session = Depends(get_db)):
    if not _admin_access(request):
        return RedirectResponse(url="/auth/login", status_code=303)

    week = db.query(ScheduleWeek).filter(ScheduleWeek.id == week_id).first()
    if not week:
        return RedirectResponse(url="/assignments/admin", status_code=303)

    calculate_satisfaction(db, week.id)
    week.status = "published"
    week.published_at = datetime.utcnow()
    db.commit()

    return RedirectResponse(url=f"/assignments/admin?week_id={week.id}&success=published", status_code=303)


@router.post("/override")
def update_satisfaction_override(
    request: Request,
    week_id: int = Form(...),
    user_id: int = Form(...),
    override_value: str = Form(""),
    db: Session = Depends(get_db),
):
    if not _admin_access(request):
        return RedirectResponse(url="/auth/login", status_code=303)

    user = db.query(User).filter(User.id == user_id).first()
    if user:
        cleaned = override_value.strip()
        user.satisfaction_override = int(cleaned) if cleaned else None
        db.commit()

    return RedirectResponse(url=f"/assignments/admin?week_id={week_id}&success=override_saved", status_code=303)


@router.post("/add")
def add_assignment_manually(
    request: Request,
    week_id: int = Form(...),
    shift_id: int = Form(...),
    user_id: int = Form(...),
    db: Session = Depends(get_db),
):
    if not _admin_access(request):
        return RedirectResponse(url="/auth/login", status_code=303)

    exists = db.query(Assignment).filter(
        Assignment.week_id == week_id,
        Assignment.shift_id == shift_id,
        Assignment.user_id == user_id
    ).first()

    if not exists:
        db.add(Assignment(
            week_id=week_id,
            shift_id=shift_id,
            user_id=user_id,
            locked=True,
        ))
        db.commit()

    return RedirectResponse(url=f"/assignments/admin?week_id={week_id}&success=manual_added", status_code=303)


@router.post("/remove")
def remove_assignment_manually(
    request: Request,
    week_id: int = Form(...),
    assignment_id: int = Form(...),
    db: Session = Depends(get_db),
):
    if not _admin_access(request):
        return RedirectResponse(url="/auth/login", status_code=303)

    row = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if row:
        db.delete(row)
        db.commit()

    return RedirectResponse(url=f"/assignments/admin?week_id={week_id}&success=manual_removed", status_code=303)


@router.post("/toggle-lock")
def toggle_lock_assignment(
    request: Request,
    week_id: int = Form(...),
    assignment_id: int = Form(...),
    db: Session = Depends(get_db),
):
    if not _admin_access(request):
        return RedirectResponse(url="/auth/login", status_code=303)

    row = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if row:
        row.locked = not row.locked
        db.commit()

    return RedirectResponse(url=f"/assignments/admin?week_id={week_id}&success=lock_toggled", status_code=303)


@router.get("", response_class=HTMLResponse)
def assignments_user_page(request: Request, db: Session = Depends(get_db)):
    username = request.cookies.get("username")
    if not username:
        return RedirectResponse(url="/auth/login", status_code=303)

    current_user = get_user_by_username(db, username)
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)

    week = get_or_create_next_week(db)

    if week.status != "published":
        return templates.TemplateResponse(
            request,
            "assignments_user.html",
            {
                "week": week,
                "is_published": False,
                "assigned_shifts": [],
                "success": request.query_params.get("success"),
            },
        )

    rows = (
        db.query(Assignment, Shift)
        .join(Shift, Shift.id == Assignment.shift_id)
        .filter(Assignment.week_id == week.id, Assignment.user_id == current_user.id)
        .order_by(Shift.shift_date.asc(), Shift.shift_type.asc())
        .all()
    )

    assigned_shifts = []
    for assignment, shift in rows:
        assigned_shifts.append({
            "day_name": DAY_NAMES[shift.shift_date.weekday()],
            "date": shift.shift_date.strftime("%d/%m/%Y"),
            "shift_type": "יום" if shift.shift_type == "day" else "לילה",
            "locked": assignment.locked,
        })

    return templates.TemplateResponse(
        request,
        "assignments_user.html",
        {
            "week": week,
            "is_published": True,
            "assigned_shifts": assigned_shifts,
            "success": request.query_params.get("success"),
        },
    )


@router.post("/message")
def send_message(
    request: Request,
    message: str = Form(...),
    db: Session = Depends(get_db),
):
    username = request.cookies.get("username")
    if not username:
        return RedirectResponse(url="/auth/login", status_code=303)

    current_user = get_user_by_username(db, username)
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)

    week = get_or_create_next_week(db)
    db.add(UserMessage(user_id=current_user.id, week_id=week.id, message=message.strip()))
    db.commit()

    return RedirectResponse(url="/assignments?success=message_sent", status_code=303)
