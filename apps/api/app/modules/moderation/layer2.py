import re

from app.modules.moderation.risk_classifier import MockRiskClassifier
from app.modules.moderation.schemas import (
    AnalysisStatus,
    Decision,
    PolicyReference,
    RiskLevel,
    ScriptRequest,
    ScriptResponse,
    ScriptViolation,
    SuggestedAction,
)
from app.modules.policy.development_policy import DEVELOPMENT_POLICY_RULES


class Layer2Moderator:
    """Deterministic, development-only full-script moderation for offline demos."""

    _RISK_PRIORITY = {
        RiskLevel.LOW: 0,
        RiskLevel.MEDIUM: 1,
        RiskLevel.HIGH: 2,
        RiskLevel.CRITICAL: 3,
    }
    _BLOCK_TERMS = ("thi thể", "máu", "tự sát")
    _REMOVABLE_DETAILS = ("cận cảnh", "máu me", "đẫm máu", "rùng rợn")

    def __init__(self, classifier: MockRiskClassifier | None = None) -> None:
        self._classifier = classifier or MockRiskClassifier()

    def moderate(self, request: ScriptRequest) -> ScriptResponse:
        script = self._normalize(request.script)
        classified = self._classifier.classify(script)
        normalized = script.casefold()

        if self._is_severe_case(normalized):
            return ScriptResponse(
                decision=Decision.BLOCK,
                risk_level=RiskLevel.CRITICAL,
                risk_categories=["graphic_violence", "self_harm"],
                violations=[
                    ScriptViolation(
                        text=script,
                        category="graphic_violence",
                        severity=RiskLevel.CRITICAL,
                        reason="The script combines graphic violence with explicit self-harm.",
                        suggested_action=SuggestedAction.REMOVE,
                    )
                ],
                policy_references=[
                    self._policy_reference("graphic_violence"),
                    self._policy_reference("self_harm"),
                ],
                reason="This synthetic development-policy case cannot be safely revised.",
                revised_script=None,
                requires_human_review=True,
                analysis_status=AnalysisStatus.COMPLETE,
                provider_error=None,
            )

        if not classified:
            return ScriptResponse(
                decision=Decision.PASS,
                risk_level=RiskLevel.LOW,
                risk_categories=[],
                violations=[],
                policy_references=[],
                reason="No risks were found by the deterministic development checks.",
                revised_script=None,
                requires_human_review=False,
                analysis_status=AnalysisStatus.COMPLETE,
                provider_error=None,
            )

        violations = [
            ScriptViolation(
                text=item.text,
                category=item.category,
                severity=item.severity,
                reason=item.reason,
                suggested_action=SuggestedAction.REWRITE,
            )
            for item in classified
        ]
        categories = list(dict.fromkeys(item.category for item in violations))
        revised_script = self._remove_nonessential_presentation_details(script)

        return ScriptResponse(
            decision=Decision.REVIEW,
            risk_level=max(
                (item.severity for item in violations),
                key=lambda level: self._RISK_PRIORITY[level],
            ),
            risk_categories=categories,
            violations=violations,
            policy_references=[self._policy_reference(category) for category in categories],
            reason="The script needs an editor's review before publication.",
            revised_script=revised_script,
            requires_human_review=True,
            analysis_status=AnalysisStatus.COMPLETE,
            provider_error=None,
        )

    @classmethod
    def _normalize(cls, text: str) -> str:
        return re.sub(r"\s+", " ", text.strip())

    def _is_severe_case(self, normalized_script: str) -> bool:
        return all(term in normalized_script for term in self._BLOCK_TERMS)

    @classmethod
    def _remove_nonessential_presentation_details(cls, script: str) -> str | None:
        revised = script
        for detail in cls._REMOVABLE_DETAILS:
            revised = re.sub(rf"\b{re.escape(detail)}\b", "", revised, flags=re.IGNORECASE)
        revised = re.sub(r"\s{2,}", " ", revised)
        revised = re.sub(r"\s+([,.;:!?])", r"\1", revised).strip()
        return revised if revised != script else None

    @staticmethod
    def _policy_reference(category: str) -> PolicyReference:
        rule = DEVELOPMENT_POLICY_RULES.get(category, DEVELOPMENT_POLICY_RULES["unknown"])
        return PolicyReference(rule_id=rule["rule_id"], category=category, reason=rule["reason"])
