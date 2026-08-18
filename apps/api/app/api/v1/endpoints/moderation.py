import logging

from fastapi import APIRouter, HTTPException, status

from app.modules.moderation.layer1 import Layer1Moderator
from app.modules.moderation.schemas import FrameRequest, FrameResponse

router = APIRouter(prefix="/moderate", tags=["moderation"])
logger = logging.getLogger(__name__)
moderator = Layer1Moderator()


@router.post("/frame", response_model=FrameResponse)
async def moderate_frame(request: FrameRequest) -> FrameResponse:
    try:
        return moderator.moderate(request)
    except Exception:
        logger.exception("Layer 1 moderation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Moderation request could not be processed.",
        ) from None
