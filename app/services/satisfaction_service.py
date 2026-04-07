from collections import defaultdict
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.preference import Preference
from app.models.satisfaction import Satisfaction
from app.models.user import User


def calculate_satisfaction(db: Session, week_id: int):
    db.query(Satisfaction).filter(Satisfaction.week_id == week_id).delete()

    users = db.query(User).filter(User.is_active == True).all()
    assignments = db.query(Assignment).filter_by(week_id=week_id).all()

    assigned_by_user = defaultdict(list)
    for a in assignments:
        assigned_by_user[a.user_id].append(a)

    for user in users:
        if user.satisfaction_override is not None:
            db.add(Satisfaction(
                user_id=user.id,
                week_id=week_id,
                score=int(user.satisfaction_override),
                is_manual_override=1,
            ))
            continue

        rows = assigned_by_user.get(user.id, [])
        if not rows:
            db.add(Satisfaction(
                user_id=user.id,
                week_id=week_id,
                score=40,
                is_manual_override=0,
            ))
            continue

        scores = []
        for a in rows:
            pref = db.query(Preference).filter_by(
                week_id=week_id,
                shift_id=a.shift_id,
                user_id=a.user_id
            ).first()

            pref_score = pref.score if pref else 3
            mapped = {1: 100, 2: 85, 3: 70, 4: 50, 5: 0}.get(pref_score, 70)
            scores.append(mapped)

        avg_score = int(sum(scores) / len(scores)) if scores else 40
        db.add(Satisfaction(
            user_id=user.id,
            week_id=week_id,
            score=avg_score,
            is_manual_override=0,
        ))

    db.commit()


def get_latest_satisfaction_map(db: Session, week_id: int):
    rows = db.query(Satisfaction).filter(Satisfaction.week_id == week_id).all()
    return {r.user_id: r.score for r in rows}
