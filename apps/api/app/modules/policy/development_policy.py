"""Synthetic development policy only; it is not official TikTok policy."""

DEVELOPMENT_POLICY_RULES: dict[str, dict[str, str]] = {
    "violence": {
        "rule_id": "DEV-TT-VIOLENCE-001",
        "reason": "Development rule for violent acts without graphic detail.",
    },
    "graphic_violence": {
        "rule_id": "DEV-TT-GRAPHIC-VIOLENCE-001",
        "reason": "Development rule for graphic or disturbing violent detail.",
    },
    "drugs": {
        "rule_id": "DEV-TT-DRUGS-001",
        "reason": "Development rule for drug-related content.",
    },
    "weapons": {
        "rule_id": "DEV-TT-WEAPONS-001",
        "reason": "Development rule for weapon-related content.",
    },
    "sexual_content": {
        "rule_id": "DEV-TT-SEXUAL-CONTENT-001",
        "reason": "Development rule for sexual content.",
    },
    "self_harm": {
        "rule_id": "DEV-TT-SELF-HARM-001",
        "reason": "Development rule for self-harm content.",
    },
    "hate": {
        "rule_id": "DEV-TT-HATE-001",
        "reason": "Development rule for hateful content.",
    },
    "crime": {
        "rule_id": "DEV-TT-CRIME-001",
        "reason": "Development rule for crime-related content.",
    },
    "unknown": {
        "rule_id": "DEV-TT-UNKNOWN",
        "reason": "No matching synthetic development-policy rule was found.",
    },
}

PRESS_LAW_POLICY_RULES: dict[str, dict[str, str]] = {
    "prohibited_state_content": {
        "rule_id": "PRESS-LAW-ARTICLE-8-STATE-001",
        "reason": "Prohibited state-directed distortion, fabrication, or psychological warfare.",
    },
    "division_and_hate": {
        "rule_id": "PRESS-LAW-ARTICLE-8-DIVISION-001",
        "reason": "Prohibited division, discrimination, or religious hostility.",
    },
    "war_and_history": {
        "rule_id": "PRESS-LAW-ARTICLE-8-WAR-HISTORY-001",
        "reason": "Prohibited incitement to war or historical distortion.",
    },
    "privacy_and_secrets": {
        "rule_id": "PRESS-LAW-ARTICLE-8-PRIVACY-001",
        "reason": "Prohibited disclosure of state, personal, or family secrets.",
    },
    "harmful_and_obscene_content": {
        "rule_id": "PRESS-LAW-ARTICLE-8-HARMFUL-001",
        "reason": "Prohibited violence incitement, obscene lifestyle promotion, or detailed crime/sexual depictions.",
    },
    "false_information_and_defamation": {
        "rule_id": "PRESS-LAW-ARTICLE-8-ACCURACY-001",
        "reason": "Prohibited false, distorted, defamatory, or premature criminal accusations.",
    },
    "child_harm": {
        "rule_id": "PRESS-LAW-ARTICLE-8-CHILDREN-001",
        "reason": "Prohibited content harmful to children's normal development.",
    },
}

DAI_POLICY_RULES: dict[str, dict[str, str]] = {
    "parliament_coverage": {
        "rule_id": "DAI-POLICY-PARLIAMENT-001",
        "reason": "Do not publish information about the National Assembly or its sessions.",
    },
    "editorial_content": {
        "rule_id": "DAI-POLICY-EDITORIAL-001",
        "reason": "Do not publish content identified as editor-edited news.",
    },
    "international_relevance": {
        "rule_id": "DAI-POLICY-INTERNATIONAL-001",
        "reason": "Publish international news only when it directly affects people in Vietnam.",
    },
    "priority_topics": {
        "rule_id": "DAI-POLICY-PRIORITY-001",
        "reason": "Prioritize education and health news.",
    },
}

TIKTOK_COMMUNITY_POLICY_RULES: dict[str, dict[str, str]] = {
    "sexual_exploitation_of_minors": {
        "rule_id": "TIKTOK-CG-MINOR-EXPLOITATION-001",
        "reason": "Prohibited sexual or physical exploitation, grooming, or sexualized content involving minors.",
    },
    "sexual_exploitation_of_adults": {
        "rule_id": "TIKTOK-CG-ADULT-SEXUAL-ABUSE-001",
        "reason": "Prohibited non-consensual sexual activity, image abuse, or sexual extortion.",
    },
    "human_trafficking": {
        "rule_id": "TIKTOK-CG-TRAFFICKING-001",
        "reason": "Prohibited promotion or facilitation of trafficking or unlawful migrant smuggling.",
    },
    "harassment_and_doxxing": {
        "rule_id": "TIKTOK-CG-HARASSMENT-001",
        "reason": "Prohibited harassment, bullying, doxxing, or coordinated abuse.",
    },
    "dangerous_activities": {
        "rule_id": "TIKTOK-CG-DANGEROUS-ACTS-001",
        "reason": "Prohibited dangerous acts or challenges likely to cause serious harm.",
    },
    "misinformation": {
        "rule_id": "TIKTOK-CG-MISINFORMATION-001",
        "reason": "Prohibited harmful misinformation, including public-safety, health, civic, or crisis misinformation.",
    },
    "ai_generated_content": {
        "rule_id": "TIKTOK-CG-AIGC-001",
        "reason": "Prohibited harmful or misleading realistic AI-generated or materially edited content.",
    },
    "intellectual_property": {
        "rule_id": "TIKTOK-CG-IP-001",
        "reason": "Prohibited intellectual-property infringement.",
    },
    "deceptive_behavior": {
        "rule_id": "TIKTOK-CG-DECEPTIVE-BEHAVIOR-001",
        "reason": "Prohibited impersonation, coordinated inauthentic behavior, or artificial engagement.",
    },
    "controlled_goods": {
        "rule_id": "TIKTOK-CG-CONTROLLED-GOODS-001",
        "reason": "Prohibited sale, promotion, access, or unsafe use of controlled goods and services.",
    },
    "scams": {
        "rule_id": "TIKTOK-CG-SCAM-001",
        "reason": "Prohibited fraud, scams, identity theft, or instructions enabling them.",
    },
}

