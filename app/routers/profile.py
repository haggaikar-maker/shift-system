from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.user_service import (
    email_exists,
    get_user_by_username,
    phone_exists,
    update_user,
    username_exists,
)

router = APIRouter(prefix="/profile", tags=["profile"])
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
def profile_page(request: Request, db: Session = Depends(get_db)):
    username = request.cookies.get("username")
    if not username:
        return RedirectResponse(url="/auth/login", status_code=303)

    user = get_user_by_username(db, username)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)

    return templates.TemplateResponse(
        request,
        "profile.html",
        {
            "user_item": user,
            "error": None,
            "success": request.query_params.get("success"),
        },
    )


@router.post("", response_class=HTMLResponse)
def profile_submit(
    request: Request,
    full_name: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    password: str = Form(""),
    db: Session = Depends(get_db),
):
    current_username = request.cookies.get("username")
    if not current_username:
        return RedirectResponse(url="/auth/login", status_code=303)

    user = get_user_by_username(db, current_username)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)

    error = None
    if username_exists(db, username, exclude_user_id=user.id):
        error = "שם המשתמש כבר קיים"
    elif email_exists(db, email, exclude_user_id=user.id):
        error = "האימייל כבר קיים"
    elif phone_exists(db, phone, exclude_user_id=user.id):
        error = "הטלפון כבר קיים"

    if error:
        return templates.TemplateResponse(
            request,
            "profile.html",
            {
                "user_item": user,
                "error": error,
                "success": None,
            },
            status_code=400,
        )

    updated_user = update_user(
        db=db,
        user=user,
        full_name=full_name,
        username=username,
        email=email,
        phone=phone,
        role=user.role,
        min_shifts_per_week=user.min_shifts_per_week,
        max_shifts_per_week=user.max_shifts_per_week,
        min_gap_hours=user.min_gap_hours,
        is_active=user.is_active,
        is_schedulable=user.is_schedulable,
        password=password,
    )

    response = RedirectResponse(url="/profile?success=1", status_code=303)
    response.set_cookie("username", updated_user.username, httponly=True)
    response.set_cookie("role", updated_user.role, httponly=True)
    response.set_cookie("user_id", str(updated_user.id), httponly=True)
    return response
