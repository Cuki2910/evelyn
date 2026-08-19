import os
from collections.abc import Callable

from app.modules.llm.gateway import LLMGateway
from app.modules.llm.schemas import LLMGatewayError
from app.modules.moderation.decision_engine import DecisionEngine
from app.modules.moderation.layer1 import Layer1Moderator
from app.modules.moderation.layer2 import Layer2Moderator
from app.modules.moderation.schemas import AnalysisStatus, CustomPolicyResult, Decision, FrameRequest, FrameResponse, PolicyReference, PolicyResult, RiskLevel, ScriptRequest, ScriptResponse
from app.modules.policy.company_policy import CompanyPolicyStore
from app.modules.policy.evaluator import map_evaluation


class ModerationService:
    """Composes built-in moderation with semantic custom policies in LLM mode."""

    def __init__(self, gateway_factory: Callable[[], LLMGateway] = LLMGateway, policy_store: CompanyPolicyStore | None = None) -> None:
        self._gateway_factory = gateway_factory
        self._policy_store = policy_store or CompanyPolicyStore()
        self._layer1 = Layer1Moderator()
        self._layer2 = Layer2Moderator()

    async def moderate_frame(self, request: FrameRequest) -> FrameResponse:
        if self._mode() == "mock":
            return self._layer1.moderate(request)
        try:
            gateway = self._gateway_factory()
            base = self._validate_complete_frame(await gateway.moderate_frame(request))
            rules = self._policy_store.enabled()
            if not rules:
                return base
            evaluated = await gateway.evaluate_custom_policies(stage="LAYER_1", content=f"Title:\n{request.title}\n\nSummary:\n{request.summary}", rules=rules)
            evaluations = {evaluation.rule_id: evaluation for evaluation in evaluated.evaluations}
            return self._combine_frame(base, [map_evaluation(rule, evaluations[rule.rule_id]) for rule in rules])
        except (LLMGatewayError, ValueError, OSError):
            return self._failed_frame()

    async def moderate_script(self, request: ScriptRequest) -> ScriptResponse:
        if self._mode() == "mock":
            return self._layer2.moderate(request)
        try:
            gateway = self._gateway_factory()
            base = self._validate_complete_script(await gateway.moderate_script(request))
            rules = self._policy_store.enabled()
            if not rules:
                return base
            title = f"Title:\n{request.title}\n\n" if request.title else ""
            evaluated = await gateway.evaluate_custom_policies(stage="LAYER_2", content=f"{title}Full script:\n{request.script}", rules=rules)
            evaluations = {evaluation.rule_id: evaluation for evaluation in evaluated.evaluations}
            return self._combine_script(base, [map_evaluation(rule, evaluations[rule.rule_id]) for rule in rules])
        except (LLMGatewayError, ValueError, OSError):
            return self._failed_script()

    @staticmethod
    def _mode() -> str:
        mode = os.getenv("MODERATION_MODE", "mock").strip().casefold()
        if mode not in {"mock", "llm"}:
            raise LLMGatewayError("MODERATION_MODE must be either 'mock' or 'llm'.")
        return mode

    @staticmethod
    def _validate_complete_frame(result: FrameResponse) -> FrameResponse:
        validated = FrameResponse.model_validate(result.model_dump())
        if validated.analysis_status is not AnalysisStatus.COMPLETE or validated.decision is not DecisionEngine.decide(validated.policy_results):
            raise LLMGatewayError("LLM result did not satisfy the Layer 1 contract.")
        return validated

    @staticmethod
    def _validate_complete_script(result: ScriptResponse) -> ScriptResponse:
        validated = ScriptResponse.model_validate(result.model_dump())
        if validated.analysis_status is not AnalysisStatus.COMPLETE:
            raise LLMGatewayError("LLM result did not complete moderation.")
        return validated

    @staticmethod
    def _combine_frame(base: FrameResponse, custom: list) -> FrameResponse:
        custom_results = [CustomPolicyResult(**result.model_dump()) for result in custom]
        decisions = [*base.policy_results, *[PolicyResult(source="semantic_custom_policy", decision=result.decision, rule_id=result.rule_id, reason=result.reason) for result in custom]]
        decision = DecisionEngine.decide(decisions)
        restricted = any(result.decision is not Decision.PASS for result in custom)
        return FrameResponse(decision=decision, risk_level=RiskLevel.CRITICAL if any(result.decision is Decision.BLOCK for result in custom) else (RiskLevel.MEDIUM if restricted else base.risk_level), risk_categories=list(dict.fromkeys([*base.risk_categories, *(["custom_policy"] if restricted else [])])), violations=base.violations, policy_results=decisions, custom_policy_results=custom_results, reason="Custom policy evaluation requires editor attention." if restricted else base.reason, requires_layer2=decision is not Decision.BLOCK, analysis_status=base.analysis_status, provider_error=base.provider_error)

    @staticmethod
    def _combine_script(base: ScriptResponse, custom: list) -> ScriptResponse:
        custom_results = [CustomPolicyResult(**result.model_dump()) for result in custom]
        decisions = [base.decision, *(result.decision for result in custom)]
        decision = Decision.BLOCK if Decision.BLOCK in decisions else (Decision.REVIEW if Decision.REVIEW in decisions else Decision.PASS)
        restricted = any(result.decision is not Decision.PASS for result in custom)
        return ScriptResponse(decision=decision, risk_level=RiskLevel.CRITICAL if Decision.BLOCK in decisions else (RiskLevel.MEDIUM if restricted else base.risk_level), risk_categories=list(dict.fromkeys([*base.risk_categories, *(["custom_policy"] if restricted else [])])), violations=base.violations, policy_references=[*base.policy_references, *[PolicyReference(rule_id=result.rule_id, category="custom_policy", reason=result.reason) for result in custom]], custom_policy_results=custom_results, reason="Custom policy evaluation requires editor attention." if restricted else base.reason, revised_script=None if restricted or decision is Decision.BLOCK else base.revised_script, requires_human_review=True, analysis_status=base.analysis_status, provider_error=base.provider_error)

    @staticmethod
    def _failed_frame() -> FrameResponse:
        return FrameResponse(decision=Decision.REVIEW, risk_level=RiskLevel.MEDIUM, risk_categories=["unknown"], violations=[], policy_results=[PolicyResult(source="llm_gateway", decision=Decision.REVIEW, rule_id="DEV-TT-UNKNOWN", reason="LLM output was unavailable or invalid; editor review is required.")], custom_policy_results=[], reason="Moderation evidence is incomplete; editor review is required.", requires_layer2=True, analysis_status=AnalysisStatus.PROVIDER_ERROR, provider_error="The moderation provider was unavailable or returned invalid output.")

    @staticmethod
    def _failed_script() -> ScriptResponse:
        return ScriptResponse(decision=Decision.REVIEW, risk_level=RiskLevel.MEDIUM, risk_categories=["unknown"], violations=[], policy_references=[PolicyReference(rule_id="DEV-TT-UNKNOWN", category="unknown", reason="LLM output was unavailable or invalid; editor review is required.")], custom_policy_results=[], reason="Moderation evidence is incomplete; editor review is required.", revised_script=None, requires_human_review=True, analysis_status=AnalysisStatus.PROVIDER_ERROR, provider_error="The moderation provider was unavailable or returned invalid output.")
