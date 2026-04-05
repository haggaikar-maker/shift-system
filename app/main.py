from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers import preferences
from app.config import settings
from app.routers import auth, pages
from app.routers import admin

app.include_router(admin.router)
app = FastAPI(title=settings.APP_NAME)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(preferences.router)
app.include_router(auth.router)
app.include_router(pages.router)
