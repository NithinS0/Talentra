"""Secure Storage Service for Documents, Resumes, and Profile Photos.

Implements private bucket handling, file signature (magic byte) verification,
path traversal prevention, SHA-256 fingerprinting, and dual-mode persistence
(Supabase Storage API with automatic local vault fallback for development/testing).
"""

import os
import re
import uuid
import hashlib
import mimetypes
from typing import Tuple, Optional
from datetime import datetime, timezone, timedelta
import httpx

from app.core.config import settings

# Allowed MIME types and extensions
ALLOWED_EXTENSIONS = {
    "pdf": "application/pdf",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
}

# Magic bytes signature validation
MAGIC_SIGNATURES = {
    "pdf": [b"%PDF-"],
    "jpg": [b"\xff\xd8\xff"],
    "jpeg": [b"\xff\xd8\xff"],
    "png": [b"\x89PNG\r\n\x1a\n"],
    "webp": [b"RIFF"],  # And offset 8 is WEBP
    "docx": [b"PK\x03\x04"],  # ZIP container
    "doc": [b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"],  # OLE container
}

MAX_DOCUMENT_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_PHOTO_SIZE_BYTES = 2 * 1024 * 1024       # 2 MB

LOCAL_STORAGE_VAULT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "storage_vault"))


class StorageValidationError(Exception):
    """File size, type, or signature validation failure."""
    pass


from dataclasses import dataclass


@dataclass
class StorageResult:
    storage_key: str
    safe_filename: str
    size_bytes: int
    mime_type: str
    content_sha256: str


