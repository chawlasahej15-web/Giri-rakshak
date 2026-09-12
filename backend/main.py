import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import CORS_ORIGINS, UPLOAD_DIR

from database import Base, engine
import models
from fastapi.middleware.cors import CORSMiddleware
from routes.alerts import router as alerts_router
from routes.auth import router as auth_router
from routes.notifications import router as notifications_router
from routes.official import router as official_router
from routes.reports import router as reports_router

from routes.risk import router as risk_router
from routes.sensors import router as sensors_router

app = FastAPI(
    title="GiriRakshak API",
    description="AI-powered landslide monitoring, citizen reporting and official response API",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5000",
        "http://localhost:5000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# DATABASE
# ============================================================

Base.metadata.create_all(bind=engine)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROUTES
# ============================================================


# ============================================================
# CORS
# ============================================================

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5500,http://127.0.0.1:5500",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROUTES
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

app.include_router(auth_router)
app.include_router(reports_router)
app.include_router(official_router)
app.include_router(notifications_router)
app.include_router(sensors_router)
app.include_router(risk_router)
app.include_router(alerts_router)
@app.get("/")
def root():
    return {"status": "online", "message": "GiriRakshak API v2 is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "database": "configured"}
