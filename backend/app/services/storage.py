import os
import hashlib
import uuid
import shutil
from abc import ABC, abstractmethod
from typing import Tuple, BinaryIO, Optional
from app.core.config import settings


class StorageService(ABC):
    @abstractmethod
    def save_file(self, file_obj: BinaryIO, original_filename: str) -> Tuple[str, str, int]:
        """
        Saves the file securely and returns:
        (storage_key, sha256_hash, file_size_bytes)
        """
        pass

    @abstractmethod
    def get_file_path(self, storage_key: str) -> str:
        """Returns the local filesystem path or temporary path to the file."""
        pass

    @abstractmethod
    def open_file(self, storage_key: str) -> BinaryIO:
        """Opens and returns a binary stream of the stored file."""
        pass

    @abstractmethod
    def delete_file(self, storage_key: str) -> bool:
        """Removes the file from storage."""
        pass

    @abstractmethod
    def verify_integrity(self, storage_key: str, expected_hash: str) -> bool:
        """Recalculates SHA-256 hash and compares with expected hash."""
        pass


class LocalStorageService(StorageService):
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = os.path.abspath(base_dir or settings.LOCAL_STORAGE_DIR)
        os.makedirs(self.base_dir, exist_ok=True)

    def _sanitize_storage_key(self, storage_key: str) -> str:
        # Prevent directory traversal attacks
        base_name = os.path.basename(storage_key)
        full_path = os.path.abspath(os.path.join(self.base_dir, base_name))
        if not full_path.startswith(self.base_dir):
            raise ValueError("Directory traversal attempt detected in storage key")
        return full_path

    def save_file(self, file_obj: BinaryIO, original_filename: str) -> Tuple[str, str, int]:
        # Generate safe random UUID key with preserved file extension
        ext = os.path.splitext(original_filename)[1].lower()
        if not ext:
            ext = ".bin"
        storage_key = f"{uuid.uuid4().hex}{ext}"
        destination_path = os.path.join(self.base_dir, storage_key)

        sha256 = hashlib.sha256()
        file_size = 0

        # Reset file pointer to beginning
        if hasattr(file_obj, "seek"):
            file_obj.seek(0)

        with open(destination_path, "wb") as dest:
            while chunk := file_obj.read(64 * 1024):
                sha256.update(chunk)
                file_size += len(chunk)
                dest.write(chunk)

        return storage_key, sha256.hexdigest(), file_size

    def get_file_path(self, storage_key: str) -> str:
        full_path = self._sanitize_storage_key(storage_key)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Stored file with key {storage_key} not found")
        return full_path

    def open_file(self, storage_key: str) -> BinaryIO:
        full_path = self.get_file_path(storage_key)
        return open(full_path, "rb")

    def delete_file(self, storage_key: str) -> bool:
        try:
            full_path = self._sanitize_storage_key(storage_key)
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
        except Exception:
            pass
        return False

    def verify_integrity(self, storage_key: str, expected_hash: str) -> bool:
        full_path = self.get_file_path(storage_key)
        sha256 = hashlib.sha256()
        with open(full_path, "rb") as f:
            while chunk := f.read(64 * 1024):
                sha256.update(chunk)
        return sha256.hexdigest().lower() == expected_hash.lower()


class DatabaseStorageService(StorageService):
    """
    Persistent private document storage service.
    Persists document binary blobs in dedicated relational storage (PostgreSQL),
    with an automatic transparent local disk cache for zero-latency OCR/streaming.
    Survives container restarts, redeployments, and host migrations.
    """
    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = os.path.abspath(cache_dir or settings.LOCAL_STORAGE_DIR)
        os.makedirs(self.cache_dir, exist_ok=True)

    def _sanitize_storage_key(self, storage_key: str) -> str:
        base_name = os.path.basename(storage_key)
        full_path = os.path.abspath(os.path.join(self.cache_dir, base_name))
        if not full_path.startswith(self.cache_dir):
            raise ValueError("Directory traversal attempt detected in storage key")
        return full_path

    def save_file(self, file_obj: BinaryIO, original_filename: str) -> Tuple[str, str, int]:
        ext = os.path.splitext(original_filename)[1].lower() or ".bin"
        storage_key = f"{uuid.uuid4().hex}{ext}"

        if hasattr(file_obj, "seek"):
            file_obj.seek(0)
        content = file_obj.read()
        sha256 = hashlib.sha256(content).hexdigest()
        file_size = len(content)

        # 1. Persist to PostgreSQL document_blobs table
        from app.db.session import SessionLocal
        from app.models.models import DocumentBlob
        db = SessionLocal()
        try:
            blob = db.query(DocumentBlob).filter(DocumentBlob.storage_key == storage_key).first()
            if not blob:
                blob = DocumentBlob(
                    storage_key=storage_key,
                    file_data=content,
                    sha256_hash=sha256,
                    file_size_bytes=file_size,
                    content_type="application/pdf" if ext == ".pdf" else "application/octet-stream"
                )
                db.add(blob)
            else:
                blob.file_data = content
                blob.sha256_hash = sha256
                blob.file_size_bytes = file_size
            db.commit()
        finally:
            db.close()

        # 2. Write to local cache directory
        cache_path = self._sanitize_storage_key(storage_key)
        with open(cache_path, "wb") as f:
            f.write(content)

        return storage_key, sha256, file_size

    def get_file_path(self, storage_key: str) -> str:
        cache_path = self._sanitize_storage_key(storage_key)
        if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
            return cache_path

        # Populate cache from persistent database blob
        from app.db.session import SessionLocal
        from app.models.models import DocumentBlob
        db = SessionLocal()
        try:
            blob = db.query(DocumentBlob).filter(DocumentBlob.storage_key == storage_key).first()
            if not blob:
                raise FileNotFoundError(f"Stored file with key {storage_key} not found in persistent storage")
            with open(cache_path, "wb") as f:
                f.write(blob.file_data)
            return cache_path
        finally:
            db.close()

    def open_file(self, storage_key: str) -> BinaryIO:
        path = self.get_file_path(storage_key)
        return open(path, "rb")

    def delete_file(self, storage_key: str) -> bool:
        cache_path = self._sanitize_storage_key(storage_key)
        if os.path.exists(cache_path):
            try:
                os.remove(cache_path)
            except Exception:
                pass
        from app.db.session import SessionLocal
        from app.models.models import DocumentBlob
        db = SessionLocal()
        try:
            blob = db.query(DocumentBlob).filter(DocumentBlob.storage_key == storage_key).first()
            if blob:
                db.delete(blob)
                db.commit()
                return True
        finally:
            db.close()
        return False

    def verify_integrity(self, storage_key: str, expected_hash: str) -> bool:
        try:
            path = self.get_file_path(storage_key)
            sha256 = hashlib.sha256()
            with open(path, "rb") as f:
                while chunk := f.read(64 * 1024):
                    sha256.update(chunk)
            return sha256.hexdigest().lower() == expected_hash.lower()
        except Exception:
            return False


# Factory or default instance
def get_storage_service() -> StorageService:
    if settings.STORAGE_TYPE in ("database", "postgres"):
        return DatabaseStorageService()
    return LocalStorageService()
