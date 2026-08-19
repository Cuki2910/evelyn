"""Small, replaceable JSON-backed store for semantic custom policy rules."""

from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.moderation.schemas import Decision


class PolicyRuleCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=120)
    rule_text: str = Field(..., min_length=1, max_length=4000)
    violation_action: Decision
    enabled: bool = True

    @field_validator("name", "rule_text")
    @classmethod
    def trim_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be blank")
        return value

    @field_validator("violation_action")
    @classmethod
    def only_restrictive_actions(cls, value: Decision) -> Decision:
        if value is Decision.PASS:
            raise ValueError("violation_action must be REVIEW or BLOCK")
        return value


class PolicyRuleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=120)
    rule_text: str | None = Field(default=None, min_length=1, max_length=4000)
    violation_action: Decision | None = None
    enabled: bool | None = None

    @field_validator("name", "rule_text")
    @classmethod
    def trim_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("value must not be blank")
        return value

    @field_validator("violation_action")
    @classmethod
    def only_restrictive_actions(cls, value: Decision | None) -> Decision | None:
        if value is Decision.PASS:
            raise ValueError("violation_action must be REVIEW or BLOCK")
        return value


class PolicyRule(PolicyRuleCreate):
    rule_id: str


class PolicyRuleList(BaseModel):
    policies: list[PolicyRule]


def _default_policy_store_path() -> Path:
    configured_path = os.getenv("POLICY_STORE_PATH")
    if configured_path:
        return Path(configured_path)
    if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        return Path("/tmp/evelyn/policies.json")
    return Path(__file__).resolve().parents[5] / "data" / "policies.json"


class CompanyPolicyStore:
    """Persistence boundary; semantic evaluation deliberately lives elsewhere."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or _default_policy_store_path()

    def list(self) -> list[PolicyRule]:
        return self._load()

    def enabled(self) -> list[PolicyRule]:
        return [policy for policy in self._load() if policy.enabled]

    def create(self, policy: PolicyRuleCreate) -> PolicyRule:
        created = PolicyRule(**policy.model_dump(), rule_id=f"COMPANY-{uuid4().hex[:12].upper()}")
        policies = self._load()
        policies.append(created)
        self._save(policies)
        return created

    def update(self, rule_id: str, update: PolicyRuleUpdate) -> PolicyRule | None:
        policies = self._load()
        for index, policy in enumerate(policies):
            if policy.rule_id == rule_id:
                policies[index] = PolicyRule(
                    **(policy.model_dump() | update.model_dump(exclude_unset=True))
                )
                self._save(policies)
                return policies[index]
        return None

    def delete(self, rule_id: str) -> bool:
        policies = self._load()
        remaining = [policy for policy in policies if policy.rule_id != rule_id]
        if len(remaining) == len(policies):
            return False
        self._save(remaining)
        return True

    def _load(self) -> list[PolicyRule]:
        if not self._path.exists():
            return []
        return [PolicyRule.model_validate(item) for item in json.loads(self._path.read_text("utf-8"))]

    def _save(self, policies: list[PolicyRule]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self._path.with_suffix(".tmp")
        temporary_path.write_text(
            json.dumps([policy.model_dump(mode="json") for policy in policies], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary_path.replace(self._path)
