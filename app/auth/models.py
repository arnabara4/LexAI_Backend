import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.extensions import db
from sqlalchemy import Enum as DBEnum

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.Text, unique=True, nullable=False)
    hashed_password = db.Column(db.Text, nullable=True) 
    
    role = db.Column(
        DBEnum('free_user', 'premium_user', name='user_role', create_type=False), 
        nullable=False, 
        default="free_user"
    )
    
    is_email_verified = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = db.Column(db.TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    refresh_tokens = db.relationship(
        'RefreshToken',
        back_populates='user',
        lazy=True,
        cascade="all, delete-orphan"
    )
    one_time_tokens = db.relationship(
        'OneTimeToken', 
        back_populates='user', 
        lazy=True, 
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.email}>"

class RefreshToken(db.Model):
    __tablename__ = 'refresh_tokens'

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), unique=True, nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False) 
    expires_at = db.Column(db.TIMESTAMP(timezone=True), nullable=False)
    created_at = db.Column(db.TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    
    user = db.relationship('User', back_populates='refresh_tokens')

class OneTimeToken(db.Model):
    __tablename__ = 'one_time_tokens'

    id = db.Column(db.Integer, primary_key=True)
    token_hash = db.Column(db.Text, unique=True, nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)

    type = db.Column(
        DBEnum('email_verification', 'password_reset', name='token_type', create_type=False), 
        nullable=False
    )
    
    expires_at = db.Column(db.TIMESTAMP(timezone=True), nullable=False)
    created_at = db.Column(db.TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    user = db.relationship(
        'User',
        back_populates='one_time_tokens'
    )

    def __repr__(self):
        return f"<OneTimeToken {self.type} for User {self.user_id}>"