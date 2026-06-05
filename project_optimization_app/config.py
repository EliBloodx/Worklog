import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "database.db"
SECRET_KEY = "dev-change-this-secret"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Local run configuration (can be overridden with environment variables).
APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
APP_PORT = int(os.getenv("APP_PORT", "5000"))
APP_DEBUG = os.getenv("APP_DEBUG", "1") == "1"
