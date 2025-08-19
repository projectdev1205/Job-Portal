import secrets
from typing import Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session

from authlib.integrations.starlette_client import OAuth, OAuthError

from app.database import get_db
from app.models import User, BusinessProfile
from app.schemas import (
    RegisterIn, LoginIn, UserOut, Token, 
    BusinessRegisterIn, ApplicantRegisterIn,
    UserOutLegacy
)
from app.utils.security import (
    hash_password, verify_password, create_access_token
)
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Auth"])
oauth = OAuth()

if settings.google_client_id and settings.google_client_secret:
    oauth.register(
        name="google",
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        client_kwargs={"scope": "openid email profile"},
    )


@router.post("/register/business", response_model=UserOut)
def register_business(payload: BusinessRegisterIn, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user
    user = User(
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        phone_number=payload.phone_number,
        password_hash=hash_password(payload.password),
        role="business",
        email_notifications=payload.email_notifications,
        terms_accepted=payload.terms_accepted,
    )
    db.add(user)
    db.flush()  # Get user.id without committing
    
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
    db.add(business_profile)
    
    db.commit()
    db.refresh(user)
    return user

@router.post("/register/applicant", response_model=UserOut)
def register_applicant(payload: ApplicantRegisterIn, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
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
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# Legacy registration endpoint for backward compatibility
@router.post("/register", response_model=UserOutLegacy)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
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
    db.add(user)
    
    # Create business profile if business user
    if payload.role == "business":
        db.flush()  # Get user.id
        business_profile = BusinessProfile(
            user_id=user.id,
            business_name=f"{first_name}'s Business",  # Default business name
        )
        db.add(business_profile)
    
    db.commit()
    db.refresh(user)
    
    # Return legacy format
    return UserOutLegacy(
        id=user.id,
        name=f"{user.first_name} {user.last_name}".strip(),
        email=user.email,
        role=user.role
    )


@router.post("/login", response_model=Token)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(sub=user.email, extra={"role": user.role, "uid": user.id})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/google/login")
async def google_login(request: Request, role: Optional[Literal["business", "applicant"]] = "applicant"):
    if not (settings.google_client_id and settings.google_client_secret):
        raise HTTPException(status_code=501, detail="Google OAuth not configured")
    
    # Store intended role in session for first-time users
    request.session["oauth_role"] = role or "applicant"
    redirect_uri = settings.google_redirect_uri or request.url_for("google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback", name="google_callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    if not (settings.google_client_id and settings.google_client_secret):
        raise HTTPException(status_code=501, detail="Google OAuth not configured")
        
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as e:
        raise HTTPException(status_code=400, detail=f"OAuth error: {e.error}")

    userinfo = token.get("userinfo")
    if not userinfo:
        resp = await oauth.google.get("userinfo", token=token)
        userinfo = resp.json()

    email = userinfo.get("email")
    name = userinfo.get("name") or (email.split("@")[0] if email else None)
    if not email:
        raise HTTPException(status_code=400, detail="Google did not return an email")

    # Upsert user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        fallback_hash = hash_password(secrets.token_urlsafe(24))
        role = request.session.get("oauth_role") or "applicant"
        
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
        db.add(user)
        
        # Create business profile if business user
        if role == "business":
            db.flush()  # Get user.id
            business_profile = BusinessProfile(
                user_id=user.id,
                business_name=f"{first_name}'s Business",  # Default business name
            )
            db.add(business_profile)
        
        db.commit()
        db.refresh(user)

    jwt_token = create_access_token(sub=user.email, extra={"role": user.role, "uid": user.id})

    if settings.frontend_url:
        # Send JWT to your SPA via URL fragment
        fragment = f"token={jwt_token}&role={user.role}&email={user.email}"
        return RedirectResponse(url=f"{settings.frontend_url}#{fragment}")

    return {
        "access_token": jwt_token,
        "token_type": "bearer",
        "user": {"id": user.id, "name": f"{user.first_name} {user.last_name}".strip(), "email": user.email, "role": user.role},
    }
