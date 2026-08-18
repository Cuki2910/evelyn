import asyncio

import pytest

from app.modules.llm.schemas import LLMGatewayError
from app.modules.moderation.schemas import Decision, ScriptRequest
from app.modules.moderation.service import ModerationService


class InvalidGateway:
    async def moderate_script(self, _: ScriptRequest):
        raise LLMGatewayError("invalid")


def test_invalid_llm_output_is_never_a_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODERATION_MODE", "llm")
    service = ModerationService(gateway_factory=InvalidGateway)

    result = asyncio.run(
        service.moderate_script(ScriptRequest(script="Thong tin thoi tiet binh thuong."))
    )

    assert result.decision is Decision.REVIEW
    assert result.policy_references[0].rule_id == "DEV-TT-UNKNOWN"
