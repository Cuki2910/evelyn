from app.modules.moderation.layer1 import Layer1Moderator
from app.modules.moderation.schemas import Decision, FrameRequest, RiskLevel


def test_moderate_passes_general_weather_news() -> None:
    result = Layer1Moderator().moderate(
        FrameRequest(
            title="Hà Nội dự báo thời tiết có mưa vào chiều nay",
            summary="Nhiệt độ dao động từ 27 đến 32 độ C.",
        )
    )

    assert result.decision is Decision.PASS
    assert result.risk_level is RiskLevel.LOW
    assert result.requires_layer2 is True


def test_moderate_reviews_violence() -> None:
    result = Layer1Moderator().moderate(
        FrameRequest(
            title="Điều tra vụ xô xát tại Hà Nội",
            summary="Một người bị đâm và được đưa đi cấp cứu.",
        )
    )

    assert result.decision is Decision.REVIEW
    assert result.risk_categories == ["violence"]
    assert result.requires_layer2 is True


def test_moderate_reviews_drugs() -> None:
    result = Layer1Moderator().moderate(
        FrameRequest(
            title="Công an triệt phá đường dây ma túy",
            summary="Lực lượng chức năng thu giữ heroin và nhiều tang vật.",
        )
    )

    assert "drugs" in result.risk_categories
    assert result.decision is not Decision.PASS


def test_moderate_blocks_explicit_mock_extreme_case() -> None:
    result = Layer1Moderator().moderate(
        FrameRequest(
            title="Phát hiện thi thể đầy máu",
            summary="Nạn nhân được xác định đã tự sát.",
        )
    )

    assert result.decision is Decision.BLOCK
    assert result.requires_layer2 is False
    assert result.policy_results[0].rule_id == "MOCK-EXTREME-VIOLENCE-001"


def test_moderate_normalizes_whitespace() -> None:
    result = Layer1Moderator().moderate(
        FrameRequest(title="  Một   người bị đâm ", summary="  và cấp cứu. ")
    )

    assert result.violations[0].text == "đâm"
