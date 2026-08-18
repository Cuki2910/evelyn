from fastapi import APIRouter

from app.api.v1.endpoints.company_policies import router as company_policy_router
from app.api.v1.endpoints.moderation import router as moderation_router

router = APIRouter()
router.include_router(company_policy_router)
router.include_router(moderation_router)
