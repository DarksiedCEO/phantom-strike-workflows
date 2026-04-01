from __future__ import annotations

import asyncio

from config.settings import get_settings
from worker import create_worker


async def _run() -> None:
    settings = get_settings()
    print(
        {
            "stage": "worker_startup",
            "core_base_url": settings.core_base_url,
            "task_queue": settings.temporal_task_queue,
        }
    )
    worker = await create_worker(settings)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(_run())
