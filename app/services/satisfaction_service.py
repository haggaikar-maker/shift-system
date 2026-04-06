from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.preference import Preference
from app.models.satisfaction import Satisfaction


def calculate_satisfaction(db: Session, week_id: int):
    assignments = db.query(Assignment).filter_by(week_id=week_id).all()

    for a in assignments:
        pref = db.query(Preference).filter_by(
            week_id=week_id,
            shift_id=a.shift_id,
            user_id=a.user_id
        ).first()

        score = 100

        if pref:
            score = max(0, 120 - pref.score * 20)

        db.add(Satisfaction(
            user_id=a.user_id,
            week_id=week_id,
            score=score
        ))

    db.commit()
