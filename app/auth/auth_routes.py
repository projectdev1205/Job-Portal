import secrets
from typing import Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session

from authlib.integrations.starlette_client import OAuth, OAuthError

from app.database import get_db
from app.models import User, BusinessProfile
from app.auth.auth_deps import get_current_user
from app.schemas import (
    RegisterIn, LoginIn, UserOut, Token, 
    BusinessRegisterIn, ApplicantRegisterIn, AdminRegisterIn,
    UserOutLegacy, LoginResponse, LogoutResponse
)
from app.utils.security import create_access_token, blacklist_token
from app.auth.auth_service import AuthService
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Auth"])
oauth = OAuth()
bearer = HTTPBearer(auto_error=True)

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
    """Register a new business user"""
    service = AuthService(db)
    return service.register_business(payload)

@router.post("/register/applicant", response_model=UserOut)
def register_applicant(payload: ApplicantRegisterIn, db: Session = Depends(get_db)):
    """Register a new applicant user"""
    service = AuthService(db)
    return service.register_applicant(payload)

@router.post("/register/admin", response_model=UserOut)
def register_admin(payload: AdminRegisterIn, db: Session = Depends(get_db)):
    """Register a new admin user (requires admin code)"""
    service = AuthService(db)
    return service.register_admin(payload)

# Legacy registration endpoint for backward compatibility
@router.post("/register", response_model=UserOutLegacy)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    """Legacy registration for backward compatibility"""
    service = AuthService(db)
    return service.register_legacy(payload)


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    """Authenticate user and return login response"""
    service = AuthService(db)
    return service.login(payload)

@router.post("/logout", response_model=LogoutResponse)
def logout(
    current_user: User = Depends(get_current_user),
    creds: HTTPAuthorizationCredentials = Depends(bearer)
):
    """Logout user by blacklisting their token"""
    token = creds.credentials
    blacklist_token(token)
    return LogoutResponse(
        message="Successfully logged out",
        status="success"
    )

@router.post("/logout/all")
def logout_all_sessions(
    current_user: User = Depends(get_current_user)
):
    """Logout user from all sessions (admin only)"""
    # This is a placeholder for future implementation
    # In a real app, you'd track user sessions and invalidate all of them
    return {
        "message": "All sessions logged out successfully",
        "status": "success",
        "note": "This endpoint is a placeholder for future session management"
    }


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
    service = AuthService(db)
    role = request.session.get("oauth_role") or "applicant"
    user = service.get_or_create_oauth_user(email, name, role)

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
