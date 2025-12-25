# from jose import jwt, JWTError
from db_config import get_db_connection, execute_query, get_data, return_update , execute_all
import re
from datetime import datetime, date



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

def check_mobile(mobile):
    mobile = execute_all( f"SELECT id FROM vi.users WHERE mobile_number = '{mobile}'; ")
    if mobile: return {"status" : "failure", "message" : "Mobile number already registered"}
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


def details_check(payload):
    if payload.get("type")=="mobile":
        phone = payload.get("phone")
        phone_pattern = r'^\+?\d{10,15}$'
        if not phone or not re.match(phone_pattern, phone):
            return {"status": "failure", "message": "Invalid phone number"}
        check = check_mobile(phone)
        if check.get("status")!="success": return check
        
        data = {"phone": mask_phone(phone)}
        
    elif payload.get("type")=="register":
        if payload.get("dob"):
            dob = datetime.strptime(payload.get("dob"), "%d-%m-%Y").date()
            today = date.today()

            age = today.year - dob.year - (
                (today.month, today.day) < (dob.month, dob.day)
            )
            if age<16:
                return {"status": "failure", "message": "You must be at least 16 years old to register"}
        else: 
            return {"status": "failure", "message": "Date of birth is required"}
        data = {"age" : age , "gender" : payload.get("gender")}
    
    else:
        return {"status": "failure", "message": "Invalid request"}

    return {"status": "success", "data": data}



def mask_phone(phone: str) -> str:
    if len(phone) <= 4:
        return "*" * len(phone)
    return "*" * (len(phone) - 4) + phone[-4:]









