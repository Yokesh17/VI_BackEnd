# from jose import jwt, JWTError
from db_config import get_db_connection, execute_query, get_data, return_update , execute_all
import re



def validate_user(p):
    user_check = check_user(p.username)
    if user_check['status']=="failure": return user_check

    email_check = check_email(p.email)
    if email_check['status']=='failure': return email_check

    password_check = validate_password(p.password, p.password)
    if password_check['status']=="failure" : return password_check

    return {'status' : 'success'}

def check_user(username):
    user = execute_all( f"SELECT id FROM vi.users WHERE username = '{username}'; ")
    if user: return {"status" : "failure", "message" : "Username already registered"}

    return {'status': 'success'}


def check_email(email):
    if is_valid_email(email):
        email = execute_all( f"SELECT id FROM vi.users WHERE email = '{email}'; ")
        if email: return {"status" : "failure", "message" : "Email already registered"}
    else:
        return {"status" : "failure" , "message": "Invalid email"}
    return {'status': 'success'}

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password, confirm_password):
    if password!=confirm_password:
        return {"status": "failure", "message": "Password must match the confirm password"}
    if len(password) < 8:
        return {"status": "failure", "message": "Password must be at least 8 characters long."}
    if not re.search(r"[A-Z]", password):
        return {"status": "failure", "message": "Password must contain at least one uppercase letter."}
    if not re.search(r"[a-z]", password):
        return {"status": "failure", "message": "Password must contain at least one lowercase letter."}
    if not re.search(r"\d", password):
        return {"status": "failure", "message": "Password must contain at least one number."}
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return {"status": "failure", "message": "Password must contain at least one special character."}

    return {'status': 'success'}












