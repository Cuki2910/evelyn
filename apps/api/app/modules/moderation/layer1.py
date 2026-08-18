import re
from collections.abc import Sequence

from app.modules.moderation.decision_engine import DecisionEngine
from app.modules.moderation.risk_classifier import MockRiskClassifier
from app.modules.moderation.schemas import (
    AnalysisStatus,
    Decision,
    FrameRequest,
    FrameResponse,
    PolicyResult,
    RiskLevel,
    Violation,
)


class Layer1Moderator:
    """Orchestrates deterministic development-only Layer 1 moderation."""

    _POLICY_RULES: dict[str, tuple[str, str]] = {
        "violence": ("MOCK-VIOLENCE-001", "Có yếu tố bạo lực."),
        "drugs": ("MOCK-DRUGS-001", "Có yếu tố ma túy."),
        "weapons": ("MOCK-WEAPONS-001", "Có yếu tố vũ khí."),
        "sexual_content": ("MOCK-SEXUAL-CONTENT-001", "Có yếu tố tình dục."),
        "self_harm": ("MOCK-SELF-HARM-001", "Có yếu tố tự hại."),
        "hate": ("MOCK-HATE-001", "Có yếu tố thù ghét."),
        "crime": ("MOCK-CRIME-001", "Có yếu tố tội phạm."),
        "sensitive": ("MOCK-SENSITIVE-001", "Có yếu tố nhạy cảm."),
    }
    _RISK_PRIORITY = {
        RiskLevel.LOW: 0,
        RiskLevel.MEDIUM: 1,
        RiskLevel.HIGH: 2,
        RiskLevel.CRITICAL: 3,
    }
    _EXTREME_BLOCK_TERMS = ("thi thể", "máu", "tự sát")

    def __init__(self, classifier: MockRiskClassifier | None = None) -> None:
        self._classifier = classifier or MockRiskClassifier()

    def moderate(self, request: FrameRequest) -> FrameResponse:
        text = self._combine_text(request.title, request.summary)
        violations = list(self._classifier.classify(text))
        policy_results = self._evaluate_policies(text, violations)
        decision = DecisionEngine.decide(policy_results)

        return FrameResponse(
            decision=decision,
            risk_level=self._risk_level(violations),
            risk_categories=list(dict.fromkeys(item.category for item in violations)),
            violations=violations,
            policy_results=policy_results,
            reason=self._reason_for(decision),
            requires_layer2=decision is not Decision.BLOCK,
            analysis_status=AnalysisStatus.COMPLETE,
            provider_error=None,
        )

    @staticmethod
    def _combine_text(title: str, summary: str) -> str:
        parts = (Layer1Moderator._normalize(title), Layer1Moderator._normalize(summary))
        return "\n".join(part for part in parts if part)

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r"\s+", " ", text.strip())

    def _evaluate_policies(
        self, text: str, violations: Sequence[Violation]
    ) -> list[PolicyResult]:
        normalized = text.casefold()
        if self._is_explicit_extreme_case(normalized):
            return [
                PolicyResult(
                    source="mock_tiktok_policy",
                    decision=Decision.BLOCK,
                    rule_id="MOCK-EXTREME-VIOLENCE-001",
                    reason="Mock case có mô tả cực đoan về bạo lực và tự hại.",
                )
            ]

        if not violations:
            return [
                PolicyResult(
                    source="mock_tiktok_policy",
                    decision=Decision.PASS,
                    rule_id="MOCK-GENERAL-001",
                    reason="Không phát hiện yếu tố rủi ro trong bộ từ khóa mock.",
                )
            ]

        results: list[PolicyResult] = []
        for violation in violations:
            rule = self._POLICY_RULES.get(violation.category)
            if rule is None:
                results.append(
                    PolicyResult(
                        source="mock_tiktok_policy",
                        decision=Decision.REVIEW,
                        rule_id="MOCK-UNKNOWN-001",
                        reason="Không xác định được policy mock phù hợp.",
                    )
                )
                continue
            rule_id, reason = rule
            results.append(
                PolicyResult(
                    source="mock_tiktok_policy",
                    decision=Decision.REVIEW,
                    rule_id=rule_id,
                    reason=reason,
                )
            )
        return results

    def _is_explicit_extreme_case(self, normalized_text: str) -> bool:
        return all(term in normalized_text for term in self._EXTREME_BLOCK_TERMS)

    def _risk_level(self, violations: Sequence[Violation]) -> RiskLevel:
        if not violations:
            return RiskLevel.LOW
        return max(violations, key=lambda item: self._RISK_PRIORITY[item.severity]).severity

    @staticmethod
    def _reason_for(decision: Decision) -> str:
        if decision is Decision.BLOCK:
            return "Nội dung có yếu tố cực đoan theo mock policy và không tiếp tục Layer 2."
        if decision is Decision.REVIEW:
            return "Nội dung có yếu tố cần được kiểm tra kỹ hơn trước khi tiếp tục."
        return "Không phát hiện yếu tố rủi ro trong bộ kiểm tra mock."
