import logging

from fastapi import APIRouter, HTTPException, status

from app.modules.policy.company_policy import (
    CompanyPolicyStore,
    PolicyRule,
    PolicyRuleCreate,
    PolicyRuleList,
    PolicyRuleUpdate,
)

router = APIRouter(prefix="/policies", tags=["policies"])
logger = logging.getLogger(__name__)
policy_store = CompanyPolicyStore()


def _policy_store_error(error: OSError | ValueError) -> HTTPException:
    logger.error("Policy storage failed", exc_info=error)
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Policy storage is temporarily unavailable.",
    )


@router.get("", response_model=PolicyRuleList)
async def list_policies() -> PolicyRuleList:
    try:
        return PolicyRuleList(policies=policy_store.list())
    except (OSError, ValueError) as error:
        raise _policy_store_error(error) from None


@router.post("", response_model=PolicyRule, status_code=status.HTTP_201_CREATED)
async def create_policy(policy: PolicyRuleCreate) -> PolicyRule:
    try:
        return policy_store.create(policy)
    except (OSError, ValueError) as error:
        raise _policy_store_error(error) from None


@router.patch("/{rule_id}", response_model=PolicyRule)
async def update_policy(rule_id: str, update: PolicyRuleUpdate) -> PolicyRule:
    try:
        policy = policy_store.update(rule_id, update)
    except (OSError, ValueError) as error:
        raise _policy_store_error(error) from None
    if policy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy rule was not found.")
    return policy


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(rule_id: str) -> None:
    try:
        if not policy_store.delete(rule_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy rule was not found.")
    except (OSError, ValueError) as error:
        raise _policy_store_error(error) from None
