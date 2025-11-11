from app.extensions import db, bcrypt, mail
from app.auth.models import User, RefreshToken, OneTimeToken
from flask_jwt_extended import create_access_token, create_refresh_token
from flask_mail import Message
from flask import current_app
from datetime import datetime, timedelta, timezone  # ✅ use class-level imports
import hashlib
import secrets
from pydantic import BaseModel, EmailStr, constr, ValidationError


def send_verification_email(user, token):
    verification_url = f"http://localhost:5173/verify-email?token={token}"

    msg = Message(
        subject="Welcome! Please verify your email.",
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user.email],
        body=(
            f"Welcome to the Legal AI Analyzer!\n\n"
            f"Please click the link to verify your email address:\n{verification_url}\n\n"
            f"If you did not sign up for this account, you can safely ignore this email."
        ),
        html=(
            f"<p>Welcome to the Legal AI Analyzer!</p>"
            f"<p>Please click the link to verify your email address:</p>"
            f"<p><a href='{verification_url}'>Verify My Email</a></p>"
            f"<p>If you did not sign up for this account, you can safely ignore this email.</p>"
        )
    )

    try:
        mail.send(msg)
    except Exception as e:
        print(f"Error sending email: {e}")
        pass


def create_and_send_one_time_token(user, token_type):
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    expires = datetime.now(timezone.utc) + timedelta(hours=1)  # ✅ timezone-aware expiration

    new_token_entry = OneTimeToken(
        token_hash=token_hash,
        user_id=user.id,
        type=token_type,
        expires_at=expires
    )
    db.session.add(new_token_entry)
    db.session.commit()

    if token_type == 'email_verification':
        send_verification_email(user, raw_token)

    return raw_token


def register_user(email, password):
    try:
        if User.query.filter_by(email=email).first():
            raise ValueError("Email address already in use")

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        new_user = User(
            email=email,
            hashed_password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        create_and_send_one_time_token(new_user, 'email_verification')

        return new_user

    except Exception as e:
        db.session.rollback()
        import traceback
        print("------ DB Commit Failed ------")
        print("Error type:", type(e))
        print("Error message:", str(e))
        traceback.print_exc()
        print("--------------------------------")
        raise


def login_user(email, password):
    user = User.query.filter_by(email=email).first()

    if not user or not bcrypt.check_password_hash(user.hashed_password, password):
        raise ValueError("Invalid email or password.")
    
    return user

def store_refresh_token(jti, user_id):
    expires = datetime.utcnow() + timedelta(days=30)
    
    new_refresh_entry = RefreshToken(
        jti=jti,
        user_id=user_id,
        expires_at=expires
    )
    db.session.add(new_refresh_entry)
    db.session.commit()


def logout_user(raw_refresh_token: str):
    if not raw_refresh_token:
        raise ValueError("No refresh token provided")

    token_hash = hashlib.sha256(raw_refresh_token.encode()).hexdigest()
    token_entry = RefreshToken.query.filter_by(token_hash=token_hash).first()

    if not token_entry:
        raise ValueError("Invalid token or already logged out")

    db.session.delete(token_entry)
    db.session.commit()

def logout_user_by_jti(jti: str):
    """
    Revokes a refresh token by deleting its JTI from the database.
    """
    token_entry = RefreshToken.query.filter_by(jti=jti).first()
    
    if not token_entry:
        raise ValueError("Token is invalid or already revoked.")

    db.session.delete(token_entry)
    db.session.commit()

def verify_email_token(raw_token: str):
    if not raw_token:
        raise ValueError("Token is missing")

    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    token_entry = OneTimeToken.query.filter_by(token_hash=token_hash).first()

    if not token_entry:
        raise ValueError("Invalid or expired token")

    if token_entry.type != 'email_verification':
        raise ValueError("Invalid token type")

    # ✅ Compare aware timestamps
    if datetime.now(timezone.utc) > token_entry.expires_at.replace(tzinfo=timezone.utc):
        db.session.delete(token_entry)
        db.session.commit()
        raise ValueError("Token has expired")

    user = User.query.get(token_entry.user_id)
    if not user:
        raise ValueError("User not found")

    user.is_email_verified = True
    db.session.delete(token_entry)
    db.session.commit()

    return user
