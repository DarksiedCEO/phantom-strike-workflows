from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict

from models.signal import EvidenceAssessment, SignalPayload


class ValidationDisposition(str, Enum):
    PROMOTE = "promote"
    HOLD = "hold"
    SUPPRESS = "suppress"
    ESCALATE = "escalate"


class ConfidenceBand(str, Enum):
    LOW = "low"
    GUARDED = "guarded"
    ELEVATED = "elevated"
    CONFIRMED = "confirmed"


class SignalDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    signal: SignalPayload
    baseline_confidence: float
    supporting_evidence: EvidenceAssessment
    contradicting_evidence: EvidenceAssessment
    confidence_delta: float
    updated_confidence: float
    confidence_band: ConfidenceBand
    disposition: ValidationDisposition
    reasoning: str
    trace_id: str
    correlation_id: str


class CoreSignalDecisionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    signal_id: str
    baseline_confidence: float
    confidence_delta: float
    updated_confidence: float
    confidence_band: ConfidenceBand
    disposition: ValidationDisposition
    reasoning: str
    trace_id: str
    correlation_id: str

    @classmethod
    def from_signal_decision(cls, decision: SignalDecision) -> "CoreSignalDecisionPayload":
        return cls(
            signal_id=decision.signal.signal_id,
            baseline_confidence=decision.baseline_confidence,
            confidence_delta=decision.confidence_delta,
            updated_confidence=decision.updated_confidence,
            confidence_band=decision.confidence_band,
            disposition=decision.disposition,
            reasoning=decision.reasoning,
            trace_id=decision.trace_id,
            correlation_id=decision.correlation_id,
        )


class DecisionSubmissionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    signal_id: str
    submitted: bool
    target_service: str
    target_endpoint: str
    trace_id: str
    correlation_id: str
