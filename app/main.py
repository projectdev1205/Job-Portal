from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.database import engine, Base
from contextlib import asynccontextmanager
from app.config import settings
from app.utils.logger import setup_logging, get_logger
from app.middleware.logging_middleware import LoggingMiddleware
import secrets

# Import routers
from app.business.business_routes import router as business_router  # Business job routes
from app.applicant.applicant_routes import router as applicant_router
from app.auth import auth_routes
from app.dashboard import router as dashboard_router
from app.admin import admin_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup logging first
    setup_logging()
    logger = get_logger("main")
    
    # Startup: create tables
    logger.info("📦 Creating tables if they do not exist...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Tables are ready!")

    yield  # Application is running

    # Shutdown: nothing to clean up now
    logger.info("🛑 Application shutting down...")
app = FastAPI(
    title="Job Portal API", 
    version="1.0.0", 
    lifespan=lifespan,
    debug=settings.debug
)

# Add logging middleware first
app.add_middleware(LoggingMiddleware)

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
    logger = get_logger("exception_handler")
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.warning(
        f"HTTP Exception: {exc.status_code} - {exc.detail}",
        extra={
            "request_id": request_id,
            "status_code": exc.status_code,
            "path": str(request.url),
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url),
            "request_id": request_id
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger = get_logger("exception_handler")
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "request_id": request_id,
            "path": str(request.url),
            "method": request.method,
            "exception_type": type(exc).__name__
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "path": str(request.url),
            "request_id": request_id
        }
    )

# Health check endpoint
@app.get("/health")
def health_check():
    logger = get_logger("health_check")
    logger.debug("Health check requested")
    return {"status": "ok"}

# Include routers
app.include_router(auth_routes.router)
app.include_router(business_router)  # Business job routes
app.include_router(applicant_router)  # Applicant job routes
app.include_router(dashboard_router)  # Dashboard routes
app.include_router(admin_routes.router)  # Admin routes

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
