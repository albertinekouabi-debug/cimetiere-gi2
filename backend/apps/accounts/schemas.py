import uuid
from datetime import datetime
from typing import Optional
from ninja import Schema
from pydantic import field_validator


class LoginIn(Schema):
    email: str
    password: str


class TokenOut(Schema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshIn(Schema):
    refresh_token: str


class ProfileOut(Schema):
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    phone: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LoginOut(Schema):
    tokens: TokenOut
    profile: ProfileOut


class UserCreateIn(Schema):
    email: str
    password: str
    full_name: str
    role: str = "agent"
    phone: Optional[str] = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        if v not in ("admin", "gestionnaire", "agent"):
            raise ValueError("Rôle invalide")
        return v


class UserUpdateIn(Schema):
    full_name: Optional[str] = None
    role: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class PasswordChangeIn(Schema):
    old_password: str
    new_password: str


class AdminPasswordResetIn(Schema):
    new_password: str
