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
        
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

"""

USERS_SELECT_ALL = f'''SELECT id, username, email, password,
                        (created_at + INTERVAL '5 hours 30 minutes') AS created_at_ist,
                        (updated_at + INTERVAL '5 hours 30 minutes') AS updated_at_ist
                    FROM vi.users '''

USER_INFO = F'''SELECT id, username, email,
                    (created_at + INTERVAL '5 hours 30 minutes') AS created_at_ist,
                    (updated_at + INTERVAL '5 hours 30 minutes') AS updated_at_ist
                FROM vi.users WHERE id=:id'''

USERS_INSERT = f"""
INSERT INTO vi.users (username, email, password)
VALUES (%(username)s, %(email)s, %(password)s)
RETURNING id
"""


LOGIN_USER = f'''SELECT id,username,email,password
                FROM vi.users WHERE username=%(username)s ;'''

LOGIN_USER_WITH_EMAIL = f'''SELECT id,username,email,password,
                    created_at + interval '5 hours 30 minutes' AS created_at_ist,
                    updated_at + interval '5 hours 30 minutes' AS updated_at_ist
                FROM vi.users WHERE email = %(email)s '''


