from __future__ import annotations

import asyncio
from dataclasses import dataclass

import pytest
from pydantic import ValidationError

from activities.core_updates import submit_signal_decision_activity
from models.decision import CoreSignalDecisionPayload, SignalDecision
from models.signal import EvidenceAssessment, SignalValidationInput


def build_signal_validation_input_payload(
    *,
    trace_id: str = "trace-regression-001",
    correlation_id: str = "e5b11411-2732-486f-9d0a-f4144ea20395",
) -> dict:
    return {
        "signal": {
            "signal_id": "df1eab71-aa5f-4ce2-9915-64ccf314e3b9",
            "title": "Suspicious campaign signal",
            "summary": "Cross-source activity suggests coordinated malicious behavior.",
            "category": "campaign",
            "status": "triaged",
            "severity": "high",
            "observed_at": "2026-04-01T07:20:00Z",
            "created_at": "2026-04-01T07:20:00Z",
            "updated_at": "2026-04-01T07:20:00Z",
            "tags": ["regression"],
            "scores": [
                {
                    "score": 0.62,
                    "confidence_band": "guarded",
                    "rationale": "Initial triage score",
                    "generated_at": "2026-04-01T07:20:00Z",
                }
            ],
            "related_source_ids": ["source-001"],
            "audit": {
                "schema": {
                    "contractVersion": "v1",
                    "schemaName": "signal",
                    "schemaRevision": 0,
                    "packageVersion": "0.1.0",
                },
                "trace": {
                    "request_id": "0b315677-0912-4f5a-a25e-24d33c841d88",
                    "trace_id": trace_id,
                    "correlation_id": correlation_id,
                    "actor_service": "workflows",
                    "environment": "local",
                },
                "recorded_at": "2026-04-01T07:20:00Z",
                "tags": ["regression"],
            },
        },
        "baseline_confidence": 0.62,
        "trace_id": trace_id,
        "correlation_id": correlation_id,
    }


def build_signal_decision() -> SignalDecision:
    input_data = SignalValidationInput.model_validate(
        build_signal_validation_input_payload(
            trace_id="trace-regression-002",
            correlation_id="f5b11411-2732-486f-9d0a-f4144ea20395",
        )
    )
    return SignalDecision(
        signal=input_data.signal,
        baseline_confidence=input_data.baseline_confidence,
        supporting_evidence=EvidenceAssessment(
            evidence_count=2,
            score_delta=0.22,
            summary="Stubbed supporting evidence indicates corroboration across multiple sources.",
            trace_id=input_data.trace_id,
            correlation_id=input_data.correlation_id,
        ),
        contradicting_evidence=EvidenceAssessment(
            evidence_count=1,
            score_delta=0.08,
            summary="Stubbed contradicting evidence indicates one unresolved discrepancy.",
            trace_id=input_data.trace_id,
            correlation_id=input_data.correlation_id,
        ),
        confidence_delta=0.14,
        updated_confidence=0.76,
        confidence_band="elevated",
        disposition="escalate",
        reasoning="Disposition=escalate; supporting_count=2; contradicting_count=1; updated_confidence=0.7600",
        trace_id=input_data.trace_id,
        correlation_id=input_data.correlation_id,
    )


def test_signal_workflow_input_accepts_runtime_schema_only() -> None:
    payload = build_signal_validation_input_payload()

    obj = SignalValidationInput.model_validate(payload)
    dumped = obj.model_dump(mode="json")

    assert dumped["signal"]["audit"]["schema"] == {
        "contractVersion": "v1",
        "schemaName": "signal",
        "schemaRevision": 0,
        "packageVersion": "0.1.0",
    }
    assert "schema_" not in dumped["signal"]["audit"]


def test_signal_workflow_input_rejects_schema_alias_field() -> None:
    payload = build_signal_validation_input_payload()
    payload["signal"]["audit"]["schema_"] = payload["signal"]["audit"].pop("schema")

    with pytest.raises(ValidationError):
        SignalValidationInput.model_validate(payload)


def test_core_signal_decision_payload_is_flat_and_contract_exact() -> None:
    payload = CoreSignalDecisionPayload.from_signal_decision(build_signal_decision()).model_dump(
        mode="json"
    )

    assert set(payload.keys()) == {
        "signal_id",
        "baseline_confidence",
        "confidence_delta",
        "updated_confidence",
        "confidence_band",
        "disposition",
        "reasoning",
        "trace_id",
        "correlation_id",
    }
    assert "signal" not in payload
    assert "supporting_evidence" not in payload
    assert "contradicting_evidence" not in payload


def test_submit_signal_decision_activity_builds_flat_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    decision = build_signal_decision()
    captured: dict[str, object] = {}

    @dataclass
    class FakeSettings:
        core_base_url: str = "http://127.0.0.1:3100"

    class FakeCoreClient:
        def __init__(self, base_url: str) -> None:
            captured["base_url"] = base_url

        def decision_endpoint(self, signal_id: str) -> str:
            return f"http://127.0.0.1:3100/v1/signals/{signal_id}/decision"

        async def submit_signal_decision(
            self,
            *,
            signal_id: str,
            payload: dict,
            trace_id: str,
            correlation_id: str,
        ) -> dict:
            captured["signal_id"] = signal_id
            captured["payload"] = payload
            captured["trace_id"] = trace_id
            captured["correlation_id"] = correlation_id
            return {"success": True}

    monkeypatch.setattr("activities.core_updates.Settings", FakeSettings)
    monkeypatch.setattr("activities.core_updates.CoreClient", FakeCoreClient)

    result = asyncio.run(submit_signal_decision_activity(decision))

    assert captured["base_url"] == "http://127.0.0.1:3100"
    assert captured["signal_id"] == "df1eab71-aa5f-4ce2-9915-64ccf314e3b9"
    assert captured["trace_id"] == decision.trace_id
    assert captured["correlation_id"] == decision.correlation_id
    assert set(captured["payload"].keys()) == {
        "signal_id",
        "baseline_confidence",
        "confidence_delta",
        "updated_confidence",
        "confidence_band",
        "disposition",
        "reasoning",
        "trace_id",
        "correlation_id",
    }
    assert "signal" not in captured["payload"]
    assert "supporting_evidence" not in captured["payload"]
    assert result.signal_id == decision.signal.signal_id