ALLOWED_DEVELOPMENT_POLICY_IDS = frozenset(
    rule["rule_id"]
    for policy in (
        DEVELOPMENT_POLICY_RULES,
        PRESS_LAW_POLICY_RULES,
        DAI_POLICY_RULES,
        TIKTOK_COMMUNITY_POLICY_RULES,
    )
    for rule in policy.values()
)

TIKTOK_DEVELOPMENT_POLICY = """
Synthetic development policy for Evelyn demos only. This is not official TikTok policy.

Use REVIEW for violence, graphic violence, drugs, weapons, sexual content, self-harm,
hate, or crime when an editor should assess context or presentation. Use BLOCK only for
severe synthetic cases that cannot be responsibly revised. Use PASS only when no issue is
found in this development policy. If uncertain or evidence is missing, use REVIEW.

Allowed rule IDs:
DEV-TT-VIOLENCE-001, DEV-TT-GRAPHIC-VIOLENCE-001, DEV-TT-DRUGS-001,
DEV-TT-WEAPONS-001, DEV-TT-SEXUAL-CONTENT-001, DEV-TT-SELF-HARM-001,
DEV-TT-HATE-001, DEV-TT-CRIME-001, DEV-TT-UNKNOWN.
""".strip()

PRESS_LAW_POLICY = """
Vietnam Press Law shared rules — Article 8 prohibited content. Use REVIEW unless evidence
clearly requires BLOCK. Preserve public-interest reporting, documentation, education,
criticism, satire, and art when they do not promote or enable the harmful conduct.

- PRESS-LAW-ARTICLE-8-STATE-001: state-directed distortion, fabrication, or psychological warfare.
- PRESS-LAW-ARTICLE-8-DIVISION-001: division, protected-characteristic discrimination, or religious hostility.
- PRESS-LAW-ARTICLE-8-WAR-HISTORY-001: incitement to war or historical distortion.
- PRESS-LAW-ARTICLE-8-PRIVACY-001: disclosure of state, personal, or family secrets.
- PRESS-LAW-ARTICLE-8-HARMFUL-001: violence incitement, obscene lifestyle promotion, or detailed crime/sexual depictions.
- PRESS-LAW-ARTICLE-8-ACCURACY-001: false, distorted, defamatory, or premature criminal accusations.
- PRESS-LAW-ARTICLE-8-CHILDREN-001: content harmful to children's normal development.
""".strip()

DAI_POLICY = """
Đài shared editorial rules. Apply these rules alongside Vietnam Press Law and TikTok Community
Guidelines. Use REVIEW when applicability or factual relevance is unclear; use BLOCK when the
content clearly violates a publication prohibition. Priority rules guide ranking, not blocking.

- DAI-POLICY-PARLIAMENT-001: do not publish National Assembly information or session coverage.
- DAI-POLICY-EDITORIAL-001: do not publish content identified as editor-edited news.
- DAI-POLICY-INTERNATIONAL-001: publish international news only when it directly affects people in Vietnam.
- DAI-POLICY-PRIORITY-001: prioritize education and health news.
""".strip()

TIKTOK_COMMUNITY_POLICY = """
TikTok Community Guidelines shared rules. For news, distinguish reporting, documentation,
education, criticism, satire, and art from promotion, facilitation, or harmful depiction.
Use REVIEW when context, presentation, factual basis, consent, or public-interest framing is
unclear; use BLOCK only for severe content that cannot be responsibly revised.

- TIKTOK-CG-MINOR-EXPLOITATION-001: sexual/physical exploitation, grooming, or sexualized minor content.
- TIKTOK-CG-ADULT-SEXUAL-ABUSE-001: non-consensual sexual activity, image abuse, or sexual extortion.
- TIKTOK-CG-TRAFFICKING-001: promotion/facilitation of trafficking or unlawful migrant smuggling.
- TIKTOK-CG-HARASSMENT-001: harassment, bullying, doxxing, or coordinated abuse.
- TIKTOK-CG-DANGEROUS-ACTS-001: dangerous acts/challenges likely to cause serious harm.
- TIKTOK-CG-MISINFORMATION-001: harmful public-safety, health, civic, or crisis misinformation.
- TIKTOK-CG-AIGC-001: harmful or misleading realistic AI-generated/materially edited content.
- TIKTOK-CG-IP-001: intellectual-property infringement.
- TIKTOK-CG-DECEPTIVE-BEHAVIOR-001: impersonation, coordinated inauthentic behavior, or artificial engagement.
- TIKTOK-CG-CONTROLLED-GOODS-001: controlled goods/services sale, promotion, access, or unsafe use.
- TIKTOK-CG-SCAM-001: fraud, scams, identity theft, or instructions enabling them.
""".strip()

SHARED_MODERATION_POLICY = "\n\n".join(
    (TIKTOK_DEVELOPMENT_POLICY, PRESS_LAW_POLICY, DAI_POLICY, TIKTOK_COMMUNITY_POLICY)
)
