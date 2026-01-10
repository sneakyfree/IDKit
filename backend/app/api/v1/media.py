"""
Media API Endpoints

Handles file uploads, presigned URLs, and media management.
"""

import uuid
from typing import List

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.dependencies import CurrentUser
from app.utils.storage import (
    storage_service,
    validate_media_type,
    get_media_folder,
)

router = APIRouter()


# ==================== Schemas ====================


class UploadUrlRequest(BaseModel):
    """Request for a presigned upload URL."""

    filename: str = Field(min_length=1, max_length=255)
    content_type: str
    file_size: int = Field(gt=0)


class UploadUrlResponse(BaseModel):
    """Presigned upload URL response."""

    upload_url: str
    file_key: str
    file_url: str
    expires_in: int


class BatchUploadRequest(BaseModel):
    """Request for multiple presigned upload URLs."""

    files: List[UploadUrlRequest] = Field(min_length=1, max_length=10)


class BatchUploadResponse(BaseModel):
    """Multiple presigned URLs response."""

    uploads: List[UploadUrlResponse]


class DeleteMediaRequest(BaseModel):
    """Request to delete media files."""

    file_keys: List[str] = Field(min_length=1, max_length=50)


class DeleteMediaResponse(BaseModel):
    """Delete operation response."""

    deleted: List[str]
    failed: List[str]


# ==================== Endpoints ====================


@router.post("/upload-url", response_model=UploadUrlResponse)
async def get_upload_url(
    request: UploadUrlRequest,
    current_user: CurrentUser,
):
    """
    Get a presigned URL for direct upload to S3/MinIO.

    The client should use this URL to PUT the file directly.
    After upload, use the file_url in post creation.
    """
    # Validate media type and size
    is_valid, error = validate_media_type(request.content_type, request.file_size)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )

    # Get appropriate folder
    folder = get_media_folder(request.content_type)

    # Generate presigned URL
    result = await storage_service.generate_upload_url(
        user_id=current_user.id,
        filename=request.filename,
        content_type=request.content_type,
        folder=folder,
    )

    return UploadUrlResponse(
        upload_url=result["upload_url"],
        file_key=result["file_key"],
        file_url=result["file_url"],
        expires_in=result["expires_in"],
    )


@router.post("/upload-urls", response_model=BatchUploadResponse)
async def get_batch_upload_urls(
    request: BatchUploadRequest,
    current_user: CurrentUser,
):
    """
    Get multiple presigned URLs for batch upload.

    Useful for carousel posts or multiple media attachments.
    """
    uploads = []

    for file_req in request.files:
        # Validate each file
        is_valid, error = validate_media_type(file_req.content_type, file_req.file_size)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{file_req.filename}: {error}",
            )

        folder = get_media_folder(file_req.content_type)

        result = await storage_service.generate_upload_url(
            user_id=current_user.id,
            filename=file_req.filename,
            content_type=file_req.content_type,
            folder=folder,
        )

        uploads.append(
            UploadUrlResponse(
                upload_url=result["upload_url"],
                file_key=result["file_key"],
                file_url=result["file_url"],
                expires_in=result["expires_in"],
            )
        )

    return BatchUploadResponse(uploads=uploads)


@router.get("/download-url")
async def get_download_url(
    file_key: str = Query(..., description="S3 object key"),
    filename: str = Query(None, description="Download filename"),
    current_user: CurrentUser = None,
):
    """
    Get a presigned URL for downloading a file.

    Optional filename parameter forces download with that name.
    """
    # Check if file exists
    exists = await storage_service.file_exists(file_key)
    if not exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    url = await storage_service.generate_download_url(
        file_key=file_key,
        filename=filename,
    )

    return {"download_url": url, "expires_in": 3600}


@router.delete("/files", response_model=DeleteMediaResponse)
async def delete_media_files(
    request: DeleteMediaRequest,
    current_user: CurrentUser,
):
    """
    Delete media files from storage.

    Only files owned by the current user can be deleted.
    """
    deleted = []
    failed = []

    for file_key in request.file_keys:
        # Verify ownership (file key should contain user ID)
        if str(current_user.id) not in file_key:
            failed.append(file_key)
            continue

        success = await storage_service.delete_file(file_key)
        if success:
            deleted.append(file_key)
        else:
            failed.append(file_key)

    return DeleteMediaResponse(deleted=deleted, failed=failed)


@router.get("/files")
async def list_user_files(
    current_user: CurrentUser,
    folder: str = Query(default="uploads", description="Folder to list"),
    limit: int = Query(default=100, ge=1, le=1000),
):
    """
    List media files for the current user.
    """
    prefix = f"{folder}/{current_user.id}/"
    files = await storage_service.list_files(prefix=prefix, max_keys=limit)

    return {
        "files": files,
        "count": len(files),
    }
