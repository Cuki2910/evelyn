import asyncio
import json

import pytest

from app.modules.llm.gateway import LLMGateway
from app.modules.llm.schemas import LLMGatewayError, LLMSettings
from app.modules.moderation.schemas import ScriptRequest


async def invalid_sender(_: dict[str, object]) -> dict[str, object]:
    return {"choices": [{"message": {"content": json.dumps({"decision": "PASS"})}}]}


def test_gateway_retries_then_rejects_invalid_structured_output() -> None:
    gateway = LLMGateway(
        settings=LLMSettings(
            provider="openai_compatible",
            api_key="test",
            model="test-model",
            base_url="https://example.test",
        ),
        sender=invalid_sender,
    )

    with pytest.raises(LLMGatewayError):
        asyncio.run(
            gateway.moderate_script(ScriptRequest(script="Thong tin thoi tiet binh thuong."))
        )
