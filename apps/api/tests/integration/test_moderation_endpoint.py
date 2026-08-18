from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_moderate_frame_returns_structured_review() -> None:
    response = client.post(
        "/api/v1/moderate/frame",
        json={
            "title": "Điều tra vụ xô xát tại Hà Nội",
            "summary": "Một người bị đâm và được đưa đi cấp cứu.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "REVIEW"
    assert body["risk_categories"] == ["violence"]
    assert body["policy_results"][0]["rule_id"] == "MOCK-VIOLENCE-001"
    assert body["requires_layer2"] is True


def test_moderate_frame_rejects_blank_title() -> None:
    response = client.post("/api/v1/moderate/frame", json={"title": "   "})

    assert response.status_code == 422


def test_moderate_frame_block_stops_layer2() -> None:
    response = client.post(
        "/api/v1/moderate/frame",
        json={
            "title": "Phát hiện thi thể đầy máu",
            "summary": "Nạn nhân được xác định đã tự sát.",
        },
    )

    assert response.status_code == 200
    assert response.json()["decision"] == "BLOCK"
    assert response.json()["requires_layer2"] is False
