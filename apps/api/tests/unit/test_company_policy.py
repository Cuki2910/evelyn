import pytest

from app.modules.moderation.schemas import Decision
from app.modules.policy.company_policy import CompanyPolicyStore, PolicyRuleCreate, PolicyRuleUpdate, _default_policy_store_path


def create_policy(store: CompanyPolicyStore):
    return store.create(PolicyRuleCreate(name="International news", rule_text="Do not publish international news without a direct Vietnam impact.", violation_action=Decision.BLOCK))


def test_policy_store_crud_and_stable_server_rule_id(tmp_path) -> None:
    store = CompanyPolicyStore(tmp_path / "policies.json")
    created = create_policy(store)
    updated = store.update(created.rule_id, PolicyRuleUpdate(name="Updated", enabled=False, violation_action=Decision.REVIEW))

    assert created.rule_id.startswith("COMPANY-")
    assert updated is not None
    assert updated.rule_id == created.rule_id
    assert updated.name == "Updated"
    assert updated.enabled is False
    assert store.enabled() == []
    assert store.delete(created.rule_id) is True
    assert store.delete(created.rule_id) is False


def test_default_store_path_is_root_runtime_data(monkeypatch) -> None:
    monkeypatch.delenv("POLICY_STORE_PATH", raising=False)
    monkeypatch.delenv("VERCEL", raising=False)
    assert _default_policy_store_path().as_posix().endswith("/data/policies.json")


@pytest.mark.parametrize("field, value", [("name", "   "), ("rule_text", "   "), ("name", "x" * 121), ("rule_text", "x" * 4001)])
def test_policy_validation_rejects_invalid_text(field: str, value: str) -> None:
    payload = {"name": "Rule", "rule_text": "Rule text", "violation_action": Decision.BLOCK}
    payload[field] = value
    with pytest.raises(ValueError):
        PolicyRuleCreate(**payload)


def test_policy_validation_rejects_pass() -> None:
    with pytest.raises(ValueError, match="REVIEW or BLOCK"):
        PolicyRuleCreate(name="Rule", rule_text="Rule text", violation_action=Decision.PASS)
