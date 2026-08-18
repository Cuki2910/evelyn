from collections.abc import Sequence

from app.modules.moderation.schemas import Decision, PolicyResult


class DecisionEngine:
    @staticmethod
    def decide(policy_results: Sequence[PolicyResult]) -> Decision:
        # An empty evaluation has no evidence for a safe publish decision.
        if not policy_results:
            return Decision.REVIEW
        decisions = {result.decision for result in policy_results}
        if Decision.BLOCK in decisions:
            return Decision.BLOCK
        if Decision.REVIEW in decisions:
            return Decision.REVIEW
        return Decision.PASS
