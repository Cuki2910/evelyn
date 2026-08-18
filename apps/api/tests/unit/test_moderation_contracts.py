import pytest
from pydantic import ValidationError

from app.modules.moderation.schemas import AnalysisStatus, Decision, FrameResponse, RiskLevel, ScriptResponse


def test_layer1_contract_rejects_block_that_allows_layer2() -> None:
    with pytest.raises(ValidationError):
        FrameResponse(
            decision=Decision.BLOCK,
            risk_level=RiskLevel.CRITICAL,
            risk_categories=["violence"],
            violations=[],
            policy_results=[],
            reason="blocked",
            requires_layer2=True,
            analysis_status=AnalysisStatus.COMPLETE,
            provider_error=None,
        )


def test_layer1_contract_rejects_pass_with_risk_categories() -> None:
    with pytest.raises(ValidationError):
        FrameResponse(
            decision=Decision.PASS,
            risk_level=RiskLevel.LOW,
            risk_categories=["violence"],
            violations=[],
            policy_results=[],
            reason="invalid",
            requires_layer2=True,
            analysis_status=AnalysisStatus.COMPLETE,
            provider_error=None,
        )


def test_layer2_contract_rejects_pass_with_revision() -> None:
    with pytest.raises(ValidationError):
        ScriptResponse(
            decision=Decision.PASS,
            risk_level=RiskLevel.LOW,
            risk_categories=[],
            violations=[],
            policy_references=[],
            reason="invalid",
            revised_script="A revision is not allowed for PASS.",
            requires_human_review=False,
            analysis_status=AnalysisStatus.COMPLETE,
            provider_error=None,
        )


@pytest.mark.parametrize("decision", [Decision.PASS, Decision.REVIEW, Decision.BLOCK])
def test_layer2_contract_requires_a_human_editor_for_every_recommendation(decision: Decision) -> None:
    with pytest.raises(ValidationError):
        ScriptResponse(
            decision=decision,
            risk_level=RiskLevel.LOW,
            risk_categories=[],
            violations=[],
            policy_references=[],
            reason="invalid",
            revised_script=None,
            requires_human_review=False,
            analysis_status=AnalysisStatus.COMPLETE,
            provider_error=None,
        )
