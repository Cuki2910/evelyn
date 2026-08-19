import asyncio

from app.modules.moderation.schemas import Decision, FrameRequest, ScriptRequest
from app.modules.moderation.service import ModerationService
from app.modules.policy.company_policy import (
    CompanyPolicyCreate,
    CompanyPolicyStore,
    _default_policy_store_path,
)


def create_policy(
    store: CompanyPolicyStore, *, decision: Decision, keyword: str = "evelyn-exclusive"
) -> None:
    store.create(
        CompanyPolicyCreate(
            company_id="evelyn-news",
            title="Evelyn editorial restriction",
            keywords=[keyword],
            decision=decision,
            reason="This is restricted by the Evelyn News demo policy.",
        )
    )


def test_serverless_policy_store_uses_writable_temp_path(monkeypatch) -> None:
    monkeypatch.delenv("COMPANY_POLICY_STORE_PATH", raising=False)
    monkeypatch.setenv("VERCEL", "1")

    assert _default_policy_store_path().as_posix() == "/tmp/evelyn/company_policies.json"


def test_company_policy_store_persists_and_matches(tmp_path) -> None:
    path = tmp_path / "company_policies.json"
    store = CompanyPolicyStore(path)
    create_policy(store, decision=Decision.REVIEW)

    reloaded_store = CompanyPolicyStore(path)
    catalog = reloaded_store.catalog()
    matches = reloaded_store.find_matches("evelyn-news", "An evelyn-exclusive story")

    assert len(catalog.policies) == 1
    assert catalog.policies[0].rule_id.startswith("COMP-EVELYN-NEWS-")
    assert matches[0].keyword == "evelyn-exclusive"


def test_company_policy_changes_mock_frame_result(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("MODERATION_MODE", "mock")
    store = CompanyPolicyStore(tmp_path / "company_policies.json")
    create_policy(store, decision=Decision.REVIEW)
    service = ModerationService(policy_store=store)

    result = asyncio.run(
        service.moderate_frame(
            FrameRequest(
                company_id="evelyn-news",
                title="Evelyn-exclusive weather update",
                summary="A neutral local forecast.",
            )
        )
    )

    assert result.decision is Decision.REVIEW
    assert result.policy_results[-1].source == "company_demo_policy"
    assert result.requires_layer2 is True


def test_company_block_policy_stops_mock_layer2(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("MODERATION_MODE", "mock")
    store = CompanyPolicyStore(tmp_path / "company_policies.json")
    create_policy(store, decision=Decision.BLOCK, keyword="evelyn-embargo")
    service = ModerationService(policy_store=store)

    result = asyncio.run(
        service.moderate_script(
            ScriptRequest(company_id="evelyn-news", script="This is under evelyn-embargo.")
        )
    )

    assert result.decision is Decision.BLOCK
    assert result.revised_script is None
    assert result.requires_human_review is True
