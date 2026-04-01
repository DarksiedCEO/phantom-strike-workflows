from __future__ import annotations

import logging

from temporalio import activity

from models.signal import EvidenceAssessment, EvidenceCheckContext

logger = logging.getLogger(__name__)


@activity.defn
async def supporting_evidence_activity(context: EvidenceCheckContext) -> EvidenceAssessment:
    logger.info(
        "supporting evidence activity invoked",
        extra={
            "signal_id": context.signal.signal_id,
            "trace_id": context.trace_id,
            "correlation_id": context.correlation_id,
            "activity_name": context.activity_name,
        },
    )
    return EvidenceAssessment(
        evidence_count=2,
        score_delta=0.22,
        summary="Stubbed supporting evidence indicates corroboration across multiple sources.",
        trace_id=context.trace_id,
        correlation_id=context.correlation_id,
    )


@activity.defn
async def contradicting_evidence_activity(context: EvidenceCheckContext) -> EvidenceAssessment:
    logger.info(
        "contradicting evidence activity invoked",
        extra={
            "signal_id": context.signal.signal_id,
            "trace_id": context.trace_id,
            "correlation_id": context.correlation_id,
            "activity_name": context.activity_name,
        },
    )
    return EvidenceAssessment(
        evidence_count=1,
        score_delta=0.08,
        summary="Stubbed contradicting evidence indicates one unresolved discrepancy.",
        trace_id=context.trace_id,
        correlation_id=context.correlation_id,
    )
