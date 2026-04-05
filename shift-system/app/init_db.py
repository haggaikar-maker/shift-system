from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.models import User
from app.services.auth_service import hash_password


def init_db():
    Base.metadata.create_all(bind=engine)

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
                min_shifts_per_week=0,
                max_shifts_per_week=7,
                min_gap_hours=12,
            )
            db.add(admin_user)
            db.commit()
            print("Admin user created: admin / admin123")
        else:
            print("Admin user already exists")
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
