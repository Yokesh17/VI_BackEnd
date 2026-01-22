import boto3
import os
import uuid
from datetime import datetime
from typing import Tuple, Optional
from PIL import Image
import io
from dotenv import load_dotenv

load_dotenv()

class R2StorageService:
    """
    Cloudflare R2 Storage Service for handling file uploads
    Handles both general media (images/videos) and profile pictures separately
    """
    
    def __init__(self):
        self.bucket_name = os.getenv("R2_BUCKET_NAME")
        self.account_id = os.getenv("R2_ACCOUNT_ID")
        self.access_key = os.getenv("R2_ACCESS_KEY")
        self.secret_key = os.getenv("R2_SECRET_KEY")
        self.public_url = os.getenv("R2_PUBLIC_URL")  # Your R2 public domain
        
        # Initialize R2 client
        self.client = self._get_r2_client()
    
    def _get_r2_client(self):
        """Initialize and return R2 client"""
        session = boto3.session.Session()
        return session.client(
            service_name="s3",
            endpoint_url=f"https://{self.account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )
    
    def generate_media_id(self) -> str:
        """
        Generate unique media ID
        Format: timestamp_uuid (e.g., 20260113_a1b2c3d4e5f6)
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        unique_id = uuid.uuid4().hex[:12]
        return f"{timestamp}_{unique_id}"
    
    def validate_image(self, file_bytes: bytes, max_size_mb: int = 10) -> Tuple[bool, Optional[str], Optional[Image.Image]]:
        """
        Validate image file
        Returns: (is_valid, error_message, PIL_Image)
        """
        # Check file size
        file_size_mb = len(file_bytes) / (1024 * 1024)
        if file_size_mb > max_size_mb:
            return False, f"File size exceeds {max_size_mb}MB limit", None
        
        try:
            img = Image.open(io.BytesIO(file_bytes))
            img.verify()  # Verify it's a valid image
            
            # Reopen image (verify closes the file)
            img = Image.open(io.BytesIO(file_bytes))
            
            # Check image dimensions (optional)
            max_dimension = 4096
            if img.width > max_dimension or img.height > max_dimension:
                return False, f"Image dimensions exceed {max_dimension}x{max_dimension}", None
            
            return True, None, img
        except Exception as e:
            return False, f"Invalid image file: {str(e)}", None
    
    def create_thumbnail(self, img: Image.Image, size: Tuple[int, int] = (150, 150)) -> bytes:
        """Create thumbnail from image"""
        # Convert RGBA to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # Create thumbnail
        img_copy = img.copy()
        img_copy.thumbnail(size, Image.Resampling.LANCZOS)
        
        # Save to bytes
        buffer = io.BytesIO()
        img_copy.save(buffer, format='JPEG', quality=85, optimize=True)
        buffer.seek(0)
        return buffer.getvalue()
    
    def upload_to_r2(self, file_bytes: bytes, key: str, content_type: str) -> bool:
        """Upload file to R2 storage"""
        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=file_bytes,
                ContentType=content_type,
                CacheControl='public, max-age=31536000',  # Cache for 1 year
            )
            return True
        except Exception as e:
            print(f"Error uploading to R2: {e}")
            return False
    
    def delete_from_r2(self, key: str) -> bool:
        """Delete file from R2 storage"""
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return True
        except Exception as e:
            print(f"Error deleting from R2: {e}")
            return False
    
    def get_public_url(self, key: str) -> str:
        """Get public URL for a file"""
        if self.public_url:
            return f"{self.public_url}/{key}"
        else:
            return f"https://{self.bucket_name}.{self.account_id}.r2.cloudflarestorage.com/{key}"
    
    # ============================================
    # MEDIA UPLOADS (Original files only - images/videos)
    # ============================================
    
    def process_and_upload_media(
        self, 
        file_bytes: bytes, 
        media_id: str, 
        user_id: int,
        content_type: str,
        file_type: str = "image"  # 'image' or 'video'
    ) -> dict:
        """
        Process and upload media file (original only, no variants)
        For general media uploads like posts, stories, etc.
        """
        width = None
        height = None
        
        # Validate and get dimensions for images
        if file_type == "image":
            is_valid, error_msg, img = self.validate_image(file_bytes)
            if not is_valid:
                raise ValueError(error_msg)
            width, height = img.size
        
        # Define storage key
        file_ext = content_type.split('/')[-1]
        if file_ext == 'jpeg':
            file_ext = 'jpg'
        
        storage_key = f"media/{user_id}/{media_id}.{file_ext}"
        
        # Upload original
        success = self.upload_to_r2(file_bytes, storage_key, content_type)
        if not success:
            raise Exception("Failed to upload media file")
        
        return {
            "storage_key": storage_key,
            "url": self.get_public_url(storage_key),
            "width": width,
            "height": height,
            "file_size_bytes": len(file_bytes)
        }
    
    # ============================================
    # PROFILE PICTURES (Original + Thumbnail)
    # ============================================
    
    def process_and_upload_profile_picture(
        self, 
        file_bytes: bytes, 
        profile_pic_id: str, 
        user_id: int,
        content_type: str
    ) -> dict:
        """
        Process and upload profile picture with thumbnail
        Creates both original and 150x150 thumbnail
        """
        # Validate image
        is_valid, error_msg, img = self.validate_image(file_bytes)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Get image dimensions
        width, height = img.size
        
        # Define storage keys
        file_ext = content_type.split('/')[-1]
        if file_ext == 'jpeg':
            file_ext = 'jpg'
        
        original_key = f"profile/{user_id}/{profile_pic_id}.{file_ext}"
        thumbnail_key = f"profile/{user_id}/{profile_pic_id}_thumb.jpg"
        
        # Upload original
        success = self.upload_to_r2(file_bytes, original_key, content_type)
        if not success:
            raise Exception("Failed to upload original profile picture")
        
        # Create and upload thumbnail (150x150)
        thumbnail_bytes = self.create_thumbnail(img, (150, 150))
        success = self.upload_to_r2(thumbnail_bytes, thumbnail_key, "image/jpeg")
        if not success:
            raise Exception("Failed to upload thumbnail")
        
        return {
            "original_key": original_key,
            "thumbnail_key": thumbnail_key,
            "original_url": self.get_public_url(original_key),
            "thumbnail_url": self.get_public_url(thumbnail_key),
            "width": width,
            "height": height,
            "file_size_bytes": len(file_bytes)
        }
    
    def download_from_r2(self, key: str) -> Tuple[bytes, str]:
        """Download file from R2 and return bytes and content type"""
        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=key)
            file_bytes = response['Body'].read()
            content_type = response.get('ContentType', 'application/octet-stream')
            return file_bytes, content_type
        except Exception as e:
            raise Exception(f"Error downloading from R2: {e}")


# Singleton instance
storage_service = R2StorageService()
