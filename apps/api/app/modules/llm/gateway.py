import json
from collections.abc import Awaitable, Callable
from typing import TypeVar

import httpx
from pydantic import BaseModel

from app.modules.llm.prompts.layer1 import LAYER1_SYSTEM_PROMPT
from app.modules.llm.prompts.layer2 import LAYER2_SYSTEM_PROMPT
from app.modules.llm.schemas import LLMGatewayError, LLMSettings
from app.modules.moderation.schemas import FrameRequest, FrameResponse, ScriptRequest, ScriptResponse
from app.modules.policy.development_policy import ALLOWED_DEVELOPMENT_POLICY_IDS

ResponseModel = TypeVar("ResponseModel", bound=BaseModel)
Sender = Callable[[dict[str, object]], Awaitable[dict[str, object]]]


class LLMGateway:
    """One thin OpenAI-compatible gateway for structured moderation calls."""

    def __init__(self, settings: LLMSettings | None = None, sender: Sender | None = None) -> None:
        self._settings = settings or LLMSettings.from_environment()
        self._sender = sender

    async def moderate_frame(self, request: FrameRequest) -> FrameResponse:
        return await self._moderate(
            system_prompt=LAYER1_SYSTEM_PROMPT,
            user_prompt=f"Title:\n{request.title}\n\nSummary:\n{request.summary}",
            response_model=FrameResponse,
            response_validator=self._validate_frame_policy_ids,
        )

    async def moderate_script(self, request: ScriptRequest) -> ScriptResponse:
        title = f"Title:\n{request.title}\n\n" if request.title else ""
        return await self._moderate(
            system_prompt=LAYER2_SYSTEM_PROMPT,
            user_prompt=f"{title}Script:\n{request.script}",
            response_model=ScriptResponse,
        )

    async def _moderate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[ResponseModel],
        response_validator: Callable[[ResponseModel], None] | None = None,
    ) -> ResponseModel:
        payload = {
            "model": self._settings.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": response_model.__name__.lower(),
                    "strict": True,
                    "schema": response_model.model_json_schema(),
                },
            },
        }

        for attempt in range(2):
            try:
                raw_response = await self._send(payload)
                content = raw_response["choices"][0]["message"]["content"]
                parsed = json.loads(content) if isinstance(content, str) else content
                result = response_model.model_validate(parsed)
                if response_validator:
                    response_validator(result)
                return result
            except (
                KeyError,
                TypeError,
                ValueError,
                json.JSONDecodeError,
                httpx.HTTPError,
            ) as error:
                if attempt == 1:
                    raise LLMGatewayError("The LLM returned invalid structured moderation output.") from error

        raise LLMGatewayError("The LLM could not produce a moderation result.")

    async def _send(self, payload: dict[str, object]) -> dict[str, object]:
        if self._sender is not None:
            return await self._sender(payload)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self._settings.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self._settings.api_key}"},
                json=payload,
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    def _validate_frame_policy_ids(result: FrameResponse) -> None:
        if any(
            policy_result.rule_id not in ALLOWED_DEVELOPMENT_POLICY_IDS
            for policy_result in result.policy_results
        ):
            raise ValueError("The LLM selected a policy ID outside the development policy.")
