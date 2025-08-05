from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from app.jobs import routes as job_routes

app = FastAPI(title="Job Portal API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "ok"}

# Include job posting routes
app.include_router(job_routes.router)

# Root endpoint
@app.get("/")
def root():
    return {"message": "Welcome to Job Portal API"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
