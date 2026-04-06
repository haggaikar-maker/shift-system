from fastapi import APIRouter
from app.services.schedule_service import run_schedule

router = APIRouter()


@router.post("/admin/run-schedule")
def run_schedule_route():
    return run_schedule()
