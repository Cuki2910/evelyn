import pytest

from app.modules.moderation.decision_engine import DecisionEngine
from app.modules.moderation.schemas import Decision, PolicyResult


def policy_result(decision: Decision) -> PolicyResult:
    return PolicyResult(
        source="mock_tiktok_policy", decision=decision, rule_id="MOCK-TEST-001", reason="test"
    )


@pytest.mark.parametrize(
    ("results", "expected"),
    [
        ([Decision.PASS, Decision.PASS], Decision.PASS),
        ([Decision.PASS, Decision.REVIEW], Decision.REVIEW),
        ([Decision.REVIEW, Decision.REVIEW], Decision.REVIEW),
        ([Decision.PASS, Decision.BLOCK], Decision.BLOCK),
        ([Decision.REVIEW, Decision.BLOCK], Decision.BLOCK),
    ],
)
def test_decide_uses_block_review_pass_priority(
    results: list[Decision], expected: Decision
) -> None:
    assert DecisionEngine.decide([policy_result(result) for result in results]) is expected


def test_decide_reviews_when_no_policy_evidence_is_available() -> None:
    assert DecisionEngine.decide([]) is Decision.REVIEW
