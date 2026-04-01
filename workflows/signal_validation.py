from __future__ import annotations

from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from activities.core_updates import submit_signal_decision_activity
    from activities.evidence import contradicting_evidence_activity, supporting_evidence_activity
    from models.decision import ConfidenceBand, SignalDecision, ValidationDisposition
    from models.signal import EvidenceAssessment, SignalValidationInput


@workflow.defn(name="signal-validation")
class SignalValidationWorkflow:
    @workflow.run
    async def run(self, input_data: SignalValidationInput) -> SignalDecision:
        workflow.logger.info(
            "signal validation workflow started",
            extra={
                "signal_id": input_data.signal.signal_id,
                "trace_id": input_data.trace_id,
                "correlation_id": input_data.correlation_id,
            },
        )

        supporting = await workflow.execute_activity(
            supporting_evidence_activity,
            input_data.activity_context("supporting_evidence"),
            schedule_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(initial_interval=timedelta(seconds=1), maximum_attempts=3),
        )
        contradicting = await workflow.execute_activity(
            contradicting_evidence_activity,
            input_data.activity_context("contradicting_evidence"),
            schedule_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(initial_interval=timedelta(seconds=1), maximum_attempts=3),
        )

        confidence_delta = self._compute_confidence_delta(supporting, contradicting)
        updated_score = self._clamp(input_data.baseline_confidence + confidence_delta)
        disposition = self._determine_disposition(updated_score, supporting, contradicting)
        confidence_band = self._confidence_band(updated_score)
        decision = SignalDecision(
            signal=input_data.signal,
            baseline_confidence=input_data.baseline_confidence,
            supporting_evidence=supporting,
            contradicting_evidence=contradicting,
            confidence_delta=confidence_delta,
            updated_confidence=updated_score,
            confidence_band=confidence_band,
            disposition=disposition,
            reasoning=self._reasoning(disposition, supporting, contradicting, updated_score),
            trace_id=input_data.trace_id,
            correlation_id=input_data.correlation_id,
        )

        await workflow.execute_activity(
            submit_signal_decision_activity,
            decision,
            schedule_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(initial_interval=timedelta(seconds=1), maximum_attempts=3),
        )

        workflow.logger.info(
            "signal validation workflow completed",
            extra={
                "signal_id": input_data.signal.signal_id,
                "trace_id": input_data.trace_id,
                "correlation_id": input_data.correlation_id,
                "updated_confidence_score": updated_score,
                "disposition": disposition.value,
                "confidence_band": confidence_band.value,
            },
        )

        return decision

    def _compute_confidence_delta(
        self,
        supporting: EvidenceAssessment,
        contradicting: EvidenceAssessment,
    ) -> float:
        delta = supporting.score_delta - contradicting.score_delta
        return round(delta, 4)

    def _determine_disposition(
        self,
        updated_score: float,
        supporting: EvidenceAssessment,
        contradicting: EvidenceAssessment,
    ) -> ValidationDisposition:
        if contradicting.score_delta >= 0.35:
            return ValidationDisposition.SUPPRESS
        if updated_score >= 0.85 and supporting.evidence_count >= 2:
            return ValidationDisposition.PROMOTE
        if updated_score >= 0.65:
            return ValidationDisposition.ESCALATE
        return ValidationDisposition.HOLD

    def _confidence_band(self, score: float) -> ConfidenceBand:
        if score >= 0.85:
            return ConfidenceBand.CONFIRMED
        if score >= 0.65:
            return ConfidenceBand.ELEVATED
        if score >= 0.4:
            return ConfidenceBand.GUARDED
        return ConfidenceBand.LOW

    def _reasoning(
        self,
        disposition: ValidationDisposition,
        supporting: EvidenceAssessment,
        contradicting: EvidenceAssessment,
        updated_score: float,
    ) -> str:
        return (
            f"Disposition={disposition.value}; "
            f"supporting_count={supporting.evidence_count}; "
            f"contradicting_count={contradicting.evidence_count}; "
            f"updated_confidence={updated_score:.4f}"
        )

    def _clamp(self, value: float) -> float:
        return round(max(0.0, min(1.0, value)), 4)
