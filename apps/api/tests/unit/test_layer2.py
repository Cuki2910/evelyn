from app.modules.moderation.layer2 import Layer2Moderator
from app.modules.moderation.schemas import Decision, ScriptRequest


def test_moderate_script_passes_neutral_public_information() -> None:
    result = Layer2Moderator().moderate(
        ScriptRequest(script="H\u00e0 N\u1ed9i s\u1ebd c\u00f3 m\u01b0a nh\u1eb9 v\u00e0o bu\u1ed5i chi\u1ec1u. Ng\u01b0\u1eddi d\u00e2n c\u1ea7n mang \u00e1o m\u01b0a.")
    )

    assert result.decision is Decision.PASS
    assert result.violations == []
    assert result.revised_script is None


def test_moderate_script_reviews_and_removes_nonessential_presentation_detail() -> None:
    script = "Video c\u1eadn c\u1ea3nh m\u00e1u me cho th\u1ea5y m\u1ed9t ng\u01b0\u1eddi b\u1ecb \u0111\u00e2m v\u00e0 \u0111\u01b0\u1ee3c \u0111\u01b0a \u0111i c\u1ea5p c\u1ee9u."
    result = Layer2Moderator().moderate(ScriptRequest(script=script))

    assert result.decision is Decision.REVIEW
    assert result.risk_categories == ["violence"]
    assert result.revised_script is not None
    assert "c\u1eadn c\u1ea3nh" not in result.revised_script
    assert "m\u00e1u me" not in result.revised_script


def test_moderate_script_blocks_synthetic_severe_case() -> None:
    result = Layer2Moderator().moderate(
        ScriptRequest(script="Ph\u00e1t hi\u1ec7n thi th\u1ec3 \u0111\u1ea7y m\u00e1u; n\u1ea1n nh\u00e2n \u0111\u00e3 t\u1ef1 s\u00e1t.")
    )

    assert result.decision is Decision.BLOCK
    assert result.revised_script is None
    assert result.requires_human_review is True
