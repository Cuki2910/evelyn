import os
from collections.abc import Callable

from app.modules.llm.gateway import LLMGateway
from app.modules.llm.schemas import LLMGatewayError
from app.modules.moderation.layer1 import Layer1Moderator
from app.modules.moderation.layer2 import Layer2Moderator
from app.modules.moderation.schemas import (
    Decision,
    FrameRequest,
    FrameResponse,
    PolicyReference,
    PolicyResult,
    RiskLevel,
    ScriptRequest,
    ScriptResponse,
)


class ModerationService:
    """Selects offline mock or real LLM moderation without changing endpoint contracts."""

    def __init__(self, gateway_factory: Callable[[], LLMGateway] = LLMGateway) -> None:
        self._gateway_factory = gateway_factory
        self._layer1 = Layer1Moderator()
        self._layer2 = Layer2Moderator()

    async def moderate_frame(self, request: FrameRequest) -> FrameResponse:
        if self._mode() == "mock":
            return self._layer1.moderate(request)
        try:
            return await self._gateway_factory().moderate_frame(request)
        except LLMGatewayError:
            return FrameResponse(
                decision=Decision.REVIEW,
                risk_level=RiskLevel.MEDIUM,
                risk_categories=["unknown"],
                violations=[],
                policy_results=[
                    PolicyResult(
                        source="llm_gateway",
                        decision=Decision.REVIEW,
                        rule_id="DEV-TT-UNKNOWN",
                        reason="LLM output was unavailable or invalid; editor review is required.",
                    )
                ],
                reason="Moderation evidence is incomplete; editor review is required.",
                requires_layer2=True,
            )

    async def moderate_script(self, request: ScriptRequest) -> ScriptResponse:
        if self._mode() == "mock":
            return self._layer2.moderate(request)
        try:
            return await self._gateway_factory().moderate_script(request)
        except LLMGatewayError:
            return ScriptResponse(
                decision=Decision.REVIEW,
                risk_level=RiskLevel.MEDIUM,
                risk_categories=["unknown"],
                violations=[],
                policy_references=[
                    PolicyReference(
                        rule_id="DEV-TT-UNKNOWN",
                        category="unknown",
                        reason="LLM output was unavailable or invalid; editor review is required.",
                    )
                ],
                reason="Moderation evidence is incomplete; editor review is required.",
                revised_script=None,
                requires_human_review=True,
            )

    @staticmethod
    def _mode() -> str:
        return os.getenv("MODERATION_MODE", "mock").strip().casefold()
