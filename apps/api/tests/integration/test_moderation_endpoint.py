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


def test_moderate_script_returns_review_with_structured_evidence() -> None:
    response = client.post(
        "/api/v1/moderate/script",
        json={"script": "Video c\u1eadn c\u1ea3nh m\u00e1u me cho th\u1ea5y m\u1ed9t ng\u01b0\u1eddi b\u1ecb \u0111\u00e2m."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "REVIEW"
    assert body["violations"][0]["category"] == "violence"
    assert body["policy_references"][0]["rule_id"] == "DEV-TT-VIOLENCE-001"
    assert body["revised_script"] is not None


def test_moderate_script_rejects_blank_script() -> None:
    response = client.post("/api/v1/moderate/script", json={"script": "   "})

    assert response.status_code == 422
