from collections import defaultdict

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.preference_service import get_user_preferences_for_week, upsert_preferences
from app.services.user_service import get_user_by_id, get_user_by_username
from app.services.week_service import get_or_create_next_week, get_week_shifts

router = APIRouter(prefix="/preferences", tags=["preferences"])
templates = Jinja2Templates(directory="app/templates")

SCORE_OPTIONS = [
    (1, "1"),
    (2, "2"),
    (3, "3"),
    (4, "4"),
    (5, "5"),
]

SCORE_LABELS = {
    1: "ממש רוצה",
    2: "רוצה",
    3: "ניטרלי",
    4: "לא רוצה",
    5: "לא יכול",
}

SHIFT_TYPE_LABELS = {
    "day": "יום",
    "night": "לילה",
}


def _resolve_target_user(request: Request, db: Session):
    current_username = request.cookies.get("username")
    current_role = request.cookies.get("role")
    if not current_username:
        return None, None

    current_user = get_user_by_username(db, current_username)
    if not current_user:
        return None, None

    target_user = current_user
    target_user_id = request.query_params.get("user_id")

    if target_user_id and current_role in ["admin", "shift_manager"]:
        try:
            parsed_id = int(target_user_id)
            found = get_user_by_id(db, parsed_id)
            if found:
                target_user = found
        except ValueError:
            pass

    return current_user, target_user


@router.get("", response_class=HTMLResponse)
def preferences_page(request: Request, db: Session = Depends(get_db)):
    current_user, target_user = _resolve_target_user(request, db)
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)

    week = get_or_create_next_week(db)
    shifts = get_week_shifts(db, week.id)
    user_scores = get_user_preferences_for_week(db, target_user.id, week.id)

    days = []
    shifts_by_type = defaultdict(list)

    for shift in shifts:
        if shift.shift_date not in [d["date_obj"] for d in days]:
            days.append(
                {
                    "date_obj": shift.shift_date,
                    "day_name": ["שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת", "ראשון"][shift.shift_date.weekday()],
                    "date_text": shift.shift_date.strftime("%d/%m/%Y"),
                }
            )

        shifts_by_type[shift.shift_type].append(
            {
                "id": shift.id,
                "shift_date": shift.shift_date,
                "score": user_scores.get(shift.id, 3),
            }
        )

    table_rows = []
    for shift_type in ["day", "night"]:
        row_cells = []
        shifts_map = {item["shift_date"]: item for item in shifts_by_type.get(shift_type, [])}

        for day in days:
            shift_item = shifts_map.get(day["date_obj"])
            row_cells.append(
                {
                    "shift_id": shift_item["id"] if shift_item else None,
                    "score": shift_item["score"] if shift_item else 3,
                }
            )

        table_rows.append(
            {
                "shift_type": shift_type,
                "shift_type_label": SHIFT_TYPE_LABELS[shift_type],
                "cells": row_cells,
            }
        )

    summary_counts = {
        1: sum(1 for score in user_scores.values() if score == 1),
        5: sum(1 for score in user_scores.values() if score == 5),
    }

    return templates.TemplateResponse(
        request,
        "preferences.html",
        {
            "week": week,
            "days": days,
            "table_rows": table_rows,
            "score_options": SCORE_OPTIONS,
            "score_labels": SCORE_LABELS,
            "summary_counts": summary_counts,
            "success": request.query_params.get("success"),
            "target_user": target_user,
            "current_role": current_user.role,
        },
    )


@router.post("", response_class=HTMLResponse)
async def preferences_submit(request: Request, db: Session = Depends(get_db)):
    current_user, target_user = _resolve_target_user(request, db)
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)

    week = get_or_create_next_week(db)
    shifts = get_week_shifts(db, week.id)
    form = await request.form()

    score_by_shift_id = {}
    for shift in shifts:
        raw_value = form.get(f"shift_{shift.id}", "3")
        try:
            score = int(raw_value)
        except ValueError:
            score = 3
        if score < 1 or score > 5:
            score = 3
        score_by_shift_id[shift.id] = score

    upsert_preferences(db, target_user.id, week.id, score_by_shift_id)

    if current_user.role in ["admin", "shift_manager"] and current_user.id != target_user.id:
        return RedirectResponse(url=f"/preferences?user_id={target_user.id}&success=1", status_code=303)
    return RedirectResponse(url="/preferences?success=1", status_code=303)
