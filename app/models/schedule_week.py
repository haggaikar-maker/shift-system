from datetime import date, datetime
from sqlalchemy import Date, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class ScheduleWeek(Base):
    __tablename__ = "schedule_weeks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    week_start_date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    week_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    slots_per_shift: Mapped[int] = mapped_column(Integer, default=2)
    shifts_per_day: Mapped[int] = mapped_column(Integer, default=2)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
