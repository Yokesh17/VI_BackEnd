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