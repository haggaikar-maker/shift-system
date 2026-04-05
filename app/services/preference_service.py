from sqlalchemy.orm import Session

from app.models.preference import Preference


def get_user_preferences_for_week(db: Session, user_id: int, week_id: int):
    rows = (
        db.query(Preference)
        .filter(Preference.user_id == user_id, Preference.week_id == week_id)
        .all()
    )
    return {row.shift_id: row.score for row in rows}


def upsert_preferences(db: Session, user_id: int, week_id: int, score_by_shift_id: dict[int, int]):
    existing_rows = (
        db.query(Preference)
        .filter(Preference.user_id == user_id, Preference.week_id == week_id)
        .all()
    )
    existing_map = {row.shift_id: row for row in existing_rows}

    for shift_id, score in score_by_shift_id.items():
        if shift_id in existing_map:
            existing_map[shift_id].score = score
        else:
            db.add(
                Preference(
                    user_id=user_id,
                    week_id=week_id,
                    shift_id=shift_id,
                    score=score,
                )
            )

    db.commit()


def get_preference_summary_for_user_week(db: Session, user_id: int, week_id: int):
    prefs = (
        db.query(Preference)
        .filter(Preference.user_id == user_id, Preference.week_id == week_id)
        .all()
    )
    return {
        "filled": len(prefs) > 0,
        "want_count": sum(1 for p in prefs if p.score == 1),
        "cannot_count": sum(1 for p in prefs if p.score == 5),
        "total": len(prefs),
    }
