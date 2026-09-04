from fastapi import FastAPI
from database import Base, engine
import models

from routes.sensors import router as sensors_router
from routes.risk import router as risk_router
from routes.alerts import router as alerts_router
from routes.reports import router as reports_router

app = FastAPI(
    title="GiriRakshak API",
    description="Backend API for AI-powered landslide monitoring",
    version="1.0.0"
)

Base.metadata.create_all(bind=engine)

app.include_router(sensors_router)
app.include_router(risk_router)
app.include_router(alerts_router)
app.include_router(reports_router)

@app.get("/")
def root():
    return {
        "status": "online",
        "message": "GiriRakshak API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }