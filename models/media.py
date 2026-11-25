"""
Uploaded Media database model.
Tracks images, audio recordings, videos, cryptographic hash (SHA-256),
storage paths, thumbnails, and transcription.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import BigInteger, Column, DateTime, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Media(Base):
    __tablename__ = "media"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = Column(String(36), ForeignKey("reports.id", ondelete="CASCADE"), nullable=True, index=True)
    mission_id = Column(String(36), ForeignKey("missions.id", ondelete="SET NULL"), nullable=True, index=True)
    media_type = Column(String(20), nullable=False, index=True)  # IMAGE, AUDIO, VIDEO
    storage_path = Column(String(500), nullable=False)
    thumbnail_path = Column(String(500), nullable=True)
    original_filename = Column(String(255), nullable=False)
    sha256_hash = Column(String(64), nullable=False, index=True)
    file_size_bytes = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=False)
    processing_status = Column(String(30), default="PENDING", index=True)  # PENDING, PROCESSING, COMPLETED, FAILED

    # Speech-to-Text Fields (for audio recordings)
    transcript = Column(Text, nullable=True)
    transcript_confidence = Column(Float, nullable=True)
    transcript_language = Column(String(10), nullable=True)
    is_uncertain_transcript = Column(String(10), default="false")

    # Metadata & AI findings
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    report = relationship("Report", back_populates="media_items", foreign_keys=[report_id])
    mission = relationship("Mission", back_populates="media_items", foreign_keys=[mission_id])
    observation_media = relationship("ObservationMedia", back_populates="media", cascade="all, delete-orphan")
