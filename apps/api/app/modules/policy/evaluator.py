"""Semantic custom-policy contracts and deterministic decision mapping."""

from enum import Enum

from pydantic import BaseModel, ConfigDict

from app.modules.moderation.schemas import Decision
from app.modules.policy.company_policy import PolicyRule


class RuleComplianceStatus(str, Enum):
    COMPLIANT = "COMPLIANT"
    VIOLATED = "VIOLATED"
    UNCERTAIN = "UNCERTAIN"


class RuleEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_id: str
    status: RuleComplianceStatus
    evidence: str | None
    reason: str


class PolicyEvaluationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evaluations: list[RuleEvaluation]


class CustomPolicyResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_id: str
    name: str
    status: RuleComplianceStatus
    decision: Decision
    evidence: str | None
    reason: str


def validate_rule_coverage(
    response: PolicyEvaluationResponse, rules: list[PolicyRule]
) -> PolicyEvaluationResponse:
    expected = {rule.rule_id for rule in rules}
    returned = [evaluation.rule_id for evaluation in response.evaluations]
    if len(returned) != len(set(returned)):
        raise ValueError("Policy evaluation contains duplicate rule IDs.")
    if set(returned) != expected:
        raise ValueError("Policy evaluation does not cover exactly the supplied rule IDs.")
    return response


def map_evaluation(rule: PolicyRule, evaluation: RuleEvaluation) -> CustomPolicyResult:
    if evaluation.status is RuleComplianceStatus.COMPLIANT:
        decision = Decision.PASS
    elif evaluation.status is RuleComplianceStatus.UNCERTAIN:
        decision = Decision.REVIEW
    else:
        decision = rule.violation_action
    return CustomPolicyResult(
        rule_id=rule.rule_id,
        name=rule.name,
        status=evaluation.status,
        decision=decision,
        evidence=evaluation.evidence,
        reason=evaluation.reason,
    )
