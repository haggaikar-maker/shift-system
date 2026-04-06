from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth_service import authenticate_user

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        request,
        "login.html",
        {"error": None},
    )


@router.post("/login", response_class=HTMLResponse)
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "שם משתמש או סיסמה שגויים"},
            status_code=401,
        )

    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie("username", user.username, httponly=True, path="/")
    response.set_cookie("role", user.role, httponly=True, path="/")
    return response


@router.get("/logout")
def logout():
    response = RedirectResponse(url="/auth/login", status_code=303)
    response.delete_cookie("username", path="/")
    response.delete_cookie("role", path="/")
    return response
