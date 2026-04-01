from __future__ import annotations

"""
IMPORTANT:
These models MUST remain aligned with phantom-strike-contracts SignalSchema.
Do not modify field names or structure without updating contracts.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ActorService(str, Enum):
    CONTRACTS = "contracts"
    CORE = "core"
    WORKFLOWS = "workflows"
    INTEL = "intel"
    CONSOLE = "console"


class EnvironmentName(str, Enum):
    LOCAL = "local"
    DEV = "dev"
    STAGING = "staging"
    PRODUCTION = "production"


class SignalCategory(str, Enum):
    ANOMALY = "anomaly"
    CAMPAIGN = "campaign"
    ENTITY = "entity"
    THREAT = "threat"
    LEAD = "lead"


class SignalStatus(str, Enum):
    DRAFT = "draft"
    TRIAGED = "triaged"
    VALIDATED = "validated"
    ESCALATED = "escalated"
    SUPPRESSED = "suppressed"
    RESOLVED = "resolved"


class SignalSeverity(str, Enum):
    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ContractSchemaDescriptor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contractVersion: str = Field(pattern=r"^v1$")
    schemaName: str
    schemaRevision: int
    packageVersion: str = Field(pattern=r"^\d+\.\d+\.\d+(-[\w.-]+)?$")


class ContractTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    trace_id: str
    correlation_id: str
    actor_service: ActorService
    environment: EnvironmentName


class ContractAudit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema: ContractSchemaDescriptor
    trace: ContractTrace
    recorded_at: datetime
    tags: list[str] = Field(default_factory=list)


class SignalScore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: float
    confidence_band: str
    rationale: str
    generated_at: datetime


class SignalPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    signal_id: str
    title: str
    summary: str
    category: SignalCategory
    status: SignalStatus
    severity: SignalSeverity
    observed_at: datetime
    created_at: datetime
    updated_at: datetime
    tags: list[str] = Field(default_factory=list)
    scores: list[SignalScore]
    related_source_ids: list[str] = Field(default_factory=list)
    audit: ContractAudit


class EvidenceCheckContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    signal: SignalPayload
    activity_name: str
    trace_id: str
    correlation_id: str


class EvidenceAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_count: int
    score_delta: float
    summary: str
    trace_id: str
    correlation_id: str


class SignalValidationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    signal: SignalPayload
    baseline_confidence: float
    trace_id: str
    correlation_id: str

    def activity_context(self, activity_name: str) -> EvidenceCheckContext:
        return EvidenceCheckContext(
            signal=self.signal,
            activity_name=activity_name,
            trace_id=self.trace_id,
            correlation_id=self.correlation_id,
        )
