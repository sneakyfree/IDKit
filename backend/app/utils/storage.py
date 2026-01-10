"""
S3/MinIO Storage Utilities

Handles media uploads, presigned URLs, and file management.
"""

import hashlib
import mimetypes
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from io import BytesIO
from typing import AsyncIterator, BinaryIO, Optional
from urllib.parse import urljoin, urlparse

import aioboto3
from botocore.config import Config

from app.config import settings


@dataclass
class FileMetadata:
    """Metadata for a stored file."""

    key: str
    size: int
    content_type: str
    last_modified: datetime
    etag: str
    metadata: dict


@dataclass
class MultipartUploadInfo:
    """Information for multipart upload."""

    upload_id: str
    key: str
    bucket: str
    parts: list[dict]


class StorageService:
    """
    S3-compatible storage service for media files.

    Supports both AWS S3 and MinIO for local development.
    """

    def __init__(self):
        self.session = aioboto3.Session(
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
        )
        self.bucket_name = settings.s3_bucket_name
        self.endpoint_url = settings.s3_endpoint_url  # For MinIO

        # Configure for MinIO if endpoint is set
        self.config = Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
        )

    async def get_client(self):
        """Get async S3 client."""
        return self.session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            config=self.config,
        )

    async def generate_upload_url(
        self,
        user_id: uuid.UUID,
        filename: str,
        content_type: str,
        folder: str = "uploads",
        expires_in: int = 3600,
    ) -> dict:
        """
        Generate a presigned URL for direct upload.

        Returns:
            dict with:
                - upload_url: Presigned PUT URL
                - file_key: S3 object key
                - file_url: Public URL after upload
        """
        # Generate unique file key
        ext = filename.rsplit(".", 1)[-1] if "." in filename else ""
        file_id = uuid.uuid4()
        timestamp = datetime.now(timezone.utc).strftime("%Y/%m/%d")
        file_key = f"{folder}/{user_id}/{timestamp}/{file_id}.{ext}"

        async with await self.get_client() as client:
            upload_url = await client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": file_key,
                    "ContentType": content_type,
                },
                ExpiresIn=expires_in,
            )

        # Construct public URL
        if self.endpoint_url:
            # MinIO URL
            file_url = f"{self.endpoint_url}/{self.bucket_name}/{file_key}"
        else:
            # AWS S3 URL
            file_url = f"https://{self.bucket_name}.s3.{settings.aws_region}.amazonaws.com/{file_key}"

        return {
            "upload_url": upload_url,
            "file_key": file_key,
            "file_url": file_url,
            "expires_in": expires_in,
        }

    async def generate_download_url(
        self,
        file_key: str,
        expires_in: int = 3600,
        filename: Optional[str] = None,
    ) -> str:
        """Generate a presigned URL for downloading/viewing a file."""
        params = {
            "Bucket": self.bucket_name,
            "Key": file_key,
        }

        if filename:
            params["ResponseContentDisposition"] = f'attachment; filename="{filename}"'

        async with await self.get_client() as client:
            return await client.generate_presigned_url(
                "get_object",
                Params=params,
                ExpiresIn=expires_in,
            )

    async def upload_file(
        self,
        file_data: bytes,
        file_key: str,
        content_type: str,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Upload file directly to S3.

        Returns the public URL of the uploaded file.
        """
        async with await self.get_client() as client:
            await client.put_object(
                Bucket=self.bucket_name,
                Key=file_key,
                Body=file_data,
                ContentType=content_type,
                Metadata=metadata or {},
            )

        # Return public URL
        if self.endpoint_url:
            return f"{self.endpoint_url}/{self.bucket_name}/{file_key}"
        return f"https://{self.bucket_name}.s3.{settings.aws_region}.amazonaws.com/{file_key}"

    async def delete_file(self, file_key: str) -> bool:
        """Delete a file from S3."""
        try:
            async with await self.get_client() as client:
                await client.delete_object(
                    Bucket=self.bucket_name,
                    Key=file_key,
                )
            return True
        except Exception:
            return False

    async def file_exists(self, file_key: str) -> bool:
        """Check if a file exists in S3."""
        try:
            async with await self.get_client() as client:
                await client.head_object(
                    Bucket=self.bucket_name,
                    Key=file_key,
                )
            return True
        except Exception:
            return False

    async def copy_file(
        self,
        source_key: str,
        destination_key: str,
    ) -> str:
        """Copy a file within the bucket."""
        async with await self.get_client() as client:
            await client.copy_object(
                Bucket=self.bucket_name,
                CopySource={"Bucket": self.bucket_name, "Key": source_key},
                Key=destination_key,
            )

        if self.endpoint_url:
            return f"{self.endpoint_url}/{self.bucket_name}/{destination_key}"
        return f"https://{self.bucket_name}.s3.{settings.aws_region}.amazonaws.com/{destination_key}"

    async def list_files(
        self,
        prefix: str,
        max_keys: int = 1000,
    ) -> list[dict]:
        """List files with a given prefix."""
        async with await self.get_client() as client:
            response = await client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys,
            )

        files = []
        for obj in response.get("Contents", []):
            files.append({
                "key": obj["Key"],
                "size": obj["Size"],
                "last_modified": obj["LastModified"].isoformat(),
            })

        return files

    async def get_file_metadata(self, file_key: str) -> Optional[FileMetadata]:
        """Get detailed metadata for a file."""
        try:
            async with await self.get_client() as client:
                response = await client.head_object(
                    Bucket=self.bucket_name,
                    Key=file_key,
                )

            return FileMetadata(
                key=file_key,
                size=response["ContentLength"],
                content_type=response.get("ContentType", "application/octet-stream"),
                last_modified=response["LastModified"],
                etag=response["ETag"].strip('"'),
                metadata=response.get("Metadata", {}),
            )
        except Exception:
            return None

    async def get_file(self, file_key: str) -> Optional[bytes]:
        """Download file content from S3."""
        try:
            async with await self.get_client() as client:
                response = await client.get_object(
                    Bucket=self.bucket_name,
                    Key=file_key,
                )
                return await response["Body"].read()
        except Exception:
            return None

    async def stream_file(
        self,
        file_key: str,
        chunk_size: int = 8192,
    ) -> AsyncIterator[bytes]:
        """Stream file content in chunks for large files."""
        async with await self.get_client() as client:
            response = await client.get_object(
                Bucket=self.bucket_name,
                Key=file_key,
            )

            async with response["Body"] as stream:
                while True:
                    chunk = await stream.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk

    async def move_file(
        self,
        source_key: str,
        destination_key: str,
    ) -> str:
        """Move a file within the bucket (copy + delete)."""
        url = await self.copy_file(source_key, destination_key)
        await self.delete_file(source_key)
        return url

    async def delete_files(self, file_keys: list[str]) -> dict[str, bool]:
        """Delete multiple files at once."""
        results = {}
        async with await self.get_client() as client:
            # S3 batch delete allows up to 1000 objects at a time
            for i in range(0, len(file_keys), 1000):
                batch = file_keys[i : i + 1000]
                try:
                    response = await client.delete_objects(
                        Bucket=self.bucket_name,
                        Delete={
                            "Objects": [{"Key": key} for key in batch],
                            "Quiet": False,
                        },
                    )
                    for deleted in response.get("Deleted", []):
                        results[deleted["Key"]] = True
                    for error in response.get("Errors", []):
                        results[error["Key"]] = False
                except Exception:
                    for key in batch:
                        results[key] = False

        return results

    async def get_total_size(self, prefix: str) -> int:
        """Get total size of all files with a given prefix."""
        total = 0
        async with await self.get_client() as client:
            paginator = client.get_paginator("list_objects_v2")
            async for page in paginator.paginate(
                Bucket=self.bucket_name,
                Prefix=prefix,
            ):
                for obj in page.get("Contents", []):
                    total += obj["Size"]
        return total

    # =========================================================================
    # Multipart Upload Methods (for large files)
    # =========================================================================

    async def initiate_multipart_upload(
        self,
        file_key: str,
        content_type: str,
        metadata: Optional[dict] = None,
    ) -> str:
        """Initiate a multipart upload for large files."""
        async with await self.get_client() as client:
            response = await client.create_multipart_upload(
                Bucket=self.bucket_name,
                Key=file_key,
                ContentType=content_type,
                Metadata=metadata or {},
            )
            return response["UploadId"]

    async def generate_part_upload_url(
        self,
        file_key: str,
        upload_id: str,
        part_number: int,
        expires_in: int = 3600,
    ) -> str:
        """Generate presigned URL for uploading a part."""
        async with await self.get_client() as client:
            return await client.generate_presigned_url(
                "upload_part",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": file_key,
                    "UploadId": upload_id,
                    "PartNumber": part_number,
                },
                ExpiresIn=expires_in,
            )

    async def complete_multipart_upload(
        self,
        file_key: str,
        upload_id: str,
        parts: list[dict],  # [{"PartNumber": 1, "ETag": "..."}]
    ) -> str:
        """Complete a multipart upload."""
        async with await self.get_client() as client:
            await client.complete_multipart_upload(
                Bucket=self.bucket_name,
                Key=file_key,
                UploadId=upload_id,
                MultipartUpload={"Parts": parts},
            )

        if self.endpoint_url:
            return f"{self.endpoint_url}/{self.bucket_name}/{file_key}"
        return f"https://{self.bucket_name}.s3.{settings.aws_region}.amazonaws.com/{file_key}"

    async def abort_multipart_upload(
        self,
        file_key: str,
        upload_id: str,
    ) -> bool:
        """Abort a multipart upload."""
        try:
            async with await self.get_client() as client:
                await client.abort_multipart_upload(
                    Bucket=self.bucket_name,
                    Key=file_key,
                    UploadId=upload_id,
                )
            return True
        except Exception:
            return False

    # =========================================================================
    # Bucket Operations
    # =========================================================================

    async def ensure_bucket_exists(self) -> bool:
        """Ensure the bucket exists, create if not."""
        try:
            async with await self.get_client() as client:
                try:
                    await client.head_bucket(Bucket=self.bucket_name)
                    return True
                except Exception:
                    # Bucket doesn't exist, create it
                    await client.create_bucket(
                        Bucket=self.bucket_name,
                        CreateBucketConfiguration={
                            "LocationConstraint": settings.aws_region,
                        }
                        if settings.aws_region != "us-east-1"
                        else {},
                    )
                    return True
        except Exception:
            return False

    async def set_bucket_cors(
        self,
        allowed_origins: list[str] = ["*"],
        allowed_methods: list[str] = ["GET", "PUT", "POST", "DELETE"],
    ) -> bool:
        """Set CORS configuration for the bucket."""
        try:
            async with await self.get_client() as client:
                await client.put_bucket_cors(
                    Bucket=self.bucket_name,
                    CORSConfiguration={
                        "CORSRules": [
                            {
                                "AllowedHeaders": ["*"],
                                "AllowedMethods": allowed_methods,
                                "AllowedOrigins": allowed_origins,
                                "ExposeHeaders": ["ETag"],
                                "MaxAgeSeconds": 3600,
                            }
                        ]
                    },
                )
            return True
        except Exception:
            return False

    # =========================================================================
    # URL Utilities
    # =========================================================================

    def get_public_url(self, file_key: str) -> str:
        """Get the public URL for a file."""
        if self.endpoint_url:
            return f"{self.endpoint_url}/{self.bucket_name}/{file_key}"
        return f"https://{self.bucket_name}.s3.{settings.aws_region}.amazonaws.com/{file_key}"

    def get_cdn_url(self, file_key: str, cdn_domain: Optional[str] = None) -> str:
        """Get CDN URL for a file if CDN is configured."""
        if cdn_domain:
            return f"https://{cdn_domain}/{file_key}"
        return self.get_public_url(file_key)

    def extract_key_from_url(self, url: str) -> Optional[str]:
        """Extract the S3 key from a public URL."""
        parsed = urlparse(url)
        path = parsed.path

        # Handle bucket-in-path style
        if path.startswith(f"/{self.bucket_name}/"):
            return path[len(f"/{self.bucket_name}/") :]

        # Handle bucket-in-host style
        if self.bucket_name in parsed.netloc:
            return path.lstrip("/")

        return None

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def generate_file_key(
        self,
        user_id: uuid.UUID,
        filename: str,
        folder: str = "uploads",
    ) -> str:
        """Generate a unique file key."""
        ext = filename.rsplit(".", 1)[-1] if "." in filename else ""
        file_id = uuid.uuid4()
        timestamp = datetime.now(timezone.utc).strftime("%Y/%m/%d")
        return f"{folder}/{user_id}/{timestamp}/{file_id}.{ext}"

    @staticmethod
    def get_content_type(filename: str) -> str:
        """Get content type from filename."""
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or "application/octet-stream"

    @staticmethod
    def calculate_md5(data: bytes) -> str:
        """Calculate MD5 hash of data."""
        return hashlib.md5(data).hexdigest()

    @staticmethod
    def human_readable_size(size_bytes: int) -> str:
        """Convert bytes to human-readable format."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} PB"


# Helper functions for media types
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/avif",
}

