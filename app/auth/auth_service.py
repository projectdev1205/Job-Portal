import secrets
import time
from typing import Optional, Literal
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models import User, BusinessProfile
from app.schemas import (
    RegisterIn, LoginIn, UserOut, 
    BusinessRegisterIn, ApplicantRegisterIn, AdminRegisterIn,
    UserOutLegacy, LoginResponse
)
from app.utils.security import (
    hash_password, verify_password, create_access_token
)
from app.utils.logger import get_logger, log_business_operation, log_database_operation, log_security_event, log_performance


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.logger = get_logger("auth_service")
    
    def register_business(self, payload: BusinessRegisterIn) -> UserOut:
        """Register a new business user"""
        existing = self.db.query(User).filter(User.email == payload.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Create user
        user = User(
            first_name=None,  # Not required for business registration
            last_name=None,   # Not required for business registration
            email=payload.email,
            phone_number=payload.phone_number,
            password_hash=hash_password(payload.password),
            role="business",
            email_notifications=payload.email_notifications,
            terms_accepted=payload.terms_accepted,
        )
        self.db.add(user)
        self.db.flush()  # Get user.id without committing
        
        # Create business profile
        business_profile = BusinessProfile(
            user_id=user.id,
            business_name=payload.business_name,
            business_category=payload.business_category,
            business_description=payload.business_description,
            address_line1=payload.address_line1,
            address_line2=payload.address_line2,
            city=payload.city,
            state=payload.state,
            zip_code=payload.zip_code,
        )
        self.db.add(business_profile)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def register_applicant(self, payload: ApplicantRegisterIn) -> UserOut:
        """Register a new applicant user"""
        existing = self.db.query(User).filter(User.email == payload.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        user = User(
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
            phone_number=payload.phone_number,
            date_of_birth=payload.date_of_birth,
            password_hash=hash_password(payload.password),
            role="applicant",
            address_line1=payload.address_line1,
            address_line2=payload.address_line2,
            city=payload.city,
            state=payload.state,
            zip_code=payload.zip_code,
            email_notifications=payload.email_notifications,
            terms_accepted=payload.terms_accepted,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def register_admin(self, payload: AdminRegisterIn) -> UserOut:
        """Register a new admin user"""
        existing = self.db.query(User).filter(User.email == payload.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        user = User(
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
            phone_number=payload.phone_number,
            password_hash=hash_password(payload.password),
            role="admin",
            email_notifications=payload.email_notifications,
            terms_accepted=payload.terms_accepted,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def register_legacy(self, payload: RegisterIn) -> UserOutLegacy:
        """Legacy registration for backward compatibility"""
        existing = self.db.query(User).filter(User.email == payload.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Split name into first_name and last_name
        name_parts = payload.name.strip().split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        user = User(
            first_name=first_name,
            last_name=last_name,
            email=payload.email,
            password_hash=hash_password(payload.password),
            role=payload.role,
            terms_accepted=True,  # Assume legacy registrations accept terms
        )
        self.db.add(user)
        
        # Create business profile if business user
        if payload.role == "business":
            self.db.flush()  # Get user.id
            business_profile = BusinessProfile(
                user_id=user.id,
                business_name=f"{first_name}'s Business",  # Default business name
            )
            self.db.add(business_profile)
        
        self.db.commit()
        self.db.refresh(user)
        
        # Return legacy format
        name_parts = [part for part in [user.first_name, user.last_name] if part]
        name = " ".join(name_parts) if name_parts else "Unknown User"
        return UserOutLegacy(
            id=user.id,
            name=name,
            email=user.email,
            role=user.role
        )
    
    def login(self, payload: LoginIn) -> LoginResponse:
        """Authenticate user and return login response"""
        start_time = time.time()
        self.logger.info(f"Login attempt for email: {payload.email}")
        
        try:
            user = self.db.query(User).filter(User.email == payload.email).first()
            if not user or not verify_password(payload.password, user.password_hash):
                log_security_event("login_failed", email=payload.email, reason="invalid_credentials")
                self.logger.warning(f"Failed login attempt for email: {payload.email}")
                raise HTTPException(status_code=401, detail="Invalid credentials")

            token = create_access_token(sub=user.email, extra={"role": user.role, "uid": user.id})
            name_parts = [part for part in [user.first_name, user.last_name] if part]
            user_name = " ".join(name_parts) if name_parts else "Unknown User"
            
            duration_ms = (time.time() - start_time) * 1000
            log_security_event("login_success", user_id=str(user.id), email=payload.email)
            log_performance("login", duration_ms)
            self.logger.info(f"Successful login for user {user.id} ({payload.email})")
            
            return LoginResponse(
                access_token=token, 
                token_type="bearer",
                user_id=user.id,
                user_role=user.role,
                user_name=user_name
            )
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Login error for {payload.email}: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error")
    
    def create_oauth_user(self, email: str, name: str, role: str) -> User:
        """Create a new user from OAuth authentication"""
        fallback_hash = hash_password(secrets.token_urlsafe(24))
        
        # Split name into first_name and last_name
        name_parts = (name or email.split("@")[0]).strip().split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        
        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password_hash=fallback_hash,   # prevents local login unless they set a password later
            role=role,
            terms_accepted=True,  # OAuth users implicitly accept terms
        )
        self.db.add(user)
        
        # Create business profile if business user
        if role == "business":
            self.db.flush()  # Get user.id
            business_profile = BusinessProfile(
                user_id=user.id,
                business_name=f"{first_name}'s Business",  # Default business name
            )
            self.db.add(business_profile)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_or_create_oauth_user(self, email: str, name: str, role: str) -> User:
        """Get existing user or create new one from OAuth"""
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            user = self.create_oauth_user(email, name, role)
        return user
