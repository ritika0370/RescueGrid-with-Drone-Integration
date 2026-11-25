"""
Disaster Response and Rescue Coordination Platform - FastAPI Backend Application.
"""
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.v1 import api_v1_router
from app.core.config import settings
from app.core.database import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: run database setup on startup."""
    logger.info("Initializing Disaster Response Platform database...")
    await init_db()
    logger.info("Database tables initialized successfully.")
    yield
    logger.info("Shutting down Disaster Response Platform...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Comprehensive backend system for Disaster Response and Rescue Coordination.\n\n"
        "Features:\n"
        "- Citizen Emergency SOS Ingestion (App, Web, Twilio Phone Voice Calls)\n"
        "- Multi-Factor Incident Grouping Engine (Spatial, Temporal, NLP Similarity)\n"
        "- Multimodal AI Emergency Analysis (Text, Audio, Vision)\n"
        "- Transparent Priority Assessment (P1-P4) with Human Override Audit\n"
        "- Drone Fleet & Mission Job Card Dispatch\n"
        "- Manual Drone Pilot Workflow & Observation Submission\n"
        "- 9-Section Final Rescue Intelligence Report Generation (JSON & PDF)\n"
        "- Real-Time WebSocket Event Distribution"
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploaded media directory for authorized media retrieval
app.mount("/uploads", StaticFiles(directory=settings.STORAGE_DIR), name="uploads")

# Include Versioned API Routes (/api/v1)
app.include_router(api_v1_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "online",
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "documentation": "/docs",
        "api_v1": settings.API_V1_STR,
        "twilio_integration": {
            "status": "active",
            "voice_hotline_number": settings.TWILIO_PHONE_NUMBER,
            "webhook_endpoint": f"{settings.API_V1_STR}/twilio/voice/incoming",
        },
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "storage": settings.STORAGE_TYPE,
        "vision_provider": settings.VISION_PROVIDER,
        "stt_provider": settings.STT_PROVIDER,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
