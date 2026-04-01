from __future__ import annotations

import logging

from temporalio import activity

from clients.core_client import CoreClient
from config.settings import Settings
from models.decision import DecisionSubmissionResult, SignalDecision

logger = logging.getLogger(__name__)


@activity.defn
async def submit_signal_decision_activity(decision: SignalDecision) -> DecisionSubmissionResult:
    settings = Settings()
    client = CoreClient(settings.core_base_url)

    logger.info(
        "submitting signal decision to core",
        extra={
            "signal_id": decision.signal.signal_id,
            "trace_id": decision.trace_id,
            "correlation_id": decision.correlation_id,
            "disposition": decision.disposition.value,
        },
    )

    await client.submit_signal_decision(
        signal_id=decision.signal.signal_id,
        payload=decision.model_dump(mode="json"),
        trace_id=decision.trace_id,
        correlation_id=decision.correlation_id,
    )

    return DecisionSubmissionResult(
        signal_id=decision.signal.signal_id,
        submitted=True,
        target_service="phantom-strike-core",
        target_endpoint=client.decision_endpoint(decision.signal.signal_id),
        trace_id=decision.trace_id,
        correlation_id=decision.correlation_id,
    )
