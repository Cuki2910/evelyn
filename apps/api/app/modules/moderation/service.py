import os
from collections.abc import Callable

from app.modules.llm.gateway import LLMGateway
from app.modules.llm.schemas import LLMGatewayError
from app.modules.moderation.layer1 import Layer1Moderator
from app.modules.moderation.layer2 import Layer2Moderator
from app.modules.moderation.decision_engine import DecisionEngine
from app.modules.moderation.schemas import (
    AnalysisStatus,
    Decision,
    FrameRequest,
    FrameResponse,
    PolicyReference,
    PolicyResult,
    RiskLevel,
    ScriptRequest,
    ScriptResponse,
    ScriptViolation,
    SuggestedAction,
    Violation,
)
from app.modules.policy.company_policy import CompanyPolicyMatch, CompanyPolicyStore


class ModerationService:
    """Selects offline mock or real LLM moderation without changing endpoint contracts."""

    def __init__(
        self,
        gateway_factory: Callable[[], LLMGateway] = LLMGateway,
        policy_store: CompanyPolicyStore | None = None,
    ) -> None:
        self._gateway_factory = gateway_factory
        self._policy_store = policy_store or CompanyPolicyStore()
        self._layer1 = Layer1Moderator()
        self._layer2 = Layer2Moderator()

    async def moderate_frame(self, request: FrameRequest) -> FrameResponse:
        if self._mode() == "mock":
            return self._apply_company_frame_policies(self._layer1.moderate(request), request)
        try:
            result = await self._gateway_factory().moderate_frame(request)
            return self._apply_company_frame_policies(self._validate_complete_frame(result), request)
        except (LLMGatewayError, ValueError):
            return FrameResponse(
                decision=Decision.REVIEW,
                risk_level=RiskLevel.MEDIUM,
                risk_categories=["unknown"],
                violations=[],
                policy_results=[
                    PolicyResult(
                        source="llm_gateway",
                        decision=Decision.REVIEW,
                        rule_id="DEV-TT-UNKNOWN",
                        reason="LLM output was unavailable or invalid; editor review is required.",
                    )
                ],
                reason="Moderation evidence is incomplete; editor review is required.",
                requires_layer2=True,
                analysis_status=AnalysisStatus.PROVIDER_ERROR,
                provider_error="The moderation provider was unavailable or returned invalid output.",
            )

    async def moderate_script(self, request: ScriptRequest) -> ScriptResponse:
        if self._mode() == "mock":
            return self._apply_company_script_policies(self._layer2.moderate(request), request)
        try:
            result = await self._gateway_factory().moderate_script(request)
            return self._apply_company_script_policies(self._validate_complete_script(result), request)
        except (LLMGatewayError, ValueError):
            return ScriptResponse(
                decision=Decision.REVIEW,
                risk_level=RiskLevel.MEDIUM,
                risk_categories=["unknown"],
                violations=[],
                policy_references=[
                    PolicyReference(
                        rule_id="DEV-TT-UNKNOWN",
                        category="unknown",
                        reason="LLM output was unavailable or invalid; editor review is required.",
                    )
                ],
                reason="Moderation evidence is incomplete; editor review is required.",
                revised_script=None,
                requires_human_review=True,
                analysis_status=AnalysisStatus.PROVIDER_ERROR,
                provider_error="The moderation provider was unavailable or returned invalid output.",
            )

    @staticmethod
    def _mode() -> str:
        mode = os.getenv("MODERATION_MODE", "mock").strip().casefold()
        if mode not in {"mock", "llm"}:
            raise LLMGatewayError("MODERATION_MODE must be either 'mock' or 'llm'.")
        return mode

    @staticmethod
    def _validate_complete_frame(result: FrameResponse) -> FrameResponse:
        validated = FrameResponse.model_validate(result.model_dump())
        if validated.analysis_status is not AnalysisStatus.COMPLETE:
            raise LLMGatewayError("LLM result did not complete moderation.")
        if validated.decision is not DecisionEngine.decide(validated.policy_results):
            raise LLMGatewayError("LLM decision conflicts with its policy results.")
        return validated

    @staticmethod
    def _validate_complete_script(result: ScriptResponse) -> ScriptResponse:
        validated = ScriptResponse.model_validate(result.model_dump())
        if validated.analysis_status is not AnalysisStatus.COMPLETE:
            raise LLMGatewayError("LLM result did not complete moderation.")
        return validated

    def _apply_company_frame_policies(
        self, result: FrameResponse, request: FrameRequest
    ) -> FrameResponse:
        matches = self._policy_store.find_matches(
            request.company_id, f"{request.title}\n{request.summary}"
        )
        if not matches:
            return result

        policy_results = [*result.policy_results, *[self._frame_policy_result(match) for match in matches]]
        violations = [*result.violations, *[self._frame_violation(match) for match in matches]]
        decision = DecisionEngine.decide(policy_results)
        return FrameResponse(
            decision=decision,
            risk_level=self._risk_level(result.risk_level, matches),
            risk_categories=list(dict.fromkeys([*result.risk_categories, "company_policy"])),
            violations=violations,
            policy_results=policy_results,
            reason="A selected company demo policy matched this content.",
            requires_layer2=decision is not Decision.BLOCK,
            analysis_status=result.analysis_status,
            provider_error=result.provider_error,
        )

    def _apply_company_script_policies(
        self, result: ScriptResponse, request: ScriptRequest
    ) -> ScriptResponse:
        matches = self._policy_store.find_matches(request.company_id, request.script)
        if not matches:
            return result

        decision = (
            Decision.BLOCK
            if result.decision is Decision.BLOCK or any(match.policy.decision is Decision.BLOCK for match in matches)
            else Decision.REVIEW
        )
        return ScriptResponse(
            decision=decision,
            risk_level=self._risk_level(result.risk_level, matches),
            risk_categories=list(dict.fromkeys([*result.risk_categories, "company_policy"])),
            violations=[*result.violations, *[self._script_violation(match) for match in matches]],
            policy_references=[
                *result.policy_references,
                *[
                    PolicyReference(
                        rule_id=match.policy.rule_id,
                        category="company_policy",
                        reason=match.policy.reason,
                    )
                    for match in matches
                ],
            ],
            reason="A selected company demo policy matched this script.",
            revised_script=None if decision is Decision.BLOCK else result.revised_script,
            requires_human_review=True,
            analysis_status=result.analysis_status,
            provider_error=result.provider_error,
        )

    @staticmethod
    def _frame_policy_result(match: CompanyPolicyMatch) -> PolicyResult:
        return PolicyResult(
            source="company_demo_policy",
            decision=match.policy.decision,
            rule_id=match.policy.rule_id,
            reason=match.policy.reason,
        )

    @staticmethod
    def _frame_violation(match: CompanyPolicyMatch) -> Violation:
        return Violation(
            text=match.keyword,
            category="company_policy",
            severity=RiskLevel.CRITICAL if match.policy.decision is Decision.BLOCK else RiskLevel.MEDIUM,
            reason=match.policy.reason,
        )

    @staticmethod
    def _script_violation(match: CompanyPolicyMatch) -> ScriptViolation:
        return ScriptViolation(
            text=match.keyword,
            category="company_policy",
            severity=RiskLevel.CRITICAL if match.policy.decision is Decision.BLOCK else RiskLevel.MEDIUM,
            reason=match.policy.reason,
            suggested_action=(
                SuggestedAction.REMOVE if match.policy.decision is Decision.BLOCK else SuggestedAction.REWRITE
            ),
        )

    @staticmethod
    def _risk_level(current: RiskLevel, matches: list[CompanyPolicyMatch]) -> RiskLevel:
        if current is RiskLevel.CRITICAL or any(match.policy.decision is Decision.BLOCK for match in matches):
            return RiskLevel.CRITICAL
        if current in {RiskLevel.HIGH, RiskLevel.MEDIUM}:
            return current
        return RiskLevel.MEDIUM
