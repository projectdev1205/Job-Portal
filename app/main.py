from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.database import engine, Base
from contextlib import asynccontextmanager
from app.config import settings
import secrets

# Import routers
from app.business.business_routes import router as business_router  # Business job routes
from app.applicant.applicant_routes import router as applicant_router
from app.auth import auth_routes
from app.dashboard import router as dashboard_router
from app.admin import admin_routes
from app.admin import dev_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    print("📦 Creating tables if they do not exist...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables are ready!")

    yield  # Application is running

    # Shutdown: nothing to clean up now
    print("🛑 Application shutting down...")
app = FastAPI(
    title="Job Portal API", 
    version="1.0.0", 
    lifespan=lifespan,
    debug=settings.debug
)

# Session middleware for OAuth (must be added before other middleware)
app.add_middleware(
    SessionMiddleware, 
    secret_key=settings.jwt_secret or secrets.token_urlsafe(32)
)

# CORS middleware with proper security
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "path": str(request.url)
        }
    )

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "ok"}

# Include routers
app.include_router(auth_routes.router)
app.include_router(business_router)  # Business job routes
app.include_router(applicant_router)  # Applicant job routes
app.include_router(dashboard_router)  # Dashboard routes
app.include_router(admin_routes.router)  # Admin routes
app.include_router(dev_routes.router)  # Development routes (only in dev environment)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
