"""Authentication and Security Module for Talentra Backend.

Implements Supabase Auth JWT verification, claim parsing, and role-based
authorization dependencies for FastAPI endpoints.
"""

import time
import logging
from typing import Optional, Dict, Any, List, Callable
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.schemas.auth import AuthClaims

logger = logging.getLogger(__name__)

# HTTP Bearer scheme with automatic 401 on missing token
oauth2_scheme = HTTPBearer(auto_error=True)


def verify_supabase_token(token: str) -> Dict[str, Any]:
    """Verify and decode a Supabase Auth access token using project JWT secret.
    
    Args:
        token: Raw JWT string from Authorization: Bearer <token>.
        
    Returns:
        Decoded payload dictionary.
        
    Raises:
        HTTPException: 401 Unauthorized if expired, malformed, or invalid signature.
    """
    secret = settings.SUPABASE_JWT_SECRET
    algorithm = settings.SUPABASE_JWT_ALGORITHM

    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=[algorithm],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "require": ["sub", "exp"],
            },
            audience=["authenticated", "anon"],
        )
        return payload
    except ExpiredSignatureError:
        logger.warning("Supabase token verification failed: expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Please re-authenticate.",
            headers={"WWW-Authenticate": "Bearer error=\"invalid_token\", error_description=\"The token has expired\""},
        )
    except InvalidTokenError as e:
        logger.warning("Supabase token verification failed: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer error=\"invalid_token\", error_description=\"Invalid credentials\""},
        )
    except Exception as e:
        logger.error("Unexpected error during token verification: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def create_test_supabase_token(
    sub: str,
    email: Optional[str] = None,
    expires_in: int = 3600,
    role: str = "authenticated",
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate a valid signed Supabase JWT for unit/integration testing."""
    now = int(time.time())
    payload = {
        "sub": sub,
        "aud": "authenticated",
        "role": role,
        "email": email or f"user_{sub[:8]}@example.com",
        "iat": now,
        "exp": now + expires_in,
        "app_metadata": {"provider": "email", "providers": ["email"]},
        "user_metadata": {},
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(
        payload,
        settings.SUPABASE_JWT_SECRET,
        algorithm=settings.SUPABASE_JWT_ALGORITHM,
    )


async def get_current_auth_subject(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
) -> AuthClaims:
    """FastAPI dependency to extract and verify the Supabase Auth subject.
    
    Used for endpoints where the user might not yet have an internal Talentra
    record (e.g. registration / onboarding).
    """
    token = credentials.credentials
    payload = verify_supabase_token(token)
    return AuthClaims(**payload)


async def get_current_user(
    claims: AuthClaims = Depends(get_current_auth_subject),
    db: Session = Depends(get_db),
):
    """FastAPI dependency to resolve the authenticated Talentra User record.
    
    Raises:
        HTTPException: 401 if user identity has not completed registration.
    """
    from app.models.user import User

    user = db.query(User).filter(User.provider_subject == claims.sub).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account not registered. Please complete registration first.",
        )
    if user.account_status_code_id != 1:  # Non-active
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive or suspended.",
        )
    return user


def require_role(required_role: str) -> Callable:
    """Dependency factory checking whether the current user has the specified role assigned.
    
    Args:
        required_role: The role code required (e.g. 'CANDIDATE', 'ADMIN', 'SUPER_ADMIN').
    """
    async def role_checker(
        user = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        from app.models.user import UserRoleAssignment, Role

        assignment = (
            db.query(UserRoleAssignment)
            .join(Role, UserRoleAssignment.role_id == Role.id)
            .filter(
                UserRoleAssignment.user_id == user.id,
                Role.role_code == required_role,
                UserRoleAssignment.revoked_at.is_(None),
            )
            .first()
        )
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: User does not possess the required '{required_role}' role.",
            )
        return user

    return role_checker
