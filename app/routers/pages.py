from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def root():
    return RedirectResponse(url="/auth/login", status_code=303)


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    username = request.cookies.get("username")
    role = request.cookies.get("role")

    if not username:
        return RedirectResponse(url="/auth/login", status_code=303)

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "username": username,
            "role": role,
        },
    )
