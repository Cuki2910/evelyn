from app.modules.moderation.risk_classifier import MockRiskClassifier
from app.modules.moderation.schemas import RiskLevel


def test_classify_detects_violence_and_preserves_matched_text() -> None:
    violations = MockRiskClassifier().classify("Một người bị đâm và được cấp cứu.")

    assert len(violations) == 1
    assert violations[0].category == "violence"
    assert violations[0].text == "đâm"
    assert violations[0].severity is RiskLevel.MEDIUM


def test_classify_detects_drugs() -> None:
    violations = MockRiskClassifier().classify("Thu giữ heroin và ma túy.")

    assert {violation.category for violation in violations} == {"drugs"}


def test_classify_returns_empty_for_unmatched_text() -> None:
    assert MockRiskClassifier().classify("Dự báo thời tiết có mưa.") == []


def test_classify_does_not_match_keyword_inside_another_word() -> None:
    assert MockRiskClassifier().classify("Nhiệt độ dao động trong ngày.") == []
