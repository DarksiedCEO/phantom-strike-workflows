from __future__ import annotations

import asyncio

from config.settings import Settings
from worker import create_worker


async def _run() -> None:
    settings = Settings()
    worker = await create_worker(settings)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(_run())
