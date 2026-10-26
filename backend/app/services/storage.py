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


# Factory or default instance
def get_storage_service() -> StorageService:
    # Extensible to S3StorageService when STORAGE_TYPE == 's3'
    return LocalStorageService()
