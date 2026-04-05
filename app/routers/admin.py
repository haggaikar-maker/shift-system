from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.preference import Preference
from app.services.week_service import get_or_create_next_week

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")


@router.get("/preferences", response_class=HTMLResponse)
def admin_preferences(request: Request, db: Session = Depends(get_db)):
    username = request.cookies.get("username")
    role = request.cookies.get("role")

    if not username or role not in ["admin", "shift_manager"]:
        return RedirectResponse("/auth/login")

    week = get_or_create_next_week(db)

    users = db.query(User).all()

    rows = []

    for user in users:
        prefs = db.query(Preference).filter_by(
            user_id=user.id,
            week_id=week.id
        ).all()

        filled = len(prefs) > 0

        want_count = sum(1 for p in prefs if p.score == 1)
        cannot_count = sum(1 for p in prefs if p.score == 5)

        rows.append({
            "name": user.full_name,
            "username": user.username,
            "filled": filled,
            "want": want_count,
            "cannot": cannot_count
        })

    return templates.TemplateResponse(request, "admin_preferences.html", {
        "rows": rows,
        "week": week
    })
