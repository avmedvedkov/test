from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from database import Base, engine
from config import settings
from auth_routes import router as auth_router
from file_routes import router as file_router
from user_routes import router as user_router
from logging_service import log_action
from database import get_db

app = FastAPI(title="Web Application API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(file_router)
app.include_router(user_router)

# Mount uploads directory for serving files
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.on_event("startup")
async def startup_event():
    """Create database tables on startup."""
    from sqlalchemy import text
    try:
        # Try to create tables
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Warning: Could not create database tables on startup: {e}")
        print("Database tables will be created when database is available")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    response = await call_next(request)
    
    # Log request (async safe way)
    try:
        db = next(get_db())
        from logging_service import log_action
        
        log_action(
            db=db,
            action="REQUEST",
            entity_type="http",
            details=f"{request.method} {request.url.path}",
            ip_address=request.client.host if request.client else None
        )
    except Exception:
        pass  # Don't fail on logging errors
    
    return response


@app.get("/")
async def root():
    return {"message": "Welcome to the Web Application API", "docs": "/docs"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
