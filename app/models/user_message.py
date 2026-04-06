from sqlalchemy import Integer, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class UserMessage(Base):
    __tablename__ = "user_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    week_id: Mapped[int] = mapped_column(ForeignKey("schedule_weeks.id"))
    message: Mapped[str] = mapped_column(String)
