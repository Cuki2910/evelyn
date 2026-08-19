from app.modules.llm.prompts.layer1 import LAYER1_SYSTEM_PROMPT
from app.modules.llm.prompts.layer2 import LAYER2_SYSTEM_PROMPT
from app.modules.policy.development_policy import ALLOWED_DEVELOPMENT_POLICY_IDS


def test_both_prompts_include_shared_press_dai_and_tiktok_rules() -> None:
    for prompt in (LAYER1_SYSTEM_PROMPT, LAYER2_SYSTEM_PROMPT):
        assert "PRESS-LAW-ARTICLE-8-ACCURACY-001" in prompt
        assert "DAI-POLICY-PARLIAMENT-001" in prompt
        assert "TIKTOK-CG-MISINFORMATION-001" in prompt


def test_shared_rule_ids_are_accepted_by_structured_output_contract() -> None:
    assert "PRESS-LAW-ARTICLE-8-ACCURACY-001" in ALLOWED_DEVELOPMENT_POLICY_IDS
    assert "DAI-POLICY-PARLIAMENT-001" in ALLOWED_DEVELOPMENT_POLICY_IDS
    assert "TIKTOK-CG-MISINFORMATION-001" in ALLOWED_DEVELOPMENT_POLICY_IDS