ALLOWED_VIDEO_TYPES = {
    "video/mp4",
    "video/webm",
    "video/quicktime",
    "video/x-msvideo",
}

ALLOWED_AUDIO_TYPES = {
    "audio/mpeg",
    "audio/wav",
    "audio/ogg",
    "audio/aac",
    "audio/mp4",
}

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500MB
MAX_AUDIO_SIZE = 100 * 1024 * 1024  # 100MB


def validate_media_type(content_type: str, file_size: int) -> tuple[bool, str]:
    """
    Validate media type and size.

    Returns:
        (is_valid, error_message)
    """
    if content_type in ALLOWED_IMAGE_TYPES:
        if file_size > MAX_IMAGE_SIZE:
            return False, f"Image too large. Max size: {MAX_IMAGE_SIZE // (1024*1024)}MB"
        return True, ""

    if content_type in ALLOWED_VIDEO_TYPES:
        if file_size > MAX_VIDEO_SIZE:
            return False, f"Video too large. Max size: {MAX_VIDEO_SIZE // (1024*1024)}MB"
        return True, ""

    if content_type in ALLOWED_AUDIO_TYPES:
        if file_size > MAX_AUDIO_SIZE:
            return False, f"Audio too large. Max size: {MAX_AUDIO_SIZE // (1024*1024)}MB"
        return True, ""

    return False, f"Unsupported file type: {content_type}"


def get_media_folder(content_type: str) -> str:
    """Get the appropriate folder for a media type."""
    if content_type in ALLOWED_IMAGE_TYPES:
        return "images"
    if content_type in ALLOWED_VIDEO_TYPES:
        return "videos"
    if content_type in ALLOWED_AUDIO_TYPES:
        return "audio"
    return "files"


# Singleton instance
storage_service = StorageService()
