from fastapi import APIRouter, HTTPException, status

from app.modules.policy.company_policy import (
    CompanyPolicy,
    CompanyPolicyCatalog,
    CompanyPolicyCreate,
    CompanyPolicyStore,
)

router = APIRouter(prefix="/policies", tags=["company policies"])
policy_store = CompanyPolicyStore()


@router.get("", response_model=CompanyPolicyCatalog)
async def list_company_policies() -> CompanyPolicyCatalog:
    return policy_store.catalog()


@router.post("", response_model=CompanyPolicy, status_code=status.HTTP_201_CREATED)
async def create_company_policy(policy: CompanyPolicyCreate) -> CompanyPolicy:
    return policy_store.create(policy)


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company_policy(policy_id: str) -> None:
    if not policy_store.delete(policy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company policy was not found.")
