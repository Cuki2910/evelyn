import logging

from fastapi import APIRouter, HTTPException, status

from app.modules.policy.company_policy import (
    CompanyPolicy,
    CompanyPolicyCatalog,
    CompanyPolicyCreate,
    CompanyPolicyStore,
)

router = APIRouter(prefix="/policies", tags=["company policies"])
logger = logging.getLogger(__name__)
policy_store = CompanyPolicyStore()


def _policy_store_error(error: OSError | ValueError) -> HTTPException:
    logger.error("Company policy storage failed", exc_info=error)
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Company policy storage is temporarily unavailable.",
    )


@router.get("", response_model=CompanyPolicyCatalog)
async def list_company_policies() -> CompanyPolicyCatalog:
    try:
        return policy_store.catalog()
    except (OSError, ValueError) as error:
        raise _policy_store_error(error) from None


@router.post("", response_model=CompanyPolicy, status_code=status.HTTP_201_CREATED)
async def create_company_policy(policy: CompanyPolicyCreate) -> CompanyPolicy:
    try:
        return policy_store.create(policy)
    except (OSError, ValueError) as error:
        raise _policy_store_error(error) from None


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company_policy(policy_id: str) -> None:
    try:
        if not policy_store.delete(policy_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company policy was not found.")
    except (OSError, ValueError) as error:
        raise _policy_store_error(error) from None
