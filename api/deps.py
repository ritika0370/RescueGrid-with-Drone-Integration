"""
FastAPI Authentication, RBAC, and Database Session Dependencies.
"""
from typing import List, Optional
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import UserRole, decode_jwt_token
from app.models.user import User

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Validate bearer token and retrieve authenticated user."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_jwt_token(credentials.credentials)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload.")

    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or disabled.")

    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Retrieve user if valid token provided; returns None for anonymous citizen requests."""
    if not credentials or not credentials.credentials:
        return None
    try:
        payload = decode_jwt_token(credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            return None
        res = await db.execute(select(User).where(User.id == user_id))
        return res.scalar_one_or_none()
    except Exception:
        return None


def require_roles(allowed_roles: List[UserRole]):
    """Enforce Role-Based Access Control."""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        allowed_str = [r.value for r in allowed_roles]
        if current_user.role not in allowed_str and current_user.role != UserRole.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires one of {allowed_str} roles.",
            )
        return current_user
    return role_checker


require_officer = require_roles([UserRole.OFFICER, UserRole.DISPATCHER, UserRole.ADMIN])
require_pilot = require_roles([UserRole.PILOT, UserRole.ADMIN])
require_admin = require_roles([UserRole.ADMIN])
