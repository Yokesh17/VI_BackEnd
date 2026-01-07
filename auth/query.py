USERS_SELECT_ALL = f'''SELECT id, username, email, password,
                        (created_at + INTERVAL '5 hours 30 minutes') AS created_at_ist,
                        (updated_at + INTERVAL '5 hours 30 minutes') AS updated_at_ist
                    FROM vi.users '''

USER_INFO = F'''SELECT id, username, email,
                    (created_at + INTERVAL '5 hours 30 minutes') AS created_at_ist,
                    (updated_at + INTERVAL '5 hours 30 minutes') AS updated_at_ist
                FROM vi.users WHERE id=:id'''

LOGIN_USER = f'''SELECT id,username,email,password
                FROM vi.users WHERE username=%(username)s ;'''

LOGIN_USER_WITH_EMAIL = f'''SELECT id,username,email,password
                FROM vi.users WHERE email = %(email)s '''





USERS_INSERT = f"""
INSERT INTO vi.users (username, email, password)
VALUES (%(username)s, %(email)s, %(password)s)
RETURNING id
"""

USERS_DETAILS_INSERT = f"""
            INSERT INTO vi.user_details 
                (user_id,full_name,gender,date_of_birth,mobile_number)
            VALUES 
                (%(user_id)s,%(full_name)s,%(gender)s,%(date_of_birth)s,%(mobile_number)s)
            RETURNING user_id
            """

USERS_UPDATE_EMAIL_VERIFY = f"""
UPDATE vi.users
SET email_verified = TRUE
WHERE user_id = %(user_id)s;
"""


USERS_UPDATE_PHONE_VERIFY = """
UPDATE vi.users
SET mobile_verified = TRUE
WHERE id = %(user_id)s;
"""

USER_DETAILS_UPDATE_PHONE = """
UPDATE vi.user_details
SET mobile_number = %(mobile_number)s
WHERE user_id = %(user_id)s;
"""



