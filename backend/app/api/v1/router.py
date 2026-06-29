from fastapi import APIRouter

from app.api.v1.endpoints import admin, applications, auth, documents, leads, notifications, pricing, users

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(applications.router, prefix="/applications", tags=["applications"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(leads.router, prefix="/leads", tags=["leads"])
api_router.include_router(pricing.router, prefix="/pricing", tags=["pricing"])
