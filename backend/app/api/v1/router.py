"""API v1 Central Router."""

from fastapi import APIRouter
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.candidates import router as candidates_router
from app.api.v1.endpoints.jobs import router as jobs_router
from app.api.v1.endpoints.applications import router as applications_router
from app.api.v1.endpoints.organisations import router as organisations_router
from app.api.v1.endpoints.admin import router as admin_router
from app.api.v1.endpoints.sourcing import router as sourcing_router
from app.api.v1.endpoints.gig import router as gig_router
from app.api.v1.endpoints.licences import router as licences_router
from app.api.v1.endpoints.subscriptions import router as subscriptions_router
from app.api.v1.endpoints.notifications import router as notifications_router
from app.api.v1.endpoints.analytics import router as analytics_router
from app.api.v1.endpoints.verification import router as verification_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(candidates_router)
api_router.include_router(jobs_router)
api_router.include_router(applications_router)
api_router.include_router(organisations_router)
api_router.include_router(admin_router)
api_router.include_router(sourcing_router)
api_router.include_router(gig_router)
api_router.include_router(licences_router)
api_router.include_router(subscriptions_router)
api_router.include_router(notifications_router)
api_router.include_router(analytics_router, prefix="/analytics", tags=["Analytics & Reporting"])
api_router.include_router(verification_router, prefix="/verification", tags=["Verification, Integrations & Retention"])



