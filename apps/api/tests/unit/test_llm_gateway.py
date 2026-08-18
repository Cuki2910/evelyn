import asyncio
import json
from typing import Any

import httpx
import pytest

from app.modules.llm.gateway import LLMGateway, strict_json_schema
from app.modules.llm.schemas import LLMGatewayError, LLMSettings
from app.modules.moderation.schemas import (
    Decision,
    FrameRequest,
    FrameResponse,
    ScriptRequest,
    ScriptResponse,
)


def settings() -> LLMSettings:
    return LLMSettings(
        provider="openrouter",
        api_key="test",
        model="openai/gpt-5.4-mini",
        base_url="https://openrouter.ai/api/v1",
    )


def test_openrouter_is_the_default_llm_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "test")
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)

    configured = LLMSettings.from_environment()

    assert configured.provider == "openrouter"
    assert configured.model == "openai/gpt-5.4-mini"
    assert configured.base_url == "https://openrouter.ai/api/v1"


def test_groq_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("LLM_API_KEY", "test")
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)

    configured = LLMSettings.from_environment()

    assert configured.model == "openai/gpt-oss-120b"
    assert configured.base_url == "https://api.groq.com/openai/v1"


def test_gemini_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("LLM_API_KEY", "test")
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)

    configured = LLMSettings.from_environment()

    assert configured.model == "gemini-3.6-flash"
    assert configured.base_url == "https://generativelanguage.googleapis.com/v1beta/openai"


def test_unsupported_provider_is_rejected_before_any_request(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "foo")
    monkeypatch.setenv("LLM_API_KEY", "test")

    with pytest.raises(LLMGatewayError, match="Unsupported LLM_PROVIDER"):
        LLMSettings.from_environment()


def complete_script_payload() -> dict[str, object]:
    return {
        "decision": "PASS",
        "risk_level": "LOW",
        "risk_categories": [],
        "violations": [],
        "policy_references": [],
        "reason": "No development-policy issue was found.",
        "revised_script": None,
        "requires_human_review": True,
        "analysis_status": "COMPLETE",
        "provider_error": None,
    }


def assert_strict_objects(schema: object) -> None:
    if isinstance(schema, dict):
        properties = schema.get("properties")
        if isinstance(properties, dict):
            assert schema["additionalProperties"] is False
            assert set(schema["required"]) == set(properties)
        for value in schema.values():
            assert_strict_objects(value)
    elif isinstance(schema, list):
        for value in schema:
            assert_strict_objects(value)


def test_openrouter_request_includes_privacy_settings_and_strict_schema() -> None:
    captured_payloads: list[dict[str, object]] = []

    async def sender(payload: dict[str, object]) -> dict[str, object]:
        captured_payloads.append(payload)
        return {"choices": [{"message": {"content": json.dumps(complete_script_payload())}}]}

    gateway = LLMGateway(settings=settings(), sender=sender)
    result = asyncio.run(gateway.moderate_script(ScriptRequest(script="Thong tin binh thuong.")))

    assert result.decision.value == "PASS"
    payload = captured_payloads[0]
    assert payload["provider"] == {
        "zdr": True,
        "data_collection": "deny",
        "require_parameters": True,
    }
    schema = payload["response_format"]["json_schema"]["schema"]
    assert_strict_objects(schema)
    assert "revised_script" in schema["required"]
    assert "provider_error" in schema["required"]


def test_gemini_request_has_no_openrouter_provider_field() -> None:
    captured_payloads: list[dict[str, object]] = []

    async def sender(payload: dict[str, object]) -> dict[str, object]:
        captured_payloads.append(payload)
        return {"choices": [{"message": {"content": json.dumps(complete_script_payload())}}]}

    gemini_settings = LLMSettings(
        provider="gemini",
        api_key="test",
        model="gemini-3.6-flash",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai",
    )
    gateway = LLMGateway(settings=gemini_settings, sender=sender)
    asyncio.run(gateway.moderate_script(ScriptRequest(script="Thong tin binh thuong.")))

    payload = captured_payloads[0]
    assert payload["model"] == "gemini-3.6-flash"
    assert "messages" in payload
    assert "provider" not in payload
    json_schema = payload["response_format"]["json_schema"]
    assert json_schema["strict"] is True
    assert "schema" in json_schema


def test_groq_request_has_no_openrouter_provider_field() -> None:
    captured_payloads: list[dict[str, object]] = []

    async def sender(payload: dict[str, object]) -> dict[str, object]:
        captured_payloads.append(payload)
        return {"choices": [{"message": {"content": json.dumps(complete_script_payload())}}]}

    groq_settings = LLMSettings(
        provider="groq",
        api_key="test",
        model="openai/gpt-oss-120b",
        base_url="https://api.groq.com/openai/v1",
    )
    gateway = LLMGateway(settings=groq_settings, sender=sender)
    asyncio.run(gateway.moderate_script(ScriptRequest(script="Thong tin binh thuong.")))

    payload = captured_payloads[0]
    assert payload["model"] == "openai/gpt-oss-120b"
    assert "provider" not in payload


