from dotenv import load_dotenv
import os

load_dotenv()

S = os.getenv("DB_SCHEMA.", "")


USERS_TABLE_CREATE = f"""
    CREATE TABLE IF NOT EXISTS vi.users (
        id SERIAL PRIMARY KEY,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        email_verified BOOLEAN DEFAULT FALSE,
        mobile_verified BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
"""

USERS_INDEX_CREATE = f"""
CREATE INDEX IF NOT EXISTS idx_users_username ON vi.users (username);
CREATE INDEX IF NOT EXISTS idx_users_email ON vi.users (email);
"""


USER_DETAILS_CREATE = f"""
    CREATE TABLE IF NOT EXISTS vi.user_details (
        user_id INTEGER PRIMARY KEY,
        full_name TEXT NOT NULL,
        bio TEXT,
        gender TEXT,
        date_of_birth DATE,
        age INTEGER,                     -- optional, or calculate from DOB
        mobile_number TEXT,
        website TEXT,
        interests TEXT,                  -- JSON string or comma-separated
        country TEXT,
        profile_pic_dms TEXT,
        is_private BOOLEAN DEFAULT FALSE,
        last_seen TIMESTAMP WITH TIME ZONE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        
        FOREIGN KEY (user_id) REFERENCES vi.users(id)
    );

"""
Users_details_index_create = f"""
CREATE INDEX IF NOT EXISTS idx_user_details_full_name ON vi.user_details (full_name);
CREATE INDEX IF NOT EXISTS idx_user_details_mobile_number ON vi.user_details (mobile_number);
CREATE INDEX IF NOT EXISTS idx_user_details_user_id ON vi.user_details (user_id);
"""



USER_CONNECTIONS_CREATE = f"""
CREATE TABLE vi.user_connections (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    connected_user_id INTEGER NOT NULL,
    status TEXT CHECK (status IN ('pending', 'accepted', 'blocked')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id, connected_user_id),
    FOREIGN KEY (user_id) REFERENCES vi.users(id),
    FOREIGN KEY (connected_user_id) REFERENCES vi.users(id)
);
"""

USER_INTERESTS_CREATE = f"""
CREATE TABLE vi.user_interests (
    user_id INTEGER,
    interest TEXT,
    PRIMARY KEY (user_id, interest),
    FOREIGN KEY (user_id) REFERENCES vi.users(id)
);
"""





# uploads table

# Table to store all media uploads (images, videos, etc.) - ORIGINAL FILES ONLY
MEDIA_UPLOADS_TABLE = """
    CREATE TABLE IF NOT EXISTS vi.media_uploads (
        id SERIAL PRIMARY KEY,
        media_id VARCHAR(100) UNIQUE NOT NULL,  -- Unique identifier (UUID)
        user_id INTEGER NOT NULL,
        file_type VARCHAR(50) NOT NULL,  -- 'image', 'video', 'document'
        mime_type VARCHAR(100) NOT NULL,  -- 'image/jpeg', 'image/png', 'video/mp4', etc.
        original_filename VARCHAR(255),
        file_size_bytes BIGINT NOT NULL,
        
        -- Storage path for original file only
        storage_key TEXT NOT NULL,  -- R2 storage key for original file
        
        -- Metadata
        width INTEGER,  -- Original width for images/videos
        height INTEGER,  -- Original height for images/videos
        duration_seconds INTEGER,  -- For videos
        
        -- Status and tracking
        upload_status VARCHAR(20) DEFAULT 'completed',  -- 'processing', 'completed', 'failed'
        is_deleted BOOLEAN DEFAULT FALSE,
        
        -- Timestamps
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        deleted_at TIMESTAMP WITH TIME ZONE,
        
        FOREIGN KEY (user_id) REFERENCES vi.users(id) ON DELETE CASCADE
    );
"""

MEDIA_UPLOADS_INDEXES = """
    CREATE INDEX IF NOT EXISTS idx_media_uploads_media_id ON vi.media_uploads (media_id);
    CREATE INDEX IF NOT EXISTS idx_media_uploads_user_id ON vi.media_uploads (user_id);
    CREATE INDEX IF NOT EXISTS idx_media_uploads_created_at ON vi.media_uploads (created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_media_uploads_file_type ON vi.media_uploads (file_type);
"""

# Table for profile pictures with thumbnails - SELF-CONTAINED
PROFILE_PICTURES_TABLE = """
    CREATE TABLE IF NOT EXISTS vi.profile_pictures (
        id SERIAL PRIMARY KEY,
        profile_pic_id VARCHAR(100) UNIQUE NOT NULL,  -- Unique identifier for profile picture
        user_id INTEGER NOT NULL,
        
        -- File metadata
        mime_type VARCHAR(100) NOT NULL,
        original_filename VARCHAR(255),
        file_size_bytes BIGINT NOT NULL,
        
        -- Storage keys for original and thumbnail
        original_key TEXT NOT NULL,  -- R2 storage key for original profile image
        thumbnail_key TEXT NOT NULL,  -- R2 storage key for thumbnail (150x150)
        
        -- Image dimensions
        width INTEGER,
        height INTEGER,
        
        -- Status
        is_current BOOLEAN DEFAULT TRUE,
        is_deleted BOOLEAN DEFAULT FALSE,
        
        -- Timestamps
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        
        FOREIGN KEY (user_id) REFERENCES vi.users(id) ON DELETE CASCADE
    );
"""

PROFILE_PICTURES_INDEXES = """
    CREATE INDEX IF NOT EXISTS idx_profile_pictures_profile_pic_id ON vi.profile_pictures (profile_pic_id);
    CREATE INDEX IF NOT EXISTS idx_profile_pictures_user_id ON vi.profile_pictures (user_id);
    CREATE INDEX IF NOT EXISTS idx_profile_pictures_is_current ON vi.profile_pictures (user_id, is_current);
"""








