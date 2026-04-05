from sqlalchemy.orm import Session
from app.models.preference import Preference

def upsert_preferences(db: Session, user_id, week_id, data):
    for shift_id, score in data.items():
        row = db.query(Preference).filter_by(
            user_id=user_id,
            week_id=week_id,
            shift_id=shift_id
        ).first()

        if row:
            row.score = score
        else:
            db.add(Preference(
                user_id=user_id,
                week_id=week_id,
                shift_id=shift_id,
                score=score
            ))
    db.commit()
