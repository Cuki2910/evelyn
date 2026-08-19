from fastapi.testclient import TestClient

from app.api.v1.endpoints import company_policies, moderation
from app.main import app
from app.modules.policy.company_policy import CompanyPolicyStore


def test_company_policy_endpoint_create_match_and_delete(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("MODERATION_MODE", "mock")
    store = CompanyPolicyStore(tmp_path / "company_policies.json")
    monkeypatch.setattr(company_policies, "policy_store", store)
    monkeypatch.setattr(moderation.moderation_service, "_policy_store", store)
    client = TestClient(app)

    created = client.post(
        "/api/v1/policies",
        json={
            "company_id": "evelyn-news",
            "title": "E2E embargo",
            "keywords": ["e2e-embargo"],
            "decision": "BLOCK",
            "reason": "This content is embargoed for the end-to-end test.",
        },
    )

    assert created.status_code == 201
    policy = created.json()
    assert policy["rule_id"].startswith("COMP-EVELYN-NEWS-E2E-EMBARGO-")

    listed = client.get("/api/v1/policies")
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["policies"]] == [policy["id"]]

    moderated = client.post(
        "/api/v1/moderate/frame",
        json={
            "company_id": "evelyn-news",
            "title": "e2e-embargo bulletin",
            "summary": "Synthetic end-to-end test content.",
        },
    )
    assert moderated.status_code == 200
    assert moderated.json()["decision"] == "BLOCK"
    assert moderated.json()["policy_results"][-1]["rule_id"] == policy["rule_id"]

    deleted = client.delete(f"/api/v1/policies/{policy['id']}")
    assert deleted.status_code == 204
    assert client.get("/api/v1/policies").json()["policies"] == []
