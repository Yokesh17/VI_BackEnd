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








LOGIN_USER = f'''SELECT id,username,email,password
                FROM vi.users WHERE username=%(username)s ;'''

LOGIN_USER_WITH_EMAIL = f'''SELECT id,username,email,password
                FROM vi.users WHERE email = %(email)s '''


