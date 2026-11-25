"""
Application Configuration Settings.
Loads configuration from environment variables and provides safe defaults.
"""
import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Project metadata
    PROJECT_NAME: str = "Disaster Response and Rescue Coordination Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # Security & JWT
    SECRET_KEY: str = Field(
        default="disaster-response-secure-key-2026-production-change-me",
        description="HMAC secret key for JWT token signing",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./disaster_platform.db",
        description="Async database connection string. Can be postgresql+asyncpg://... or sqlite+aiosqlite:///",
    )
    DATABASE_SYNC_URL: Optional[str] = Field(
        default="sqlite:///./disaster_platform.db",
        description="Sync database connection string for migrations and inspection",
    )

    # Redis & Event Queue
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for caching, queues, and pub/sub",
    )

    # Storage
    STORAGE_TYPE: str = "local"  # "local" or "s3"
    STORAGE_DIR: str = os.path.abspath("./uploads")
    MEDIA_DIR: str = os.path.join(os.path.abspath("./uploads"), "media")
    THUMBNAIL_DIR: str = os.path.join(os.path.abspath("./uploads"), "thumbnails")
    REPORTS_PDF_DIR: str = os.path.join(os.path.abspath("./uploads"), "reports_pdf")
    MAX_UPLOAD_SIZE_BYTES: int = 50 * 1024 * 1024  # 50 MB
    ALLOWED_IMAGE_EXTENSIONS: List[str] = ["jpg", "jpeg", "png", "webp", "gif"]
    ALLOWED_AUDIO_EXTENSIONS: List[str] = ["mp3", "wav", "m4a", "ogg", "aac"]
    ALLOWED_VIDEO_EXTENSIONS: List[str] = ["mp4", "mov", "avi", "mkv", "webm"]

    # AI & Computer Vision Providers
    VISION_PROVIDER: str = "simulated"  # "simulated", "yolov8"
    YOLO_MODEL_PATH: str = "yolov8n.pt"
    STT_PROVIDER: str = "configurable"  # "configurable", "whisper", "twilio"
    OPENAI_API_KEY: Optional[str] = None

    # Twilio Voice Call Integration (Credentials can be set via env, leaving placeholders by default)
    TWILIO_ACCOUNT_SID: str = "AC_TWILIO_PLACEHOLDER_ACCOUNT_SID"
    TWILIO_AUTH_TOKEN: str = "TWILIO_PLACEHOLDER_AUTH_TOKEN"
    TWILIO_PHONE_NUMBER: str = "+18005550199"
    TWILIO_WEBHOOK_BASE_URL: str = "http://localhost:8000"

    # Incident Grouping Engine Thresholds
    GROUPING_MAX_DISTANCE_KM: float = 3.5  # Max radius for incident spatial proximity
    GROUPING_TIME_WINDOW_HOURS: float = 6.0  # Max temporal window
    GROUPING_HIGH_CONFIDENCE_THRESHOLD: float = 0.70  # Auto-suggest link
    GROUPING_MEDIUM_CONFIDENCE_THRESHOLD: float = 0.35  # Send for officer review

    # CORS
    CORS_ORIGINS: List[str] = ["*"]


settings = Settings()

# Ensure storage directories exist
os.makedirs(settings.MEDIA_DIR, exist_ok=True)
os.makedirs(settings.THUMBNAIL_DIR, exist_ok=True)
os.makedirs(settings.REPORTS_PDF_DIR, exist_ok=True)
