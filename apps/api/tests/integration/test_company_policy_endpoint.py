from fastapi.testclient import TestClient

from app.api.v1.endpoints import company_policies
from app.main import app
from app.modules.policy.company_policy import CompanyPolicyStore


def test_policy_endpoint_crud(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(company_policies, "policy_store", CompanyPolicyStore(tmp_path / "policies.json"))
    client = TestClient(app)
    created = client.post("/api/v1/policies", json={"name": "International news", "rule_text": "Must affect Vietnam.", "violation_action": "BLOCK", "enabled": True})

    assert created.status_code == 201
    rule_id = created.json()["rule_id"]
    assert client.get("/api/v1/policies").json()["policies"][0]["rule_id"] == rule_id
    updated = client.patch(f"/api/v1/policies/{rule_id}", json={"name": "Updated", "enabled": False, "violation_action": "REVIEW"})
    assert updated.status_code == 200
    assert updated.json()["rule_id"] == rule_id
    assert updated.json()["enabled"] is False
    assert client.delete(f"/api/v1/policies/{rule_id}").status_code == 204
    assert client.patch("/api/v1/policies/COMPANY-MISSING", json={"enabled": True}).status_code == 404
    assert client.delete("/api/v1/policies/COMPANY-MISSING").status_code == 404


def test_policy_endpoint_rejects_pass(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(company_policies, "policy_store", CompanyPolicyStore(tmp_path / "policies.json"))
    response = TestClient(app).post("/api/v1/policies", json={"name": "Rule", "rule_text": "Text", "violation_action": "PASS"})
    assert response.status_code == 422
