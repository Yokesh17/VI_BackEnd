# SQL queries for media operations

# ============================================
# MEDIA UPLOADS QUERIES (General media: images, videos)
# ============================================

# Insert new media upload (original file only)
INSERT_MEDIA_UPLOAD = """
    INSERT INTO vi.media_uploads (
        media_id, user_id, file_type, mime_type, original_filename,
        file_size_bytes, storage_key, width, height, duration_seconds, upload_status
    ) VALUES (
        %(media_id)s, %(user_id)s, %(file_type)s, %(mime_type)s, %(original_filename)s,
        %(file_size_bytes)s, %(storage_key)s, %(width)s, %(height)s, %(duration_seconds)s, %(upload_status)s
    )
    RETURNING id, media_id, created_at;
"""

# Get media by media_id
GET_MEDIA_BY_ID = """
    SELECT 
        id, media_id, user_id, file_type, mime_type, original_filename,
        file_size_bytes, storage_key, width, height, duration_seconds,
        upload_status, is_deleted, created_at
    FROM vi.media_uploads
    WHERE media_id = %(media_id)s AND is_deleted = FALSE;
"""

# Get all media for a user
GET_USER_MEDIA = """
    SELECT 
        id, media_id, user_id, file_type, mime_type, original_filename,
        file_size_bytes, storage_key, width, height, duration_seconds,
        upload_status, created_at
    FROM vi.media_uploads
    WHERE user_id = %(user_id)s AND is_deleted = FALSE
    ORDER BY created_at DESC
    LIMIT %(limit)s OFFSET %(offset)s;
"""

# Soft delete media
SOFT_DELETE_MEDIA = """
    UPDATE vi.media_uploads
    SET is_deleted = TRUE, deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
    WHERE media_id = %(media_id)s AND user_id = %(user_id)s
    RETURNING media_id, storage_key;
"""

# Update media status
UPDATE_MEDIA_STATUS = """
    UPDATE vi.media_uploads
    SET upload_status = %(status)s, updated_at = CURRENT_TIMESTAMP
    WHERE media_id = %(media_id)s
    RETURNING media_id, upload_status;
"""


# ============================================
# PROFILE PICTURES QUERIES (with thumbnails)
# ============================================

# Insert new profile picture (marks previous as not current)
INSERT_PROFILE_PICTURE = """
    WITH deactivate_old AS (
        UPDATE vi.profile_pictures
        SET is_current = FALSE, updated_at = CURRENT_TIMESTAMP
        WHERE user_id = %(user_id)s AND is_current = TRUE
    )
    INSERT INTO vi.profile_pictures (
        profile_pic_id, user_id, mime_type, original_filename,
        file_size_bytes, original_key, thumbnail_key, width, height, is_current
    ) VALUES (
        %(profile_pic_id)s, %(user_id)s, %(mime_type)s, %(original_filename)s,
        %(file_size_bytes)s, %(original_key)s, %(thumbnail_key)s, %(width)s, %(height)s, TRUE
    )
    RETURNING id, profile_pic_id, created_at;
"""

# Get current profile picture for a user
GET_CURRENT_PROFILE_PICTURE = """
    SELECT 
        id, profile_pic_id, user_id, mime_type, original_filename,
        file_size_bytes, original_key, thumbnail_key, width, height,
        is_current, created_at
    FROM vi.profile_pictures
    WHERE user_id = %(user_id)s AND is_current = TRUE AND is_deleted = FALSE
    LIMIT 1;
"""

# Get profile picture by profile_pic_id
GET_PROFILE_PICTURE_BY_ID = """
    SELECT 
        id, profile_pic_id, user_id, mime_type, original_filename,
        file_size_bytes, original_key, thumbnail_key, width, height,
        is_current, created_at
    FROM vi.profile_pictures
    WHERE profile_pic_id = %(profile_pic_id)s AND is_deleted = FALSE;
"""

# Get all profile pictures for a user (history)
GET_USER_PROFILE_PICTURES = """
    SELECT 
        id, profile_pic_id, user_id, mime_type, original_filename,
        file_size_bytes, original_key, thumbnail_key, width, height,
        is_current, created_at
    FROM vi.profile_pictures
    WHERE user_id = %(user_id)s AND is_deleted = FALSE
    ORDER BY created_at DESC
    LIMIT %(limit)s OFFSET %(offset)s;
"""

# Soft delete profile picture
SOFT_DELETE_PROFILE_PICTURE = """
    UPDATE vi.profile_pictures
    SET is_deleted = TRUE, is_current = FALSE, updated_at = CURRENT_TIMESTAMP
    WHERE profile_pic_id = %(profile_pic_id)s AND user_id = %(user_id)s
    RETURNING profile_pic_id, original_key, thumbnail_key;
"""

# Set a specific profile picture as current
SET_PROFILE_PICTURE_AS_CURRENT = """
    WITH deactivate_old AS (
        UPDATE vi.profile_pictures
        SET is_current = FALSE, updated_at = CURRENT_TIMESTAMP
        WHERE user_id = %(user_id)s AND is_current = TRUE
    )
    UPDATE vi.profile_pictures
    SET is_current = TRUE, updated_at = CURRENT_TIMESTAMP
    WHERE profile_pic_id = %(profile_pic_id)s AND user_id = %(user_id)s AND is_deleted = FALSE
    RETURNING profile_pic_id;
"""
