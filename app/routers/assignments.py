from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.assignment_service import run_assignment_algorithm
from app.services.satisfaction_service import calculate_satisfaction
from app.services.week_service import get_or_create_next_week

router = APIRouter(prefix="/assignments")


@router.get("/run")
def run_assignments(request: Request, db: Session = Depends(get_db)):
    week = get_or_create_next_week(db)

    run_assignment_algorithm(db, week.id)
    calculate_satisfaction(db, week.id)

    return RedirectResponse("/assignments/admin", status_code=303)


@router.get("/publish")
def publish(request: Request, db: Session = Depends(get_db)):
    week = get_or_create_next_week(db)

    week.status = "published"
    db.commit()

    return RedirectResponse("/assignments/admin", status_code=303)
