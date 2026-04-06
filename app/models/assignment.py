from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    week_id: Mapped[int] = mapped_column(ForeignKey("schedule_weeks.id"))
    shift_id: Mapped[int] = mapped_column(ForeignKey("shifts.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    locked: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
