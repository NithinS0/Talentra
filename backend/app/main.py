"""Talentra Backend Application Entrypoint."""

from fastapi import FastAPI, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db, check_database_connection

app = FastAPI(
    title=settings.APP_NAME,
    description="Scalable Job Search & Demand Management Platform API (Supabase PostgreSQL)",
    version="0.1.0",
    debug=settings.APP_DEBUG,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

# CORS Middleware configuration (allowing configurable frontend origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API v1 routes
from app.api.v1.router import api_router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)



@app.get("/", tags=["Root"])
def root():
    """Service status summary."""
    return {
        "service": settings.APP_NAME,
        "status": "online",
        "environment": settings.APP_ENV,
        "version": "0.1.0",
    }


@app.get("/health", tags=["Health"])
@app.get(f"{settings.API_V1_PREFIX}/health", tags=["Health"])
def health_check():
    """Liveness probe - does not require active database session."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
    }


@app.get(f"{settings.API_V1_PREFIX}/health/db", tags=["Health"])
def database_health_check():
    """Readiness probe - actively verifies Supabase database connectivity."""
    is_connected, message = check_database_connection()
    if is_connected:
        return {
            "status": "healthy",
            "database": "connected",
            "detail": message,
        }
    return {
        "status": "unhealthy",
        "database": "disconnected",
        "detail": message,
    }
