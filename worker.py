from __future__ import annotations

from temporalio.worker import Worker

from app.bootstrap import activity_definitions, build_temporal_client, workflow_definitions
from config.settings import Settings
from observability.logging import configure_logging


async def create_worker(settings: Settings | None = None) -> Worker:
    resolved_settings = settings or Settings()
    configure_logging(resolved_settings.log_level)
    client = await build_temporal_client(resolved_settings)

    return Worker(
        client,
        task_queue=resolved_settings.temporal_task_queue,
        workflows=workflow_definitions(),
        activities=activity_definitions(),
    )
