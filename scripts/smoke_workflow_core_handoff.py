from __future__ import annotations

import asyncio
import json
import sys
import uuid
from copy import deepcopy
from datetime import timedelta
from pathlib import Path

import httpx
from temporalio.client import Client

from config.settings import get_settings
from models.decision import SignalDecision
from models.signal import SignalValidationInput
from workflows.signal_validation import SignalValidationWorkflow

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "smoke_signal_input.json"


def fail(message: str, **details: object) -> None:
    print(f"SMOKE FAIL: {message}")
    if details:
        print(json.dumps(details, indent=2, sort_keys=True, default=str))
    raise SystemExit(1)


def load_fixture() -> dict:
    try:
        return json.loads(FIXTURE_PATH.read_text())
    except FileNotFoundError as exc:
        fail("fixture file missing", fixture_path=str(FIXTURE_PATH), error=str(exc))
    except json.JSONDecodeError as exc:
        fail("fixture file is invalid json", fixture_path=str(FIXTURE_PATH), error=str(exc))


def build_smoke_input() -> SignalValidationInput:
    fixture = deepcopy(load_fixture())
    run_suffix = uuid.uuid4().hex[:8]
    signal_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"phantom-strike-smoke-signal-{run_suffix}"))
    correlation_id = str(uuid.uuid4())
    trace_id = f"trace-smoke-{run_suffix}"
    request_id = str(uuid.uuid4())

    fixture["signal"]["signal_id"] = signal_id
    fixture["signal"]["audit"]["trace"]["request_id"] = request_id
    fixture["signal"]["audit"]["trace"]["trace_id"] = trace_id
    fixture["signal"]["audit"]["trace"]["correlation_id"] = correlation_id
    fixture["trace_id"] = trace_id
    fixture["correlation_id"] = correlation_id

    try:
        return SignalValidationInput.model_validate(fixture)
    except Exception as exc:  # pragma: no cover - smoke harness failure path
        fail("workflow input validation failed", error=str(exc))


async def verify_core_health(core_base_url: str) -> None:
    try:
        async with httpx.AsyncClient(base_url=core_base_url, timeout=10.0) as client:
            response = await client.get("/health")
            response.raise_for_status()
    except Exception as exc:  # pragma: no cover - smoke harness failure path
        fail("core health check failed", core_base_url=core_base_url, error=str(exc))


async def main() -> None:
    settings = get_settings()
    payload = build_smoke_input()

    print(
        json.dumps(
            {
                "stage": "smoke_start",
                "core_base_url": settings.core_base_url,
                "temporal_server_url": settings.temporal_server_url,
                "temporal_namespace": settings.temporal_namespace,
                "task_queue": settings.temporal_task_queue,
                "signal_id": payload.signal.signal_id,
                "trace_id": payload.trace_id,
                "correlation_id": payload.correlation_id,
            },
            indent=2,
            sort_keys=True,
        )
    )

    await verify_core_health(settings.core_base_url)

    try:
        client = await Client.connect(
            settings.temporal_server_url,
            namespace=settings.temporal_namespace,
        )
    except Exception as exc:  # pragma: no cover - smoke harness failure path
        fail(
            "unable to connect to Temporal",
            temporal_server_url=settings.temporal_server_url,
            temporal_namespace=settings.temporal_namespace,
            error=str(exc),
        )

    workflow_id = f"smoke-{payload.signal.signal_id}-{payload.correlation_id}"

    try:
        result = await asyncio.wait_for(
            client.execute_workflow(
                SignalValidationWorkflow.run,
                payload,
                id=workflow_id,
                task_queue=settings.temporal_task_queue,
                execution_timeout=timedelta(seconds=settings.smoke_timeout_seconds),
            ),
            timeout=settings.smoke_timeout_seconds,
        )
    except asyncio.TimeoutError:  # pragma: no cover - smoke harness failure path
        fail("workflow execution timed out", workflow_id=workflow_id)
    except Exception as exc:  # pragma: no cover - smoke harness failure path
        fail("workflow execution failed", workflow_id=workflow_id, error=str(exc))

    try:
        validated_result = SignalDecision.model_validate(result.model_dump(mode="json"))
    except Exception as exc:  # pragma: no cover - smoke harness failure path
        fail("workflow returned an invalid result shape", workflow_id=workflow_id, error=str(exc))

    if validated_result.trace_id != payload.trace_id:
        fail(
            "trace_id mismatch",
            expected=payload.trace_id,
            actual=validated_result.trace_id,
        )
    if validated_result.correlation_id != payload.correlation_id:
        fail(
            "correlation_id mismatch",
            expected=payload.correlation_id,
            actual=validated_result.correlation_id,
        )
    if validated_result.signal.signal_id != payload.signal.signal_id:
        fail(
            "signal_id mismatch",
            expected=payload.signal.signal_id,
            actual=validated_result.signal.signal_id,
        )

    print(
        json.dumps(
            {
                "stage": "smoke_pass",
                "workflow_id": workflow_id,
                "signal_id": validated_result.signal.signal_id,
                "trace_id": validated_result.trace_id,
                "correlation_id": validated_result.correlation_id,
                "disposition": validated_result.disposition.value,
                "confidence_band": validated_result.confidence_band.value,
                "core_acceptance_inferred_from_workflow_completion": True,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:  # pragma: no cover - smoke harness failure path
        sys.exit(130)
