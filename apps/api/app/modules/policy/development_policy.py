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

ALLOWED_DEVELOPMENT_POLICY_IDS = frozenset(
    rule["rule_id"] for rule in DEVELOPMENT_POLICY_RULES.values()
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
