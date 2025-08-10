from pathlib import Path
import uuid
from functools import lru_cache
import logging
from app.services.database_service import get_database_service
import httpx
from typing import Optional

logger = logging.getLogger(__name__)


class FileStorageService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FileStorageService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "db_service"):
            self.db_service = get_database_service()

    def generate_storage_path(self, file_name: str) -> str:
        """Generate a unique storage path for a file"""
        unique_id = str(uuid.uuid4())
        file_extension = Path(file_name).suffix
        return f"{unique_id}{file_extension}"

    def upload_file(self, file_content: bytes, file_name: str, bucket: str) -> str:
        """Upload a file to Supabase storage and return the file path

        Args:
            file_content: The file content in bytes
            file_name: The name of the file
            bucket: The storage bucket name to upload to

        Returns:
            str: The public URL of the uploaded file
        """
        storage_path = self.generate_storage_path(file_name)
        try:
            storage_client = self.db_service.supabase.storage
            logger.info(
                f"Creating signed upload URL for path: {storage_path} in bucket: {bucket}"
            )
            signed_url_response = storage_client.from_(bucket).create_signed_upload_url(
                storage_path
            )

            if not signed_url_response or "signedUrl" not in signed_url_response:
                raise Exception("Failed to create signed upload URL")

            path = signed_url_response["path"]
            token = signed_url_response["token"]
            storage_client.from_(bucket).upload_to_signed_url(
                path=path, token=token, file=file_content
            )
            logger.info(
                f"Successfully uploaded file to path: {storage_path} in bucket: {bucket}"
            )

            file_url = storage_client.from_(bucket).get_public_url(storage_path)
            return file_url

        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Storage path: {storage_path}")
            logger.error(f"File name: {file_name}")
            logger.error(f"Bucket: {bucket}")
            raise

    async def download_file(
        self, url: str, bucket: str, timeout: Optional[float] = 30.0
    ) -> bytes:
        """Download a file from Supabase storage and return its contents as bytes.

        Args:
            url: The URL of the file
            bucket: The storage bucket name to download from
            timeout: Timeout in seconds for the request (default: 30 seconds)

        Returns:
            bytes: The file contents

        Raises:
            Exception: If the download fails or times out
        """
        try:
            logger.info(f"Downloading file from bucket '{bucket}': {url}")

            # Extract the file path from the URL (last part after the last /)
            file_path = url.split("/")[-1]

            storage_client = self.db_service.supabase.storage
            response = storage_client.from_(bucket).download(file_path)
            logger.info(f"Successfully downloaded file from bucket '{bucket}': {url}")
            return response

        except Exception as e:
            logger.error(f"Error downloading file from bucket '{bucket}': {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"URL: {url}")
            raise Exception(f"Failed to download file: {str(e)}")


@lru_cache()
def get_file_storage_service() -> FileStorageService:
    return FileStorageService()
