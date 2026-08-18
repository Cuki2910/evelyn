import asyncio

import pytest

from app.modules.llm.schemas import LLMGatewayError
from app.modules.moderation.schemas import (
    AnalysisStatus,
    Decision,
    FrameRequest,
    RiskLevel,
    ScriptRequest,
    ScriptResponse,
)
from app.modules.moderation.service import ModerationService


class InvalidGateway:
    async def moderate_frame(self, _: FrameRequest):
        raise LLMGatewayError("invalid")

    async def moderate_script(self, _: ScriptRequest):
        raise LLMGatewayError("invalid")


class InconsistentGateway:
    async def moderate_script(self, _: ScriptRequest) -> ScriptResponse:
        # Bypass Pydantic to prove the service enforces the contract after a gateway call.
        return ScriptResponse.model_construct(
            decision=Decision.PASS,
            risk_level=RiskLevel.LOW,
            risk_categories=["violence"],
            violations=[],
            policy_references=[],
            reason="invalid",
            revised_script=None,
            requires_human_review=False,
            analysis_status=AnalysisStatus.COMPLETE,
            provider_error=None,
        )


def test_provider_failure_is_not_presented_as_completed_content_review(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MODERATION_MODE", "llm")
    service = ModerationService(gateway_factory=InvalidGateway)

    frame_result = asyncio.run(service.moderate_frame(FrameRequest(title="Thong tin binh thuong")))
    script_result = asyncio.run(
        service.moderate_script(ScriptRequest(script="Thong tin thoi tiet binh thuong."))
    )

    for result in (frame_result, script_result):
        assert result.decision is Decision.REVIEW
        assert result.analysis_status is AnalysisStatus.PROVIDER_ERROR
        assert result.provider_error is not None


def test_inconsistent_llm_result_falls_back_without_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODERATION_MODE", "llm")
    service = ModerationService(gateway_factory=InconsistentGateway)

    result = asyncio.run(service.moderate_script(ScriptRequest(script="Thong tin thoi tiet binh thuong.")))

    assert result.decision is Decision.REVIEW
    assert result.analysis_status is AnalysisStatus.PROVIDER_ERROR


class GeminiHTTPErrorGateway:
    """Simulates a Gemini 429/5xx surfacing through the gateway as LLMGatewayError."""

    async def moderate_frame(self, _: FrameRequest):
        raise LLMGatewayError("gemini provider failure")

    async def moderate_script(self, _: ScriptRequest):
        raise LLMGatewayError("gemini provider failure")


def test_gemini_provider_failure_falls_back_to_review(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODERATION_MODE", "llm")
    service = ModerationService(gateway_factory=GeminiHTTPErrorGateway)

    result = asyncio.run(service.moderate_script(ScriptRequest(script="Thong tin thoi tiet binh thuong.")))

    assert result.decision is Decision.REVIEW
    assert result.analysis_status is AnalysisStatus.PROVIDER_ERROR
    assert result.provider_error is not None


def test_unsupported_moderation_mode_does_not_call_the_llm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gateway_called = False

    def gateway_factory() -> InvalidGateway:
        nonlocal gateway_called
        gateway_called = True
        return InvalidGateway()

    monkeypatch.setenv("MODERATION_MODE", "lm")
    service = ModerationService(gateway_factory=gateway_factory)

    with pytest.raises(LLMGatewayError, match="MODERATION_MODE"):
        asyncio.run(service.moderate_frame(FrameRequest(title="Thong tin binh thuong")))

    assert gateway_called is False
