from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.models.schedule_week import ScheduleWeek
from app.models.shift import Shift

def get_next_week_start():
    today = date.today()
    days = (7 - today.weekday()) % 7
    return today + timedelta(days=days or 7)

def get_or_create_next_week(db: Session):
    start = get_next_week_start()
    end = start + timedelta(days=6)

    week = db.query(ScheduleWeek).filter_by(week_start_date=start).first()
    if week:
        return week

    week = ScheduleWeek(week_start_date=start, week_end_date=end)
    db.add(week)
    db.commit()
    db.refresh(week)

    for i in range(7):
        for t in ["day", "night"]:
            db.add(Shift(
                week_id=week.id,
                shift_date=start + timedelta(days=i),
                shift_type=t
            ))

    db.commit()
    return week
