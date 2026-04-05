from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.schedule_week import ScheduleWeek
from app.models.shift import Shift


SHIFT_TYPES = ["day", "night"]

DAY_NAMES_HE = {
    6: "ראשון",
    0: "שני",
    1: "שלישי",
    2: "רביעי",
    3: "חמישי",
    4: "שישי",
    5: "שבת",
}


def get_next_week_start(today: date | None = None) -> date:
    today = today or date.today()

    # weekday(): Monday=0 ... Sunday=6
    days_until_next_sunday = (6 - today.weekday()) % 7
    if days_until_next_sunday == 0:
        days_until_next_sunday = 7

    return today + timedelta(days=days_until_next_sunday)


def get_or_create_next_week(db: Session, slots_per_shift: int = 2, shifts_per_day: int = 2) -> ScheduleWeek:
    week_start = get_next_week_start()
    week_end = week_start + timedelta(days=6)

    week = db.query(ScheduleWeek).filter(ScheduleWeek.week_start_date == week_start).first()
    if week:
        return week

    week = ScheduleWeek(
        week_start_date=week_start,
        week_end_date=week_end,
        status="draft",
        slots_per_shift=slots_per_shift,
        shifts_per_day=shifts_per_day,
    )
    db.add(week)
    db.commit()
    db.refresh(week)

    for i in range(7):
        shift_date = week_start + timedelta(days=i)
        for shift_type in SHIFT_TYPES[:shifts_per_day]:
            db.add(
                Shift(
                    week_id=week.id,
                    shift_date=shift_date,
                    shift_type=shift_type,
                    capacity=slots_per_shift,
                )
            )

    db.commit()
    return week


def get_week_shifts(db: Session, week_id: int):
    return (
        db.query(Shift)
        .filter(Shift.week_id == week_id)
        .order_by(Shift.shift_date.asc(), Shift.shift_type.asc())
        .all()
    )


def get_shift_label(shift) -> str:
    day_name = DAY_NAMES_HE.get(shift.shift_date.weekday(), "")
    shift_type_he = "יום" if shift.shift_type == "day" else "לילה"
    return f"{day_name} | {shift.shift_date.strftime('%d/%m/%Y')} | {shift_type_he}"
