
USERS_TABLE_CREATE = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        email TEXT,
        password TEXT, 
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
"""

USERS_SELECT_ALL = '''SELECT id,username,email, 
                        datetime(created_at, '+5 hours', '30 minutes') AS created_at_ist,
                        datetime(updated_at, '+5 hours', '30 minutes') AS updated_at_ist  
                    FROM users '''

USER_INFO = '''SELECT id,username,email, 
                    datetime(created_at, '+5 hours', '30 minutes') AS created_at_ist,
                    datetime(updated_at, '+5 hours', '30 minutes') AS updated_at_ist  
                FROM users WHERE id=:id'''

USERS_INSERT = "INSERT INTO users (username, email, password) VALUES (:username, :email, :password)"


