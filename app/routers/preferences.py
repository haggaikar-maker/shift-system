from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.week_service import get_or_create_next_week
from app.services.preference_service import upsert_preferences
from app.services.user_service import get_user_by_username
from app.models.shift import Shift

router = APIRouter(prefix="/preferences")
templates = Jinja2Templates(directory="app/templates")

@router.get("", response_class=HTMLResponse)
def page(request: Request, db: Session = Depends(get_db)):
    username = request.cookies.get("username")
    if not username:
        return RedirectResponse("/auth/login")

    user = get_user_by_username(db, username)
    week = get_or_create_next_week(db)
    shifts = db.query(Shift).filter_by(week_id=week.id).all()

    return templates.TemplateResponse(request, "preferences.html", {
        "shifts": shifts
    })

@router.post("", response_class=HTMLResponse)
async def submit(request: Request, db: Session = Depends(get_db)):
    username = request.cookies.get("username")
    user = get_user_by_username(db, username)

    week = get_or_create_next_week(db)
    shifts = db.query(Shift).filter_by(week_id=week.id).all()

    form = await request.form()
    data = {}

    for s in shifts:
        data[s.id] = int(form.get(f"shift_{s.id}", 3))

    upsert_preferences(db, user.id, week.id, data)

    return RedirectResponse("/preferences", status_code=303)
