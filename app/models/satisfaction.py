from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Satisfaction(Base):
    __tablename__ = "satisfaction"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    week_id: Mapped[int] = mapped_column(ForeignKey("schedule_weeks.id"))

    score: Mapped[int] = mapped_column(Integer)
