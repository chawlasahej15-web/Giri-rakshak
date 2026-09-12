import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def normalize_database_url(url: str | None) -> str:
    url = (url or "sqlite:///./giri_rakshak.db").strip()
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


DATABASE_URL = normalize_database_url(os.getenv("DATABASE_URL"))
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-only-change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "720"))
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))
SENSOR_API_KEY = os.getenv("SENSOR_API_KEY", "").strip()
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5500,http://127.0.0.1:5500,http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

UPLOAD_DIR = Path(
    os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads" / "reports"))
).resolve()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
