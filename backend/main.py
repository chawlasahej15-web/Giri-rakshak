import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
import models

from routes.sensors import router as sensors_router
from routes.risk import router as risk_router
from routes.alerts import router as alerts_router
from routes.reports import router as reports_router


app = FastAPI(
    title="GiriRakshak API",
    description="Backend API for AI-powered landslide monitoring",
    version="1.0.0",
)


# ============================================================
# DATABASE
# ============================================================

Base.metadata.create_all(bind=engine)


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
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROUTES
# ============================================================

app.include_router(sensors_router)
app.include_router(risk_router)
app.include_router(alerts_router)
app.include_router(reports_router)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "status": "online",
        "message": "GiriRakshak API is running",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
    }
