import os
from sqlalchemy import inspect, text
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import CORS_ORIGINS, UPLOAD_DIR
from database import Base, engine
import models

from routes.alerts import router as alerts_router
from routes.auth import router as auth_router
from routes.notifications import router as notifications_router
from routes.official import router as official_router
from routes.reports import router as reports_router
from routes.devices import router as devices_router
from routes.risk import router as risk_router
from routes.sensors import router as sensors_router
from routes.susceptibility import router as susceptibility_router


# ============================================================
# DATABASE SCHEMA COMPATIBILITY
# ============================================================

def ensure_schema_compatibility():

    Base.metadata.create_all(
        bind=engine
    )

    inspector = inspect(
        engine
    )

    additions = {
        "sensor_readings": {
            "telemetry_json": "TEXT",
            "alert_level": "VARCHAR(20)",
            "system_state": "VARCHAR(30)",
        },
        "alerts": {
            "source": "VARCHAR(30)",
            "is_active": "BOOLEAN",
        },
    }

    with engine.begin() as conn:

        for table_name, columns in additions.items():

            if not inspector.has_table(
                table_name
            ):
                continue

            existing = {
                column["name"]
                for column in inspector.get_columns(
                    table_name
                )
            }

            for column_name, column_type in columns.items():

                if column_name not in existing:

                    conn.execute(
                        text(
                            f"ALTER TABLE {table_name} "
                            f"ADD COLUMN {column_name} "
                            f"{column_type}"
                        )
                    )


ensure_schema_compatibility()

app = FastAPI(
    title="GiriRakshak API",
    description="AI-powered landslide monitoring, citizen reporting and official response API",
    version="2.0.0",
)

# ============================================================
# DATABASE
# ============================================================

Base.metadata.create_all(bind=engine)

# ============================================================
# CORS (SINGLE CLEAN MIDDLEWARE WITH WILDCARD FOR DEMO)
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows localhost:8000, 5500, Render, and Android APK wrappers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# MEDIA SERVING & ROUTERS
# ============================================================

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

app.include_router(auth_router)
app.include_router(reports_router)
app.include_router(official_router)
app.include_router(notifications_router)
app.include_router(sensors_router)
app.include_router(susceptibility_router)
app.include_router(risk_router)
app.include_router(alerts_router)
app.include_router(devices_router)
@app.get("/")
def root():
    return {"status": "online", "message": "GiriRakshak API v2 is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "database": "configured"}