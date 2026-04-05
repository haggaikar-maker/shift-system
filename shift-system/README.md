# Shift System

מערכת ניהול משמרות בעברית, מבוססת FastAPI.

## מה יש כרגע
- התחברות בסיסית
- משתמש מנהל ראשוני
- הפרדה לקבצים ומודולים
- HTML/CSS בעברית
- בסיס נתונים עם SQLAlchemy

## הרצה מקומית
```bash
pip install -r requirements.txt
cp .env.example .env
python -m app.init_db
uvicorn app.main:app --reload
```

פתח בדפדפן:
`http://127.0.0.1:8000`

## משתמש ראשוני
- username: `admin`
- password: `admin123`

## הערה
כדי להתחיל מהר, קובץ `.env.example` מוגדר עם SQLite.
לפריסה לענן אפשר לעבור בהמשך ל-PostgreSQL.
