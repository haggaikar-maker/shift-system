from collections import defaultdict
import random

from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.preference import Preference
from app.models.user import User
from app.models.shift import Shift


def run_assignment_algorithm(db: Session, week_id: int):
    # מחיקת שיבוצים ישנים (לא נעולים)
    db.query(Assignment).filter(
        Assignment.week_id == week_id,
        Assignment.locked == False
    ).delete()

    users = db.query(User).filter(
        User.is_active == True,
        User.is_schedulable == True
    ).all()

    shifts = db.query(Shift).filter(Shift.week_id == week_id).all()

    # העדפות
    pref_map = defaultdict(dict)
    for p in db.query(Preference).filter(Preference.week_id == week_id):
        pref_map[p.shift_id][p.user_id] = p.score

    user_shift_count = defaultdict(int)

    for shift in shifts:
        capacity = shift.capacity
        candidates = []

        for user in users:
            score = pref_map.get(shift.id, {}).get(user.id, 3)

            if score == 5:
                continue

            candidates.append((user, score))

        # דירוג: קודם רוצים (1), ואז 2, ואז 3, ואז 4
        candidates.sort(key=lambda x: (x[1], user_shift_count[x[0].id]))

        selected = []

        for user, score in candidates:
            if len(selected) >= capacity:
                break

            selected.append(user)
            user_shift_count[user.id] += 1

        for user in selected:
            db.add(Assignment(
                week_id=week_id,
                shift_id=shift.id,
                user_id=user.id,
                locked=False
            ))

    db.commit()
