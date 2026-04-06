from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.assignment_service import run_assignment_algorithm
from app.services.satisfaction_service import calculate_satisfaction
from app.services.week_service import get_or_create_next_week

router = APIRouter(prefix="/assignments", tags=["assignments"])
templates = Jinja2Templates(directory="app/templates")


def _admin_access(request: Request):
    username = request.cookies.get("username")
    role = request.cookies.get("role")
    return username and role in ["admin", "shift_manager"]


@router.get("/admin", response_class=HTMLResponse)
def assignments_admin_page(request: Request):
    return templates.TemplateResponse(
        request,
        "assignments_admin.html",
        {}
    )


@router.get("/run")
def run_assignments(request: Request, db: Session = Depends(get_db)):
    if not _admin_access(request):
        return RedirectResponse(url="/auth/login", status_code=303)

    week = get_or_create_next_week(db)
    run_assignment_algorithm(db, week.id)
    calculate_satisfaction(db, week.id)

    return RedirectResponse("/assignments/admin", status_code=303)


@router.get("/publish")
def publish(request: Request, db: Session = Depends(get_db)):
    if not _admin_access(request):
        return RedirectResponse(url="/auth/login", status_code=303)

    week = get_or_create_next_week(db)
    week.status = "published"
    db.commit()

    return RedirectResponse("/assignments/admin", status_code=303)
