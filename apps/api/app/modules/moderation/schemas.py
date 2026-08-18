from enum import Enum

from pydantic import BaseModel, Field, field_validator


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
