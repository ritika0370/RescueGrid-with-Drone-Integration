"""
Storage Adapter for uploaded media files.
Handles validation, cryptographic SHA-256 hashing, thumbnail generation, and secure storage.
"""
import hashlib
import os
import uuid
from typing import Dict, Optional, Tuple
from PIL import Image
from app.core.config import settings


class StorageAdapter:
    @staticmethod
    def calculate_sha256(file_bytes: bytes) -> str:
        """Compute SHA-256 cryptographic hash of raw file bytes."""
        hasher = hashlib.sha256()
        hasher.update(file_bytes)
        return hasher.hexdigest()

    @staticmethod
    def validate_file(filename: str, file_size: int) -> Tuple[str, str]:
        """
        Validate file extension and size.
        Returns (media_type, extension) or raises ValueError.
        """
        if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
            raise ValueError(f"File size exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_BYTES} bytes.")

        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if not ext:
            raise ValueError("File has no extension.")

        if ext in settings.ALLOWED_IMAGE_EXTENSIONS:
            return "IMAGE", ext
        elif ext in settings.ALLOWED_AUDIO_EXTENSIONS:
            return "AUDIO", ext
        elif ext in settings.ALLOWED_VIDEO_EXTENSIONS:
            return "VIDEO", ext
        else:
            raise ValueError(f"Unsupported file extension: .{ext}")

    @classmethod
    def save_file(cls, filename: str, content: bytes) -> Dict[str, Optional[str]]:
        """
        Validates, hashes, stores content to disk, and generates thumbnails if image.
        Returns dictionary with storage paths, hash, and media metadata.
        """
        media_type, ext = cls.validate_file(filename, len(content))
        sha256_hash = cls.calculate_sha256(content)

        file_id = str(uuid.uuid4())
        safe_filename = f"{file_id}.{ext}"
        target_path = os.path.join(settings.MEDIA_DIR, safe_filename)

        with open(target_path, "wb") as f:
            f.write(content)

        thumbnail_path = None
        if media_type == "IMAGE":
            thumbnail_filename = f"thumb_{file_id}.jpg"
            thumb_full_path = os.path.join(settings.THUMBNAIL_DIR, thumbnail_filename)
            try:
                with Image.open(target_path) as img:
                    img = img.convert("RGB")
                    img.thumbnail((300, 300))
                    img.save(thumb_full_path, "JPEG", quality=85)
                thumbnail_path = thumb_full_path
            except Exception:
                thumbnail_path = None

        return {
            "media_type": media_type,
            "storage_path": target_path,
            "thumbnail_path": thumbnail_path,
            "sha256_hash": sha256_hash,
            "original_filename": filename,
            "file_size_bytes": len(content),
            "mime_type": f"{media_type.lower()}/{ext}",
        }
