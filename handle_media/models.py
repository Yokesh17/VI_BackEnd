from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MediaUploadResponse(BaseModel):
    """Response model for successful media upload (original file only)"""
    status: str = "success"
    message: str
    media_id: str
    urls: dict  # Contains only 'original' URL
    file_type: str
    mime_type: str
    file_size_bytes: int
    width: Optional[int] = None
    height: Optional[int] = None
    created_at: datetime

class MediaInfo(BaseModel):
    """Model for media information"""
    id: int
    media_id: str
    user_id: int
    file_type: str
    mime_type: str
    original_filename: Optional[str]
    file_size_bytes: int
    storage_key: str
    width: Optional[int]
    height: Optional[int]
    duration_seconds: Optional[int]
    upload_status: str
    created_at: datetime

class ProfilePictureResponse(BaseModel):
    """Response model for profile picture operations (original + thumbnail)"""
    status: str = "success"
    message: str
    media_id: str  # This is the profile_pic_id
    urls: dict  # Contains 'original' and 'thumbnail' URLs

class MediaDeleteResponse(BaseModel):
    """Response model for media deletion"""
    status: str = "success"
    message: str
    media_id: str

class ErrorResponse(BaseModel):
    """Standard error response"""
    status: str = "error"
    message: str
    details: Optional[str] = None
