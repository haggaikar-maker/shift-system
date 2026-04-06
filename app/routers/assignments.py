from collections import defaultdict

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.assignment import Assignment
from app.models.shift import Shift
from app.models.user import User
from app.models.user_message import UserMessage
from app.services.assignment_service import run_assignment_algorithm
from app.services.satisfaction_service import calculate_satisfaction
from app.services.user_service import get_user_by_username
from app.services.week_service import get_or_create_next_week, get_week_shifts

router = APIRouter(prefix="/assignments", tags=["assignments"])
templates = Jinja2Templates(directory="app/templates")

DAY_NAMES = ["שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת", "ראשון"]


def _admin_access(request: Request):
    username = request.cookies.get("username")
    role = request.cookies.get("role")
    return username and role in ["admin", "shift_manager"]


@router.get("/admin", response_class=HTMLResponse)
def assignments_admin_page(request: Request, db: Session = Depends(get_db)):
    if not _admin_access(request):
        return RedirectResponse(url="/auth/login", status_code=303)

    week = get_or_create_next_week(db)
    shifts = get_week_shifts(db, week.id)

    assignments = db.query(Assignment).filter(Assignment.week_id == week.id).all()
    users = {u.id: u for u in db.query(User).all()}

    shift_assignments = defaultdict(list)
    for a in assignments:
        user = users.get(a.user_id)
        shift_assignments[a.shift_id].append({
            "user_name": user.full_name if user else f"User {a.user_id}",
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
        row_cells = []
        for day in days:
            current_shift = next(
                (
                    s for s in shifts
                    if s.shift_date == day["date_obj"] and s.shift_type == shift_type
                ),
                None,
            )

            if current_shift:
                row_cells.append({
                    "shift_id": current_shift.id,
                    "capacity": current_shift.capacity,
                    "assigned_users": shift_assignments.get(current_shift.id, []),
                })
            else:
                row_cells.append({
                    "shift_id": None,
                    "capacity": 0,
                    "assigned_users": [],
                })

        table_rows.append({
            "shift_type_label": shift_type_label,
            "cells": row_cells,
        })

    return templates.TemplateResponse(
        request,
        "assignments_admin.html",
        {
            "week": week,
            "days": days,
            "table_rows": table_rows,
            "success": request.query_params.get("success"),
        },
    )


@router.get("/run")
def run_assignments(request: Request, db: Session = Depends(get_db)):
    if not _admin_access(request):
        return RedirectResponse(url="/auth/login", status_code=303)

    week = get_or_create_next_week(db)

    run_assignment_algorithm(db, week.id)
    calculate_satisfaction(db, week.id)

    return RedirectResponse(url="/assignments/admin?success=ran", status_code=303)


@router.get("/publish")
def publish_assignments(request: Request, db: Session = Depends(get_db)):
    if not _admin_access(request):
        return RedirectResponse(url="/auth/login", status_code=303)

    week = get_or_create_next_week(db)
    week.status = "published"
    db.commit()

    return RedirectResponse(url="/assignments/admin?success=published", status_code=303)


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
        .filter(
            Assignment.week_id == week.id,
            Assignment.user_id == current_user.id,
        )
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

    db.add(
        UserMessage(
            user_id=current_user.id,
            week_id=week.id,
            message=message.strip(),
        )
    )
    db.commit()

    return RedirectResponse(url="/assignments?success=message_sent", status_code=303)
