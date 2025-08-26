from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory token blacklist (in production, use Redis or database)
token_blacklist = set()

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(sub: str, extra: Optional[Dict[str, Any]] = None) -> str:
    """Create a JWT access token"""
    to_encode = {"sub": sub, "exp": datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)}
    if extra:
        to_encode.update(extra)
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None

def is_token_blacklisted(token: str) -> bool:
    """Check if a token is blacklisted"""
    return token in token_blacklist

def blacklist_token(token: str) -> None:
    """Add a token to the blacklist"""
    token_blacklist.add(token)

def clear_expired_tokens() -> None:
    """Clear expired tokens from blacklist (call periodically)"""
    # In a real implementation, you'd check token expiration
    # For now, we'll keep it simple with in-memory storage
    pass
