from collections import defaultdict
from datetime import timedelta

from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.preference import Preference
from app.models.satisfaction import Satisfaction
from app.models.user import User
from app.models.shift import Shift


def _shift_dt_key(shift):
    # day = 08:00, night = 20:00, רק לצורך השוואות
    hour = 8 if shift.shift_type == "day" else 20
    return (shift.shift_date, hour)


def _is_consecutive(shift_a, shift_b):
    # אותו יום: יום+לילה אסור
    if shift_a.shift_date == shift_b.shift_date:
        return True

    # לילה ואז יום למחרת אסור
    if shift_a.shift_type == "night" and shift_b.shift_type == "day":
        if shift_b.shift_date == shift_a.shift_date + timedelta(days=1):
            return True

    # יום אחרי לילה של אתמול - גם אסור בכיוון ההפוך
    if shift_b.shift_type == "night" and shift_a.shift_type == "day":
        if shift_a.shift_date == shift_b.shift_date + timedelta(days=1):
            return True

    return False


def _user_can_take_shift(user, shift, current_user_shift_objs):
    if len(current_user_shift_objs) >= user.max_shifts_per_week:
        return False

    for existing_shift in current_user_shift_objs:
        if _is_consecutive(existing_shift, shift):
            return False

    return True


def run_assignment_algorithm(db: Session, week_id: int):
    # לא מוחקים נעולים
    db.query(Assignment).filter(
        Assignment.week_id == week_id,
        Assignment.locked == False
    ).delete()

    users = db.query(User).filter(
        User.is_active == True,
        User.is_schedulable == True
    ).all()

    shifts = db.query(Shift).filter(Shift.week_id == week_id).order_by(Shift.shift_date.asc(), Shift.shift_type.asc()).all()

    locked_assignments = db.query(Assignment).filter(
        Assignment.week_id == week_id,
        Assignment.locked == True
    ).all()

    pref_map = defaultdict(dict)
    for p in db.query(Preference).filter(Preference.week_id == week_id):
        pref_map[p.shift_id][p.user_id] = p.score

    latest_sat_rows = db.query(Satisfaction).filter(Satisfaction.week_id == week_id).all()
    sat_map = {r.user_id: r.score for r in latest_sat_rows}

    user_shift_count = defaultdict(int)
    user_shift_objs = defaultdict(list)

    shifts_by_id = {s.id: s for s in shifts}

    for a in locked_assignments:
        shift = shifts_by_id.get(a.shift_id)
        if shift:
            user_shift_count[a.user_id] += 1
            user_shift_objs[a.user_id].append(shift)

    for shift in shifts:
        already_locked_here = [a for a in locked_assignments if a.shift_id == shift.id]
        locked_count = len(already_locked_here)
        remaining_capacity = max(0, shift.capacity - locked_count)

        if remaining_capacity == 0:
            continue

        candidates = []
        for user in users:
            score = pref_map.get(shift.id, {}).get(user.id, 3)
            if score == 5:
                continue

            if not _user_can_take_shift(user, shift, user_shift_objs[user.id]):
                continue

            # עדיפות בסיסית לפי העדפה
            pref_rank = score

            # מי שיש לו שביעות רצון נמוכה יקבל בוסט
            sat_score = sat_map.get(user.id, 70)
            sat_boost = 100 - sat_score

            # override ידני עוקף את חישוב ההוגנות
            if user.satisfaction_override is not None:
                sat_boost = 100 - int(user.satisfaction_override)

            candidates.append((user, pref_rank, sat_boost, user_shift_count[user.id]))

        candidates.sort(key=lambda x: (x[1], -x[2], x[3], x[0].full_name))

        picked = []
        for user, _, _, _ in candidates:
            if len(picked) >= remaining_capacity:
                break

            picked.append(user)
            user_shift_count[user.id] += 1
            user_shift_objs[user.id].append(shift)

        for user in picked:
            db.add(Assignment(
                week_id=week_id,
                shift_id=shift.id,
                user_id=user.id,
                locked=False,
            ))

    db.commit()
