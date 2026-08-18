from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator

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
    text: str
    category: str
    severity: RiskLevel
    reason: str


class PolicyResult(BaseModel):
    source: str = "mock_tiktok_policy"
    decision: Decision
    rule_id: str
    reason: str


class FrameResponse(BaseModel):
    decision: Decision
    risk_level: RiskLevel
    risk_categories: list[str]
    violations: list[Violation]
    policy_results: list[PolicyResult]
    reason: str
    requires_layer2: bool


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
    text: str = Field(..., min_length=1)
    category: str
    severity: RiskLevel
    reason: str
    suggested_action: SuggestedAction


class PolicyReference(BaseModel):
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
    decision: Decision
    risk_level: RiskLevel
    risk_categories: list[str]
    violations: list[ScriptViolation]
    policy_references: list[PolicyReference]
    reason: str
    revised_script: str | None = None
    requires_human_review: bool

    @model_validator(mode="after")
    def validate_revision_contract(self) -> "ScriptResponse":
        if self.decision is not Decision.REVIEW and self.revised_script is not None:
            raise ValueError("revised_script is only allowed for REVIEW")
        if self.decision is Decision.PASS and (self.violations or self.risk_categories):
            raise ValueError("PASS cannot contain risks or violations")
        return self
