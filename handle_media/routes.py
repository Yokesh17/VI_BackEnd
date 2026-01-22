from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from fastapi.responses import StreamingResponse
from typing import Optional
import io

from .storage import storage_service
from .models import (
    MediaUploadResponse, 
    ProfilePictureResponse, 
    MediaDeleteResponse,
    ErrorResponse,
    MediaInfo
)
from db_config import execute_returning_one, execute_all
from handle_media.queries import (
    # Media queries
    INSERT_MEDIA_UPLOAD,
    GET_MEDIA_BY_ID,
    GET_USER_MEDIA,
    SOFT_DELETE_MEDIA,
    # Profile picture queries
    INSERT_PROFILE_PICTURE,
    GET_CURRENT_PROFILE_PICTURE,
    GET_PROFILE_PICTURE_BY_ID,
    GET_USER_PROFILE_PICTURES,
    SOFT_DELETE_PROFILE_PICTURE
)
from utils import get_current_user

router = APIRouter(prefix="/media")

# Allowed file types
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/jpg", 
    "image/png",
    "image/webp",
    "image/heic"
}

ALLOWED_VIDEO_TYPES = {
    "video/mp4",
    "video/quicktime",
    "video/webm"
}

MAX_FILE_SIZE_MB = 10
MAX_VIDEO_SIZE_MB = 50


# ============================================
# MEDIA UPLOAD ENDPOINTS (General media: images, videos)
# ============================================

@router.post("/upload", response_model=MediaUploadResponse)
async def upload_media(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload media file (image or video) - stores ORIGINAL file only
    
    This endpoint:
    1. Validates the uploaded file
    2. Generates a unique media_id
    3. Uploads original file to R2 storage
    4. Stores metadata in database
    5. Returns URL for the file
    
    Use this for posts, stories, general media uploads.
    For profile pictures, use /profile-picture endpoint instead.
    """
    try:
        # Determine file type
        if file.content_type in ALLOWED_IMAGE_TYPES:
            file_type = "image"
            max_size = MAX_FILE_SIZE_MB
        elif file.content_type in ALLOWED_VIDEO_TYPES:
            file_type = "video"
            max_size = MAX_VIDEO_SIZE_MB
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES)}"
            )
        
        # Read file
        file_bytes = await file.read()
        
        # Check file size
        file_size_mb = len(file_bytes) / (1024 * 1024)
        if file_size_mb > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds {max_size}MB limit"
            )
        
        # Generate unique media ID
        media_id = storage_service.generate_media_id()
        user_id = current_user["id"]
        
        # Process and upload media (original only)
        upload_result = storage_service.process_and_upload_media(
            file_bytes=file_bytes,
            media_id=media_id,
            user_id=user_id,
            content_type=file.content_type,
            file_type=file_type
        )
        
        # Store in database
        db_params = {
            "media_id": media_id,
            "user_id": user_id,
            "file_type": file_type,
            "mime_type": file.content_type,
            "original_filename": file.filename,
            "file_size_bytes": upload_result["file_size_bytes"],
            "storage_key": upload_result["storage_key"],
            "width": upload_result["width"],
            "height": upload_result["height"],
            "duration_seconds": None,  # TODO: Extract for videos
            "upload_status": "completed"
        }
        
        result = execute_returning_one(INSERT_MEDIA_UPLOAD, db_params)
        
        return MediaUploadResponse(
            message="Media uploaded successfully",
            media_id=media_id,
            urls={"original": upload_result["url"]},
            file_type=file_type,
            mime_type=file.content_type,
            file_size_bytes=upload_result["file_size_bytes"],
            width=upload_result["width"],
            height=upload_result["height"],
            created_at=result["created_at"]
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.get("/{media_id}")
async def get_media_info(media_id: str, current_user: dict = Depends(get_current_user)):
    """
    Get media information by media_id
    Returns metadata and URL
    """
    try:
        result = execute_returning_one(GET_MEDIA_BY_ID, {"media_id": media_id})
        user_id = current_user["id"]
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media not found"
            )
        
        return {
            "status": "success",
            "media_id": result["media_id"],
            "user_id": user_id,
            "file_type": result["file_type"],
            "mime_type": result["mime_type"],
            "url": storage_service.get_public_url(result["storage_key"]),
            "width": result["width"],
            "height": result["height"],
            "duration_seconds": result["duration_seconds"],
            "file_size_bytes": result["file_size_bytes"],
            "created_at": result["created_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get media info: {str(e)}"
        )


@router.get("/download/{media_id}")
async def download_media(media_id: str, current_user: dict = Depends(get_current_user)):
    """
    Download media file by media_id
    """
    try:
        result = execute_returning_one(GET_MEDIA_BY_ID, {"media_id": media_id})
        user_id = current_user["id"]
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media not found"
            )
        
        # Download from R2
        file_bytes, content_type = storage_service.download_from_r2(result["storage_key"])
        
        return StreamingResponse(
            io.BytesIO(file_bytes),
            media_type=content_type,
            headers={
                "Content-Disposition": f'inline; filename="{media_id}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download media: {str(e)}"
        )


@router.delete("/{media_id}", response_model=MediaDeleteResponse)
async def delete_media(
    media_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Soft delete media (marks as deleted in database)
    Only the owner can delete their media
    """
    try:
        user_id = current_user["id"]
        
        result = execute_returning_one(SOFT_DELETE_MEDIA, {
            "media_id": media_id,
            "user_id": user_id
        })
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media not found or you don't have permission to delete it"
            )
        
        return MediaDeleteResponse(
            message="Media deleted successfully",
            media_id=media_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete media: {str(e)}"
        )


