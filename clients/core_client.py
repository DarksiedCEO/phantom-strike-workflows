from __future__ import annotations

from typing import Any

import httpx


class CoreClient:
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    def decision_endpoint(self, signal_id: str) -> str:
        return f"{self._base_url}/v1/signals/{signal_id}/decision"

    async def get_health(self) -> dict[str, Any]:
        async with httpx.AsyncClient(base_url=self._base_url, timeout=10.0) as client:
            response = await client.get("/health")
            response.raise_for_status()
            return response.json()

    async def submit_signal_update(
        self,
        payload: dict[str, Any],
        trace_id: str,
        correlation_id: str,
    ) -> dict[str, Any]:
        headers = {
            "x-trace-id": trace_id,
            "x-correlation-id": correlation_id,
        }
        async with httpx.AsyncClient(base_url=self._base_url, timeout=10.0) as client:
            response = await client.post("/v1/signals", json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

    async def submit_signal_decision(
        self,
        signal_id: str,
        payload: dict[str, Any],
        trace_id: str,
        correlation_id: str,
    ) -> dict[str, Any]:
        headers = {
            "x-trace-id": trace_id,
            "x-correlation-id": correlation_id,
        }
        async with httpx.AsyncClient(base_url=self._base_url, timeout=10.0) as client:
            response = await client.post(
                f"/v1/signals/{signal_id}/decision",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
