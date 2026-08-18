import os
from collections.abc import Callable

from app.modules.llm.gateway import LLMGateway
from app.modules.llm.schemas import LLMGatewayError
from app.modules.moderation.layer1 import Layer1Moderator
from app.modules.moderation.layer2 import Layer2Moderator
from app.modules.moderation.schemas import (
    AnalysisStatus,
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
            result = await self._gateway_factory().moderate_frame(request)
            return self._validate_complete_frame(result)
        except (LLMGatewayError, ValueError):
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
                analysis_status=AnalysisStatus.PROVIDER_ERROR,
                provider_error="The moderation provider was unavailable or returned invalid output.",
            )

    async def moderate_script(self, request: ScriptRequest) -> ScriptResponse:
        if self._mode() == "mock":
            return self._layer2.moderate(request)
        try:
            result = await self._gateway_factory().moderate_script(request)
            return self._validate_complete_script(result)
        except (LLMGatewayError, ValueError):
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
                analysis_status=AnalysisStatus.PROVIDER_ERROR,
                provider_error="The moderation provider was unavailable or returned invalid output.",
            )

    @staticmethod
    def _mode() -> str:
        return os.getenv("MODERATION_MODE", "mock").strip().casefold()

    @staticmethod
    def _validate_complete_frame(result: FrameResponse) -> FrameResponse:
        validated = FrameResponse.model_validate(result.model_dump())
        if validated.analysis_status is not AnalysisStatus.COMPLETE:
            raise LLMGatewayError("LLM result did not complete moderation.")
        return validated

    @staticmethod
    def _validate_complete_script(result: ScriptResponse) -> ScriptResponse:
        validated = ScriptResponse.model_validate(result.model_dump())
        if validated.analysis_status is not AnalysisStatus.COMPLETE:
            raise LLMGatewayError("LLM result did not complete moderation.")
        return validated
