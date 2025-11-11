import re

EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

def validate_signup_data(data:dict):
    if not data:
        raise ValueError("No Input Data Provided")
    
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        raise ValueError("Email and Password are required")
    
    if not isinstance(email,str) or not isinstance(password, str):
        raise ValueError("Email and Password must be a string")
    
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    
    if not re.match(EMAIL_REGEX,email):
        raise ValueError("Invalid email address format")
    
    return {
        'email':email.strip().lower(),
        'password':password,
    }

def validate_login_data(data:dict):
    if not data:
        raise ValueError("No input data was provided")
    
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        raise ValueError("Email and Password are required")
    
    return {
        "email" : email.strip().lower(),
        "password":password
    }