@router.get("/user/media")
async def get_user_media(
    limit: int = 20,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all media uploaded by a user
    Supports pagination
    """
    try:
        user_id = current_user["id"]
        results = execute_all(GET_USER_MEDIA, {
            "user_id": user_id,
            "limit": limit,
            "offset": offset
        })
        
        media_list = []
        for result in results:
            media_list.append({
                "media_id": result["media_id"],
                "file_type": result["file_type"],
                "mime_type": result["mime_type"],
                # "url": storage_service.get_public_url(result["storage_key"]),
                "width": result["width"],
                "height": result["height"],
                "duration_seconds": result["duration_seconds"],
                "file_size_bytes": result["file_size_bytes"],
                "created_at": result["created_at"]
            })
        
        return {
            "status": "success",
            "user_id": user_id,
            "media": media_list,
            "count": len(media_list),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user media: {str(e)}"
        )


# ============================================
# PROFILE PICTURE ENDPOINTS (Original + Thumbnail)
# ============================================

@router.post("/profile-picture", response_model=ProfilePictureResponse)
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload and set profile picture with automatic thumbnail generation
    
    This endpoint:
    1. Validates the uploaded image
    2. Generates unique profile_pic_id
    3. Creates original + thumbnail (150x150)
    4. Uploads both to R2 storage
    5. Marks previous profile pictures as not current
    6. Returns URLs for original and thumbnail
    """
    try:
        # Validate content type (images only for profile pictures)
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_IMAGE_TYPES)}"
            )
        
        # Read file
        file_bytes = await file.read()
        
        # Check file size
        file_size_mb = len(file_bytes) / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds {MAX_FILE_SIZE_MB}MB limit"
            )
        
        # Generate unique profile picture ID
        profile_pic_id = storage_service.generate_media_id()
        user_id = current_user["id"]
        
        # Process and upload profile picture (original + thumbnail)
        upload_result = storage_service.process_and_upload_profile_picture(
            file_bytes=file_bytes,
            profile_pic_id=profile_pic_id,
            user_id=user_id,
            content_type=file.content_type
        )
        
        # Store in database (automatically marks previous as not current)
        db_params = {
            "profile_pic_id": profile_pic_id,
            "user_id": user_id,
            "mime_type": file.content_type,
            "original_filename": file.filename,
            "file_size_bytes": upload_result["file_size_bytes"],
            "original_key": upload_result["original_key"],
            "thumbnail_key": upload_result["thumbnail_key"],
            "width": upload_result["width"],
            "height": upload_result["height"]
        }
        
        execute_returning_one(INSERT_PROFILE_PICTURE, db_params)
        
        return ProfilePictureResponse(
            message="Profile picture updated successfully",
            media_id=profile_pic_id,
            urls={
                "original": upload_result["original_url"],
                "thumbnail": upload_result["thumbnail_url"]
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set profile picture: {str(e)}"
        )


@router.get("/profile-picture/{user_id}")
async def get_profile_picture(current_user: dict = Depends(get_current_user)):
    """
    Get user's current profile picture
    Returns URLs for original and thumbnail
    """
    try:
        user_id = current_user["id"]
        result = execute_returning_one(GET_CURRENT_PROFILE_PICTURE, {"user_id": user_id})
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No profile picture found"
            )
        
        return {
            "status": "success",
            "profile_pic_id": result["profile_pic_id"],
            "urls": {
                "original": storage_service.get_public_url(result["original_key"]),
                "thumbnail": storage_service.get_public_url(result["thumbnail_key"])
            },
            "mime_type": result["mime_type"],
            "width": result["width"],
            "height": result["height"],
            "created_at": result["created_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get profile picture: {str(e)}"
        )


@router.get("/profile-picture/{user_id}/history")
async def get_profile_picture_history(
    limit: int = 10,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all profile pictures for a user (history)
    """
    try:
        user_id = current_user["id"]
        results = execute_all(GET_USER_PROFILE_PICTURES, {
            "user_id": user_id,
            "limit": limit,
            "offset": offset
        })
        
        pictures = []
        for result in results:
            pictures.append({
                "profile_pic_id": result["profile_pic_id"],
                "urls": {
                    "original": storage_service.get_public_url(result["original_key"]),
                    "thumbnail": storage_service.get_public_url(result["thumbnail_key"])
                },
                "is_current": result["is_current"],
                "width": result["width"],
                "height": result["height"],
                "created_at": result["created_at"]
            })
        
        return {
            "status": "success",
            "user_id": user_id,
            "profile_pictures": pictures,
            "count": len(pictures),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get profile picture history: {str(e)}"
        )


@router.delete("/profile-picture/{profile_pic_id}")
async def delete_profile_picture(
    profile_pic_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Soft delete a profile picture
    Only the owner can delete their profile picture
    """
    try:
        user_id = current_user["id"]
        
        result = execute_returning_one(SOFT_DELETE_PROFILE_PICTURE, {
            "profile_pic_id": profile_pic_id,
            "user_id": user_id
        })
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile picture not found or you don't have permission to delete it"
            )
        
        return {
            "status": "success",
            "message": "Profile picture deleted successfully",
            "profile_pic_id": profile_pic_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete profile picture: {str(e)}"
        )


@router.get("/profile-picture/download/{profile_pic_id}")
async def download_profile_picture(
    profile_pic_id: str,
    variant: str = "thumbnail",  # 'original' or 'thumbnail',
    current_user: dict = Depends(get_current_user)
):
    """
    Download profile picture by profile_pic_id
    Supports: original or thumbnail variant
    """
    try:
        result = execute_returning_one(GET_PROFILE_PICTURE_BY_ID, {"profile_pic_id": profile_pic_id})
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile picture not found"
            )
        
        # Determine which key to use
        key = result["original_key"] if variant == "original" else result["thumbnail_key"]
        
        # Download from R2
        file_bytes, content_type = storage_service.download_from_r2(key)
        
        return StreamingResponse(
            io.BytesIO(file_bytes),
            media_type=content_type,
            headers={
                "Content-Disposition": f'inline; filename="{profile_pic_id}_{variant}.jpg"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download profile picture: {str(e)}"
        )
