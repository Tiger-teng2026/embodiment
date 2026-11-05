import io
import logging
from datetime import timedelta
from pathlib import Path

from minio import Minio

from app.config import settings

logger = logging.getLogger(__name__)


class StorageError(Exception):
    pass


class Storage:
    def __init__(self) -> None:
        self.bucket = settings.minio_bucket_name
        self.client = self._client(settings.minio_endpoint)
        public = settings.minio_public_endpoint.strip() or settings.minio_endpoint
        self.signer = self.client if public == settings.minio_endpoint else self._client(public)

    def _client(self, endpoint: str) -> Minio:
        return Minio(
            endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )

    def ensure_bucket(self) -> None:
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except Exception as exc:
            raise StorageError(str(exc)) from exc

    def upload_bytes(self, key: str, data: bytes, content_type: str) -> None:
        try:
            self.client.put_object(
                self.bucket,
                key,
                io.BytesIO(data),
                length=len(data),
                content_type=content_type,
            )
        except Exception as exc:
            raise StorageError(str(exc)) from exc

    def upload_file(self, key: str, path: Path, content_type: str) -> None:
        try:
            self.client.fput_object(self.bucket, key, str(path), content_type=content_type)
        except Exception as exc:
            raise StorageError(str(exc)) from exc

    def download(self, key: str, path: Path) -> None:
        try:
            self.client.fget_object(self.bucket, key, str(path))
        except Exception as exc:
            raise StorageError(str(exc)) from exc

    def presign(self, key: str, filename: str) -> str:
        try:
            return self.signer.presigned_get_object(
                self.bucket,
                key,
                expires=timedelta(seconds=settings.presign_seconds),
                response_headers={
                    "response-content-disposition": f'attachment; filename="{filename}"'
                },
            )
        except Exception as exc:
            raise StorageError(str(exc)) from exc

    def remove_quiet(self, key: str) -> None:
        try:
            self.client.remove_object(self.bucket, key)
        except Exception:
            logger.warning("could not remove object %s", key)

    def healthy(self) -> bool:
        try:
            self.client.bucket_exists(self.bucket)
            return True
        except Exception:
            return False


storage = Storage()
