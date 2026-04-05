from sqlalchemy.orm import Session

from app.models.user import User
from app.services.auth_service import hash_password


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter_by(username=username).first()


def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter_by(id=user_id).first()


def list_users(db: Session):
    return db.query(User).order_by(User.full_name.asc()).all()


def create_user(
    db: Session,
    full_name: str,
    username: str,
    email: str,
    phone: str,
    password: str,
    role: str = "user",
    min_shifts_per_week: int = 0,
    max_shifts_per_week: int = 5,
    min_gap_hours: int = 12,
):
    user = User(
        full_name=full_name.strip(),
        username=username.strip(),
        email=email.strip(),
        phone=phone.strip(),
        password_hash=hash_password(password),
        role=role,
        is_active=True,
        min_shifts_per_week=min_shifts_per_week,
        max_shifts_per_week=max_shifts_per_week,
        min_gap_hours=min_gap_hours,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def username_exists(db: Session, username: str) -> bool:
    return db.query(User).filter(User.username == username.strip()).first() is not None


def email_exists(db: Session, email: str) -> bool:
    return db.query(User).filter(User.email == email.strip()).first() is not None


def phone_exists(db: Session, phone: str) -> bool:
    return db.query(User).filter(User.phone == phone.strip()).first() is not None
