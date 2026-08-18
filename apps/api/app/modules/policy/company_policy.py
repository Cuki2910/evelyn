"""Local, file-backed company policies for the demo only."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.moderation.schemas import Decision


DEMO_COMPANIES = (
    {"id": "evelyn-news", "name": "Evelyn News"},
    {"id": "city-desk", "name": "City Desk"},
)


class CompanyPolicyCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: str = Field(..., min_length=1, max_length=80)
    title: str = Field(..., min_length=3, max_length=120)
    keywords: list[str] = Field(..., min_length=1, max_length=20)
    decision: Decision
    reason: str = Field(..., min_length=3, max_length=500)

    @field_validator("company_id")
    @classmethod
    def company_must_be_supported(cls, value: str) -> str:
        if value not in {company["id"] for company in DEMO_COMPANIES}:
            raise ValueError("company_id is not a configured demo company")
        return value

    @field_validator("keywords")
    @classmethod
    def keywords_must_not_be_blank(cls, values: list[str]) -> list[str]:
        normalized = list(dict.fromkeys(value.strip() for value in values if value.strip()))
        if not normalized:
            raise ValueError("at least one non-blank keyword is required")
        return normalized

    @field_validator("decision")
    @classmethod
    def policy_must_restrict_content(cls, value: Decision) -> Decision:
        if value is Decision.PASS:
            raise ValueError("company policies must use REVIEW or BLOCK")
        return value


class CompanyPolicy(CompanyPolicyCreate):
    id: str
    rule_id: str


class CompanyPolicyCatalog(BaseModel):
    companies: list[dict[str, str]]
    policies: list[CompanyPolicy]


class CompanyPolicyMatch(BaseModel):
    policy: CompanyPolicy
    keyword: str


class CompanyPolicyStore:
    """Owns demo policy persistence and keyword matching behind one interface."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or Path(
            os.getenv(
                "COMPANY_POLICY_STORE_PATH",
                Path(__file__).resolve().parents[2] / "runtime" / "company_policies.json",
            )
        )

    def catalog(self) -> CompanyPolicyCatalog:
        return CompanyPolicyCatalog(companies=list(DEMO_COMPANIES), policies=self._load())

    def create(self, policy: CompanyPolicyCreate) -> CompanyPolicy:
        created = CompanyPolicy(
            **policy.model_dump(),
            id=uuid4().hex,
            rule_id=self._rule_id(policy.company_id, policy.title),
        )
        policies = self._load()
        policies.append(created)
        self._save(policies)
        return created

    def delete(self, policy_id: str) -> bool:
        policies = self._load()
        remaining = [policy for policy in policies if policy.id != policy_id]
        if len(remaining) == len(policies):
            return False
        self._save(remaining)
        return True

    def find_matches(self, company_id: str, text: str) -> list[CompanyPolicyMatch]:
        normalized = text.casefold()
        matches: list[CompanyPolicyMatch] = []
        for policy in self._load():
            if policy.company_id != company_id:
                continue
            for keyword in policy.keywords:
                if keyword.casefold() in normalized:
                    matches.append(CompanyPolicyMatch(policy=policy, keyword=keyword))
                    break
        return matches

    def _load(self) -> list[CompanyPolicy]:
        if not self._path.exists():
            return []
        return [CompanyPolicy.model_validate(item) for item in json.loads(self._path.read_text("utf-8"))]

    def _save(self, policies: list[CompanyPolicy]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self._path.with_suffix(".tmp")
        temporary_path.write_text(
            json.dumps([policy.model_dump(mode="json") for policy in policies], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary_path.replace(self._path)

    @staticmethod
    def _rule_id(company_id: str, title: str) -> str:
        company = re.sub(r"[^A-Z0-9]+", "-", company_id.upper()).strip("-")
        policy = re.sub(r"[^A-Z0-9]+", "-", title.upper()).strip("-")[:32]
        return f"COMP-{company}-{policy}-{uuid4().hex[:6].upper()}"
