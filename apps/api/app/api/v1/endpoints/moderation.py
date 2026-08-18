import logging

from fastapi import APIRouter, HTTPException, status

from app.modules.moderation.schemas import FrameRequest, FrameResponse, ScriptRequest, ScriptResponse
from app.modules.moderation.service import ModerationService

router = APIRouter(prefix="/moderate", tags=["moderation"])
logger = logging.getLogger(__name__)
moderation_service = ModerationService()


@router.post("/frame", response_model=FrameResponse)
async def moderate_frame(request: FrameRequest) -> FrameResponse:
    try:
        return await moderation_service.moderate_frame(request)
    except Exception:
        logger.exception("Layer 1 moderation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Moderation request could not be processed.",
        ) from None


@router.post("/script", response_model=ScriptResponse)
async def moderate_script(request: ScriptRequest) -> ScriptResponse:
    try:
        return await moderation_service.moderate_script(request)
    except Exception:
        logger.exception("Layer 2 moderation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Moderation request could not be processed.",
        ) from None