class StorageService:
    """Manages secure file uploads, verification, and retrieval."""

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Strip dangerous characters and path traversal sequences."""
        clean = os.path.basename(filename)
        clean = re.sub(r"[^a-zA-Z0-9._-]", "_", clean)
        return clean[:120] if clean else "document"

    @classmethod
    def validate_file(
        cls,
        content: bytes,
        original_filename: str,
        is_photo: bool = False,
    ) -> Tuple[str, str, int, str]:
        """Validate size, extension, MIME type, and magic bytes.

        Returns: (safe_filename, mime_type, file_size_bytes, sha256_hash)
        """
        size = len(content)
        max_allowed = MAX_PHOTO_SIZE_BYTES if is_photo else MAX_DOCUMENT_SIZE_BYTES
        if size == 0:
            raise StorageValidationError("File is empty (0 bytes).")
        if size > max_allowed:
            limit_mb = max_allowed // (1024 * 1024)
            raise StorageValidationError(f"File size ({size / 1024 / 1024:.2f} MB) exceeds maximum allowed limit ({limit_mb} MB).")

        safe_name = cls.sanitize_filename(original_filename)
        ext = safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else ""
        if ext not in ALLOWED_EXTENSIONS:
            raise StorageValidationError(
                f"File format '.{ext}' is not supported. Allowed formats: {', '.join(sorted(ALLOWED_EXTENSIONS.keys()))}"
            )

        if is_photo and ext not in ["jpg", "jpeg", "png", "webp"]:
            raise StorageValidationError("Profile photos must be JPEG, PNG, or WebP.")

        expected_mime = ALLOWED_EXTENSIONS[ext]

        # Magic byte header check
        valid_signature = False
        signatures = MAGIC_SIGNATURES.get(ext, [])
        for sig in signatures:
            if content.startswith(sig):
                if ext == "webp":
                    if len(content) > 12 and content[8:12] == b"WEBP":
                        valid_signature = True
                else:
                    valid_signature = True
                break

        if not valid_signature:
            raise StorageValidationError(
                f"File content does not match the expected signature for '.{ext}'."
            )

        sha256_hash = hashlib.sha256(content).hexdigest()
        return safe_name, expected_mime, size, sha256_hash

    @classmethod
    def store_file(
        cls,
        actor_id: str = "default",
        category: str = "document",
        content: Optional[bytes] = None,
        original_filename: str = "document",
        is_photo: bool = False,
        file_bytes: Optional[bytes] = None,
        content_type: Optional[str] = None,
        owner_id: Optional[int] = None,
    ) -> StorageResult:
        """Validate and persist file to Supabase Storage or Local Vault.

        Returns: StorageResult with metadata.
        """
        actual_content = content if content is not None else (file_bytes or b"")
        actual_actor = actor_id if actor_id != "default" else (str(owner_id) if owner_id else "common")
        actual_is_photo = is_photo or (category == "photo")

        safe_name, mime_type, size, sha256_hash = cls.validate_file(
            content=actual_content,
            original_filename=original_filename,
            is_photo=actual_is_photo,
        )

        unique_id = uuid.uuid4().hex[:12]
        safe_actor = re.sub(r"[^a-zA-Z0-9-]", "_", actual_actor)
        safe_cat = re.sub(r"[^a-zA-Z0-9_-]", "_", category.lower())
        storage_key = f"candidates/{safe_actor}/{safe_cat}/{unique_id}_{safe_name}"

        # 1. Attempt Supabase Storage if configured with service role key
        if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
            try:
                bucket = "talentra-documents"
                url = f"{settings.SUPABASE_URL.rstrip('/')}/storage/v1/object/{bucket}/{storage_key}"
                headers = {
                    "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                    "Content-Type": mime_type,
                }
                with httpx.Client(timeout=10.0) as client:
                    client.post(url, headers=headers, content=actual_content)
            except Exception:
                pass

        # 2. Always persist to local storage vault for guaranteed retrieval / offline resilience
        target_path = os.path.join(LOCAL_STORAGE_VAULT, os.path.normpath(storage_key))
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "wb") as f:
            f.write(actual_content)

        return StorageResult(
            storage_key=storage_key,
            safe_filename=safe_name,
            size_bytes=size,
            mime_type=mime_type,
            content_sha256=sha256_hash,
        )

    @classmethod
    def retrieve_file(cls, storage_key: str) -> Tuple[bytes, str, str]:
        """Retrieve file bytes, safe filename, and mime type from local vault or Supabase."""
        safe_filename = os.path.basename(storage_key).split("_", 1)[-1] if "_" in storage_key else os.path.basename(storage_key)

        # Check local vault first
        target_path = os.path.join(LOCAL_STORAGE_VAULT, os.path.normpath(storage_key))
        if os.path.isfile(target_path):
            with open(target_path, "rb") as f:
                content = f.read()
            ext = storage_key.rsplit(".", 1)[-1].lower() if "." in storage_key else "bin"
            mime = ALLOWED_EXTENSIONS.get(ext, "application/octet-stream")
            return content, safe_filename, mime

        # Fallback to Supabase Storage
        if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
            try:
                bucket = "talentra-documents"
                url = f"{settings.SUPABASE_URL.rstrip('/')}/storage/v1/object/{bucket}/{storage_key}"
                headers = {"Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}"}
                with httpx.Client(timeout=10.0) as client:
                    resp = client.get(url, headers=headers)
                    if resp.status_code == 200:
                        mime = resp.headers.get("content-type", "application/octet-stream")
                        return resp.content, safe_filename, mime
            except Exception:
                pass

        raise StorageValidationError("File not found in storage vault.")

    @classmethod
    def delete_file(cls, storage_key: str) -> bool:
        """Remove file from storage."""
        target_path = os.path.join(LOCAL_STORAGE_VAULT, os.path.normpath(storage_key))
        if os.path.isfile(target_path):
            try:
                os.remove(target_path)
            except OSError:
                pass

        if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
            try:
                bucket = "talentra-documents"
                url = f"{settings.SUPABASE_URL.rstrip('/')}/storage/v1/object/{bucket}"
                headers = {
                    "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                    "Content-Type": "application/json",
                }
                with httpx.Client(timeout=10.0) as client:
                    client.request("DELETE", url, headers=headers, json={"prefixes": [storage_key]})
            except Exception:
                pass

        return True


storage_service = StorageService()
StorageError = StorageValidationError
