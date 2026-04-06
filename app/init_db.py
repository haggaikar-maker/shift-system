from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.models import User, ScheduleWeek, Shift, Preference
from app.services.auth_service import hash_password


def ensure_user_columns():
    inspector = inspect(engine)
    columns = [col["name"] for col in inspector.get_columns("users")]

    with engine.connect() as conn:
        if "is_schedulable" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_schedulable BOOLEAN DEFAULT 1"))
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
            )
            db.add(admin_user)
            db.commit()
            print("Admin user created: admin / admin123")
        else:
            if getattr(admin, "is_schedulable", None) is None:
                admin.is_schedulable = True
                db.commit()
            print("Admin user already exists")
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
