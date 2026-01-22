# Media Upload System Architecture

## System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT (Frontend)                            │
│                                                                       │
│  [User selects image] → [Upload button clicked]                     │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            │ POST /media/upload
                            │ (multipart/form-data)
                            │ Authorization: Bearer {token}
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND (routes.py)                       │
│                                                                       │
│  1. Authenticate user (JWT)                                          │
│  2. Validate file type (JPEG/PNG/WebP)                              │
│  3. Check file size (<10MB)                                         │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            │ Pass to storage service
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  STORAGE SERVICE (storage.py)                        │
│                                                                       │
│  4. Generate unique media_id                                         │
│     → "20260113123045_a1b2c3d4e5f6"                                 │
│                                                                       │
│  5. Validate image integrity (PIL)                                   │
│                                                                       │
│  6. Create variants:                                                 │
│     ┌─────────────────────────────────────────┐                     │
│     │ Original (1920x1080) → 2.5MB            │                     │
│     │ Medium (640x640)     → 150KB            │                     │
│     │ Thumbnail (150x150)  → 15KB             │                     │
│     └─────────────────────────────────────────┘                     │
│                                                                       │
│  7. Optimize (JPEG compression 85-90%)                              │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            │ Upload to cloud
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    CLOUDFLARE R2 STORAGE                             │
│                                                                       │
│  media/                                                              │
│  └── 123/                          (user_id)                        │
│      ├── original/                                                   │
│      │   └── 20260113123045_a1b2c3d4e5f6.jpg                       │
│      ├── medium/                                                     │
│      │   └── 20260113123045_a1b2c3d4e5f6_medium.jpg                │
│      └── thumbnail/                                                  │
│          └── 20260113123045_a1b2c3d4e5f6_thumb.jpg                 │
│                                                                       │
│  Cache-Control: public, max-age=31536000                            │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            │ Store metadata
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      POSTGRESQL DATABASE                             │
│                                                                       │
│  vi.media_uploads                                                    │
│  ┌────────────────────────────────────────────────────────┐         │
│  │ id: 1                                                   │         │
│  │ media_id: "20260113123045_a1b2c3d4e5f6"               │         │
│  │ user_id: 123                                           │         │
│  │ file_type: "image"                                     │         │
│  │ mime_type: "image/jpeg"                                │         │
│  │ original_key: "media/123/original/..."                │         │
│  │ thumbnail_key: "media/123/thumbnail/..."              │         │
│  │ medium_key: "media/123/medium/..."                    │         │
│  │ width: 1920                                            │         │
│  │ height: 1080                                           │         │
│  │ file_size_bytes: 2458624                              │         │
│  │ upload_status: "completed"                             │         │
│  │ is_deleted: false                                      │         │
│  │ created_at: 2026-01-13 12:30:45                       │         │
│  └────────────────────────────────────────────────────────┘         │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            │ Return response
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         RESPONSE TO CLIENT                           │
│                                                                       │
│  {                                                                   │
│    "status": "success",                                             │
│    "media_id": "20260113123045_a1b2c3d4e5f6",                      │
│    "urls": {                                                        │
│      "original": "https://cdn.../original/...",                    │
│      "medium": "https://cdn.../medium/...",                        │
│      "thumbnail": "https://cdn.../thumbnail/..."                   │
│    },                                                               │
│    "width": 1920,                                                   │
│    "height": 1080,                                                  │
│    "file_size_bytes": 2458624                                      │
│  }                                                                   │
└─────────────────────────────────────────────────────────────────────┘
```

## Retrieval Flow

```
CLIENT REQUEST
    │
    │ GET /media/{media_id}
    │
    ▼
BACKEND
    │
    ├─→ Query PostgreSQL for metadata
    │   (media_id → storage keys)
    │
    └─→ Generate CDN URLs
        │
        ▼
    RESPONSE
        {
          "urls": {
            "original": "https://cdn.../original/...",
            "medium": "https://cdn.../medium/...",
            "thumbnail": "https://cdn.../thumbnail/..."
          }
        }
```

## Profile Picture Flow

```
UPLOAD PROFILE PICTURE
    │
    ├─→ Upload image (same as regular upload)
    │   └─→ Get media_id
    │
    └─→ Update profile_pictures table
        │
        ├─→ Set previous profile pictures to is_current=false
        │
        └─→ Insert new record with is_current=true
```

## Data Relationships

```
users (id)
    │
    ├─→ media_uploads (user_id)
    │   └─→ Stores all uploaded media
    │
    └─→ profile_pictures (user_id)
        └─→ Tracks profile picture history
            └─→ References media_uploads (media_id)
```

## Why This Architecture?

### 1. Separation of Concerns
- **routes.py**: API endpoints & validation
- **storage.py**: File processing & R2 interaction
- **models.py**: Data validation
- **queries.py**: Database operations

### 2. Scalability
- R2 handles storage & CDN
- PostgreSQL handles metadata
- Stateless API (can scale horizontally)

### 3. Performance
- CDN caching (1 year)
- Image variants (right size for use case)
- Database indexes (fast queries)
- Optimized JPEG compression

### 4. Reliability
- Soft deletes (data preservation)
- Transaction safety
- Error handling at each layer
- Validation before processing

## Key Components

### Media ID Generator
```python
timestamp = "20260113123045"  # YYYYMMDDHHmmss
uuid = "a1b2c3d4e5f6"        # 12 chars
media_id = f"{timestamp}_{uuid}"
```

### Image Processor
```python
Original → Validate → Create variants → Optimize → Upload
```

### Storage Keys
```python
f"media/{user_id}/original/{media_id}.jpg"
f"media/{user_id}/medium/{media_id}_medium.jpg"
f"media/{user_id}/thumbnail/{media_id}_thumb.jpg"
```

### URL Generator
```python
f"{R2_PUBLIC_URL}/{storage_key}"
```

## Security Layers

```
1. JWT Authentication
   ↓
2. File Type Validation
   ↓
3. File Size Check
   ↓
4. Image Integrity Verification
   ↓
5. Dimension Limits
   ↓
6. User Ownership (for deletes)
```

## Database Indexes

```sql
-- Fast lookups by media_id
CREATE INDEX idx_media_uploads_media_id ON vi.media_uploads (media_id);

-- Fast user media queries
CREATE INDEX idx_media_uploads_user_id ON vi.media_uploads (user_id);

-- Chronological sorting
CREATE INDEX idx_media_uploads_created_at ON vi.media_uploads (created_at DESC);

-- Profile picture queries
CREATE INDEX idx_profile_pictures_is_current ON vi.profile_pictures (user_id, is_current);
```

## Storage Optimization

```
Original:   1920x1080 → 2.5MB  (100%)
Medium:     640x640   → 150KB  (6%)
Thumbnail:  150x150   → 15KB   (0.6%)
────────────────────────────────────
Total:                  2.665MB (106.6% of original)

But saves bandwidth:
- Lists use thumbnail: 99.4% savings
- Feed uses medium: 94% savings
```
