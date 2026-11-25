"""
Authentication and User schemas.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.core.security import UserRole


class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    phone: Optional[str] = Field(None, max_length=30)
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.CITIZEN
    department_id: Optional[str] = None


class UserLoginRequest(BaseModel):
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str
    role: str
    department_id: Optional[str] = None
    user_id: str
    name: str


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    role: str
    department_id: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
