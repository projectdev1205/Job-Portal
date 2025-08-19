from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from backend.app.config import settings

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(p: str) -> str:
    return _pwd.hash(p)

def verify_password(p: str, hashed: str) -> bool:
    return _pwd.verify(p, hashed)

def create_access_token(sub: str, extra: dict | None = None) -> str:
    claims = {
        "sub": sub,
        "exp": datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes),
        "iat": datetime.utcnow(),
    }
    if extra:
        claims.update(extra)
    return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)
