import re
from collections.abc import Sequence

from app.modules.moderation.schemas import RiskLevel, Violation


class MockRiskClassifier:
    """Deterministic development mock; not production moderation logic."""

    _RULES: dict[str, tuple[RiskLevel, str, tuple[str, ...]]] = {
        "violence": (
            RiskLevel.MEDIUM,
            "Nội dung có mô tả hành vi bạo lực cần được kiểm tra thêm.",
            ("giết", "đâm", "chém", "đánh", "thi thể", "tử vong", "máu"),
        ),
        "drugs": (
            RiskLevel.MEDIUM,
            "Nội dung có yếu tố ma túy cần được kiểm tra thêm.",
            ("ma túy", "heroin", "cocaine", "cần sa", "methamphetamine"),
        ),
        "weapons": (
            RiskLevel.MEDIUM,
            "Nội dung có đề cập vũ khí cần được kiểm tra thêm.",
            ("súng", "dao", "vũ khí"),
        ),
        "sexual_content": (
            RiskLevel.HIGH,
            "Nội dung có yếu tố tình dục cần được kiểm tra thêm.",
            ("khiêu dâm", "tình dục", "khỏa thân"),
        ),
        "self_harm": (
            RiskLevel.HIGH,
            "Nội dung có yếu tố tự hại cần được kiểm tra thêm.",
            ("tự sát", "tự tử"),
        ),
        "hate": (
            RiskLevel.HIGH,
            "Nội dung có yếu tố thù ghét cần được kiểm tra thêm.",
            ("thù ghét", "kỳ thị", "phân biệt chủng tộc"),
        ),
        "crime": (
            RiskLevel.MEDIUM,
            "Nội dung có yếu tố tội phạm cần được kiểm tra thêm.",
            ("trộm cắp", "cướp", "lừa đảo"),
        ),
        "sensitive": (
            RiskLevel.MEDIUM,
            "Nội dung có yếu tố nhạy cảm cần được kiểm tra thêm.",
            ("bí mật nhà nước", "thông tin mật"),
        ),
    }

    def classify(self, text: str) -> Sequence[Violation]:
        normalized = text.casefold()
        violations: list[Violation] = []

        for category, (severity, reason, keywords) in self._RULES.items():
            for keyword in keywords:
                suffix = r"(?!\w|\s+động)" if keyword == "dao" else r"(?!\w)"
                match = re.search(
                    rf"(?<!\w){re.escape(keyword.casefold())}{suffix}", normalized
                )
                if match:
                    violations.append(
                        Violation(
                            text=text[match.start() : match.end()],
                            category=category,
                            severity=severity,
                            reason=reason,
                        )
                    )
                    break

        return violations