def test_gemini_http_error_never_becomes_a_successful_result() -> None:
    async def failing_sender(_: dict[str, object]) -> dict[str, object]:
        request = httpx.Request("POST", "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions")
        response = httpx.Response(429, request=request)
        raise httpx.HTTPStatusError("rate limited", request=request, response=response)

    gemini_settings = LLMSettings(
        provider="gemini",
        api_key="test",
        model="gemini-3.6-flash",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai",
    )
    gateway = LLMGateway(settings=gemini_settings, sender=failing_sender)

    with pytest.raises(LLMGatewayError):
        asyncio.run(gateway.moderate_script(ScriptRequest(script="Thong tin binh thuong.")))


@pytest.mark.parametrize("response_model", [FrameResponse, ScriptResponse])
def test_strict_schema_requires_every_response_property(response_model: type[object]) -> None:
    assert_strict_objects(strict_json_schema(response_model))


def test_gateway_retries_then_rejects_invalid_structured_output() -> None:
    attempts = 0

    async def invalid_sender(_: dict[str, object]) -> dict[str, object]:
        nonlocal attempts
        attempts += 1
        return {"choices": [{"message": {"content": json.dumps({"decision": "PASS"})}}]}

    gateway = LLMGateway(settings=settings(), sender=invalid_sender)

    with pytest.raises(LLMGatewayError):
        asyncio.run(gateway.moderate_script(ScriptRequest(script="Thong tin thoi tiet binh thuong.")))

    assert attempts == 2


def test_gemini_retries_then_rejects_malformed_structured_output() -> None:
    attempts = 0

    async def invalid_sender(_: dict[str, object]) -> dict[str, object]:
        nonlocal attempts
        attempts += 1
        return {"choices": [{"message": {"content": "not valid json"}}]}

    gemini_settings = LLMSettings(
        provider="gemini",
        api_key="test",
        model="gemini-3.6-flash",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai",
    )
    gateway = LLMGateway(settings=gemini_settings, sender=invalid_sender)

    with pytest.raises(LLMGatewayError):
        asyncio.run(gateway.moderate_script(ScriptRequest(script="Thong tin thoi tiet binh thuong.")))

    assert attempts == 2


def complete_frame_payload(
    policy_decisions: list[str], decision: str
) -> dict[str, object]:
    return {
        "decision": decision,
        "risk_level": "LOW",
        "risk_categories": [],
        "violations": [],
        "policy_results": [
            {
                "source": "llm_gateway",
                "decision": policy_decision,
                "rule_id": "DEV-TT-UNKNOWN",
                "reason": "Synthetic policy result.",
            }
            for policy_decision in policy_decisions
        ],
        "reason": "Synthetic moderation result.",
        "requires_layer2": decision != "BLOCK",
        "analysis_status": "COMPLETE",
        "provider_error": None,
    }


@pytest.mark.parametrize(
    ("policy_decisions", "decision"),
    [
        (["BLOCK"], "PASS"),
        (["REVIEW"], "PASS"),
        ([], "PASS"),
    ],
)
def test_gateway_rejects_layer1_decision_that_conflicts_with_policy_results(
    policy_decisions: list[str], decision: str
) -> None:
    attempts = 0
    inconsistent_response = complete_frame_payload(policy_decisions, decision)

    async def sender(_: dict[str, object]) -> dict[str, object]:
        nonlocal attempts
        attempts += 1
        return {"choices": [{"message": {"content": json.dumps(inconsistent_response)}}]}

    gateway = LLMGateway(settings=settings(), sender=sender)

    with pytest.raises(LLMGatewayError):
        asyncio.run(gateway.moderate_frame(FrameRequest(title="Thong tin binh thuong")))

    assert attempts == 2


@pytest.mark.parametrize(
    ("policy_decisions", "decision"),
    [
        (["PASS", "PASS"], "PASS"),
        (["PASS", "REVIEW"], "REVIEW"),
        (["PASS", "BLOCK"], "BLOCK"),
    ],
)
def test_gateway_accepts_layer1_decision_derived_from_policy_results(
    policy_decisions: list[str], decision: str
) -> None:
    async def sender(_: dict[str, object]) -> dict[str, object]:
        return {
            "choices": [
                {"message": {"content": json.dumps(complete_frame_payload(policy_decisions, decision))}}
            ]
        }

    result = asyncio.run(
        LLMGateway(settings=settings(), sender=sender).moderate_frame(
            FrameRequest(title="Thong tin binh thuong")
        )
    )

    assert result.decision is Decision(decision)
