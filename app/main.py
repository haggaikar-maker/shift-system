from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import auth, pages, preferences, admin, profile, assignments

app = FastAPI(title=settings.APP_NAME)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(pages.router)
app.include_router(preferences.router)
app.include_router(admin.router)
app.include_router(profile.router)
app.include_router(assignments.router)
