from fastapi import APIRouter

from app.api.v1.endpoints.moderation import router as moderation_router

router = APIRouter()
router.include_router(moderation_router)
