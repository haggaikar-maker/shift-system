from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.preference_service import get_preference_summary_for_user_week
from app.services.user_service import (
    create_user,
    email_exists,
    get_user_by_id,
    list_users,
    phone_exists,
    username_exists,
)
from app.services.week_service import get_or_create_next_week

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="app/templates")

ROLE_OPTIONS = ["user", "shift_manager", "admin"]


def _check_admin_access(request: Request):
    username = request.cookies.get("username")
    role = request.cookies.get("role")
    return username and role in ["admin", "shift_manager"]


@router.get("/preferences", response_class=HTMLResponse)
def admin_preferences(request: Request, db: Session = Depends(get_db)):
    if not _check_admin_access(request):
        return RedirectResponse(url="/auth/login", status_code=303)

    week = get_or_create_next_week(db)
    users = list_users(db)
    rows = []

    for user in users:
        summary = get_preference_summary_for_user_week(db, user.id, week.id)
        rows.append(
            {
                "id": user.id,
                "name": user.full_name,
                "username": user.username,
                "email": user.email,
                "phone": user.phone,
                "role": user.role,
                "filled": summary["filled"],
                "want": summary["want_count"],
                "cannot": summary["cannot_count"],
                "week_label": f"{week.week_start_date.strftime('%d/%m/%Y')} - {week.week_end_date.strftime('%d/%m/%Y')}",
            }
        )

    return templates.TemplateResponse(
        request,
        "admin_preferences.html",
        {
            "rows": rows,
            "week": week,
            "success": request.query_params.get("success"),
        },
    )


@router.get("/users/new", response_class=HTMLResponse)
def new_user_page(request: Request):
    if not _check_admin_access(request):
        return RedirectResponse(url="/auth/login", status_code=303)

    return templates.TemplateResponse(
        request,
        "admin_user_form.html",
        {
            "error": None,
            "success": None,
            "role_options": ROLE_OPTIONS,
        },
    )


@router.post("/users/new", response_class=HTMLResponse)
def create_user_submit(
    request: Request,
    full_name: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...),
    role: str = Form("user"),
    min_shifts_per_week: int = Form(0),
    max_shifts_per_week: int = Form(5),
    min_gap_hours: int = Form(12),
    db: Session = Depends(get_db),
):
    if not _check_admin_access(request):
        return RedirectResponse(url="/auth/login", status_code=303)

    error = None
    if username_exists(db, username):
        error = "שם המשתמש כבר קיים"
    elif email_exists(db, email):
        error = "האימייל כבר קיים"
    elif phone_exists(db, phone):
        error = "הטלפון כבר קיים"
    elif role not in ROLE_OPTIONS:
        error = "תפקיד לא תקין"
    elif max_shifts_per_week < min_shifts_per_week:
        error = "מקסימום שיבוצים חייב להיות גדול או שווה למינימום"

    if error:
        return templates.TemplateResponse(
            request,
            "admin_user_form.html",
            {
                "error": error,
                "success": None,
                "role_options": ROLE_OPTIONS,
            },
            status_code=400,
        )

    create_user(
        db=db,
        full_name=full_name,
        username=username,
        email=email,
        phone=phone,
        password=password,
        role=role,
        min_shifts_per_week=min_shifts_per_week,
        max_shifts_per_week=max_shifts_per_week,
        min_gap_hours=min_gap_hours,
    )
    return RedirectResponse(url="/admin/preferences?success=user_created", status_code=303)


@router.get("/users/{user_id}", response_class=HTMLResponse)
def user_detail_page(user_id: int, request: Request, db: Session = Depends(get_db)):
    if not _check_admin_access(request):
        return RedirectResponse(url="/auth/login", status_code=303)

    user = get_user_by_id(db, user_id)
    if not user:
        return RedirectResponse(url="/admin/preferences", status_code=303)

    week = get_or_create_next_week(db)
    summary = get_preference_summary_for_user_week(db, user.id, week.id)

    return templates.TemplateResponse(
        request,
        "admin_user_detail.html",
        {
            "user_item": user,
            "week": week,
            "summary": summary,
        },
    )
