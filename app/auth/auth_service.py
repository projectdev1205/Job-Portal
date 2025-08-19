from __future__ import annotations
from typing import Optional, Literal
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import User
from app.utils.security import hash_password, verify_password, create_access_token


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def _get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def _ensure_unique_email(self, email: str):
        if self._get_user_by_email(email):
            raise HTTPException(status_code=400, detail="Email already registered")

    def register_user(
        self, *, name: str, email: str, password: str, role: Literal["business", "applicant"]
    ) -> User:
        self._ensure_unique_email(email)
        user = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role=role,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def authenticate_user(self, *, email: str, password: str) -> User:
        user = self._get_user_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return user

    def issue_token(self, user: User) -> str:
        return create_access_token(sub=user.email, extra={"role": user.role, "uid": user.id})

    def upsert_google_user(
        self,
        *,
        email: str,
        name: Optional[str],
        default_role: Literal["business", "applicant"] = "applicant",
        random_pw_hash: Optional[str] = None,
    ) -> User:
        """
        Create user if not exists, otherwise return existing.
        For first-time Google users, we set a random password hash to prevent local login.
        """
        user = self._get_user_by_email(email)
        if user:
            return user

        # Guard values
        display_name = name or email.split("@")[0]
        if not random_pw_hash:
            # If caller didn't pre-hash, store a clearly unusable password
            # (they can set a real one later via a password-set flow)
            from app.utils.security import hash_password as _hash
            random_pw_hash = _hash(email + ":google-only")

        user = User(
            name=display_name,
            email=email,
            password_hash=random_pw_hash,
            role=default_role,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
