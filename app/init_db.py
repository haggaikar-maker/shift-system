from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.models import User, ScheduleWeek, Shift, Preference, Assignment, Satisfaction, UserMessage
from app.services.auth_service import hash_password


def ensure_user_columns():
    inspector = inspect(engine)
    user_columns = [col["name"] for col in inspector.get_columns("users")]
    week_columns = [col["name"] for col in inspector.get_columns("schedule_weeks")]

    with engine.connect() as conn:
        # users.is_schedulable
        if "is_schedulable" not in user_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_schedulable BOOLEAN DEFAULT TRUE"))
            conn.commit()

        # users.satisfaction_override
        if "satisfaction_override" not in user_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN satisfaction_override INTEGER NULL"))
            conn.commit()

        # schedule_weeks.published_at
        if "published_at" not in week_columns:
            conn.execute(text("ALTER TABLE schedule_weeks ADD COLUMN published_at TIMESTAMP NULL"))
            conn.commit()


def init_db():
    Base.metadata.create_all(bind=engine)
    ensure_user_columns()

    db: Session = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin_user = User(
                full_name="מנהל מערכת",
                username="admin",
                email="admin@example.com",
                phone="0500000000",
                password_hash=hash_password("admin123"),
                role="admin",
                is_active=True,
                is_schedulable=True,
                min_shifts_per_week=0,
                max_shifts_per_week=7,
                min_gap_hours=12,
                satisfaction_override=None,
            )
            db.add(admin_user)
            db.commit()
            print("Admin user created: admin / admin123")
        else:
            if getattr(admin, "is_schedulable", None) is None:
                admin.is_schedulable = True
            if getattr(admin, "satisfaction_override", None) is None:
                admin.satisfaction_override = None
            db.commit()
            print("Admin user already exists")
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
