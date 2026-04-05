import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "Shift System")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./shift_system.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change_me_please")


settings = Settings()
