import json
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel

from app.modules.llm.prompts.layer1 import LAYER1_SYSTEM_PROMPT
from app.modules.llm.prompts.layer2 import LAYER2_SYSTEM_PROMPT
from app.modules.llm.prompts.policy import POLICY_EVALUATION_SYSTEM_PROMPT
from app.modules.llm.schemas import LLMGatewayError, LLMSettings
from app.modules.moderation.decision_engine import DecisionEngine
from app.modules.moderation.schemas import (
    AnalysisStatus,
    FrameRequest,
    FrameResponse,
    ScriptRequest,
    ScriptResponse,
)
from app.modules.policy.development_policy import ALLOWED_DEVELOPMENT_POLICY_IDS
from app.modules.policy.company_policy import PolicyRule
from app.modules.policy.evaluator import PolicyEvaluationResponse, validate_rule_coverage

ResponseModel = TypeVar("ResponseModel", bound=BaseModel)
Sender = Callable[[dict[str, object]], Awaitable[dict[str, object]]]


def strict_json_schema(
    response_model: type[BaseModel], excluded_fields: set[str] | None = None
) -> dict[str, Any]:
    """Make Pydantic's JSON Schema acceptable for strict structured outputs."""

    schema = response_model.model_json_schema()
    excluded_fields = excluded_fields or set()

    def enforce(node: object) -> None:
        if isinstance(node, dict):
            properties = node.get("properties")
            if isinstance(properties, dict):
                for field in excluded_fields:
                    properties.pop(field, None)
                node["additionalProperties"] = False
                node["required"] = list(properties)
            for value in node.values():
                enforce(value)
        elif isinstance(node, list):
            for value in node:
                enforce(value)

    enforce(schema)
    return schema


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
            response_validator=self._validate_frame_contract,
            schema_excluded_fields={"custom_policy_results"},
        )

    async def moderate_script(self, request: ScriptRequest) -> ScriptResponse:
        title = f"Title:\n{request.title}\n\n" if request.title else ""
        return await self._moderate(
            system_prompt=LAYER2_SYSTEM_PROMPT,
            user_prompt=f"{title}Script:\n{request.script}",
            response_model=ScriptResponse,
            schema_excluded_fields={"custom_policy_results"},
        )

    async def evaluate_custom_policies(
        self, *, stage: str, content: str, rules: list[PolicyRule]
    ) -> PolicyEvaluationResponse:
        rules_input = "\n\n".join(
            f"<RULE>\nrule_id: {rule.rule_id}\nname: {rule.name}\nrule_text:\n{rule.rule_text}\n</RULE>"
            for rule in rules
        )
        result = await self._moderate(
            system_prompt=POLICY_EVALUATION_SYSTEM_PROMPT,
            user_prompt=(
                f"MODERATION STAGE:\n{stage}\n\nPOLICY RULES:\n{rules_input}\n\n"
                f"CONTENT TO EVALUATE:\n<CONTENT>\n{content}\n</CONTENT>"
            ),
            response_model=PolicyEvaluationResponse,
            require_complete=False,
        )
        return validate_rule_coverage(result, rules)

    async def _moderate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[ResponseModel],
        response_validator: Callable[[ResponseModel], None] | None = None,
        require_complete: bool = True,
        schema_excluded_fields: set[str] | None = None,
    ) -> ResponseModel:
        payload: dict[str, object] = {
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
                    "schema": strict_json_schema(response_model, schema_excluded_fields),
                },
            },
        }
        if self._settings.provider == "openrouter":
            payload["provider"] = {
                "zdr": True,
                "data_collection": "deny",
                "require_parameters": True,
            }

        for attempt in range(2):
            try:
                raw_response = await self._send(payload)
                content = raw_response["choices"][0]["message"]["content"]
                parsed = json.loads(content) if isinstance(content, str) else content
                result = response_model.model_validate(parsed)
                if require_complete and result.analysis_status is not AnalysisStatus.COMPLETE:
                    raise ValueError("LLM results must be complete moderation analyses")
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
    def _validate_frame_contract(result: FrameResponse) -> None:
        if any(
            policy_result.rule_id not in ALLOWED_DEVELOPMENT_POLICY_IDS
            for policy_result in result.policy_results
        ):
            raise ValueError("The LLM selected a policy ID outside the development policy.")
        expected_decision = DecisionEngine.decide(result.policy_results)
        if result.decision is not expected_decision:
            raise ValueError("The LLM decision conflicts with its policy results.")
