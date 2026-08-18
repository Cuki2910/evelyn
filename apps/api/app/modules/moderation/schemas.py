from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.policy.development_policy import ALLOWED_DEVELOPMENT_POLICY_IDS


class Decision(str, Enum):
    PASS = "PASS"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AnalysisStatus(str, Enum):
    COMPLETE = "COMPLETE"
    PROVIDER_ERROR = "PROVIDER_ERROR"


class FrameRequest(BaseModel):
    title: str = Field(..., min_length=1)
    summary: str = ""

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("title must not be blank")
        return value


class Violation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    category: str
    severity: RiskLevel
    reason: str


class PolicyResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str
    decision: Decision
    rule_id: str
    reason: str


class FrameResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Decision
    risk_level: RiskLevel
    risk_categories: list[str]
    violations: list[Violation]
    policy_results: list[PolicyResult]
    reason: str
    requires_layer2: bool
    analysis_status: AnalysisStatus
    provider_error: str | None

    @model_validator(mode="after")
    def validate_decision_contract(self) -> "FrameResponse":
        if self.analysis_status is AnalysisStatus.COMPLETE and self.provider_error is not None:
            raise ValueError("complete moderation cannot include a provider error")
        if self.analysis_status is AnalysisStatus.PROVIDER_ERROR:
            if self.decision is not Decision.REVIEW or not self.provider_error:
                raise ValueError("provider failures must be explicit REVIEW results")
        if self.requires_layer2 is not (self.decision is not Decision.BLOCK):
            raise ValueError("requires_layer2 must match the Layer 1 decision")
        if self.decision is Decision.PASS and (self.violations or self.risk_categories):
            raise ValueError("PASS cannot contain risks or violations")
        return self


class ScriptRequest(BaseModel):
    title: str | None = Field(default=None, max_length=500)
    script: str = Field(..., min_length=1)

    @field_validator("script")
    @classmethod
    def script_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("script must not be blank")
        return value

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank_when_provided(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            return None
        return value


class SuggestedAction(str, Enum):
    KEEP = "KEEP"
    REWRITE = "REWRITE"
    REMOVE = "REMOVE"


class ScriptViolation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(..., min_length=1)
    category: str
    severity: RiskLevel
    reason: str
    suggested_action: SuggestedAction


class PolicyReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_id: str
    category: str
    reason: str

    @field_validator("rule_id")
    @classmethod
    def rule_id_must_be_from_development_policy(cls, value: str) -> str:
        if value not in ALLOWED_DEVELOPMENT_POLICY_IDS:
            raise ValueError("rule_id must be supplied by the development policy")
        return value


class ScriptResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Decision
    risk_level: RiskLevel
    risk_categories: list[str]
    violations: list[ScriptViolation]
    policy_references: list[PolicyReference]
    reason: str
    revised_script: str | None
    requires_human_review: bool
    analysis_status: AnalysisStatus
    provider_error: str | None

    @model_validator(mode="after")
    def validate_revision_contract(self) -> "ScriptResponse":
        if self.analysis_status is AnalysisStatus.COMPLETE and self.provider_error is not None:
            raise ValueError("complete moderation cannot include a provider error")
        if self.analysis_status is AnalysisStatus.PROVIDER_ERROR:
            if (
                self.decision is not Decision.REVIEW
                or not self.provider_error
                or self.revised_script is not None
            ):
                raise ValueError("provider failures must be explicit unrevised REVIEW results")
        if self.decision is not Decision.REVIEW and self.revised_script is not None:
            raise ValueError("revised_script is only allowed for REVIEW")
        if self.decision is Decision.PASS and (self.violations or self.risk_categories):
            raise ValueError("PASS cannot contain risks or violations")
        if not self.requires_human_review:
            raise ValueError("a human editor must make the final publishing decision")
        return self
