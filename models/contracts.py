"""
Pinned contracts metadata for PhantomStrike workflows.

This repo is aligned to phantom-strike-contracts and must not drift from that
source of truth without an explicit contracts update.
"""

from pydantic import BaseModel, ConfigDict


class ContractsMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repository: str
    commit: str
    schema_version: str


CONTRACTS_METADATA = ContractsMetadata(
    repository="phantom-strike-contracts",
    commit="3110d87",
    schema_version="v1",
)
