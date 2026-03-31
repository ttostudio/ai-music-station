"""バックグラウンド生成ワーカー — FastAPI lifespan から起動する。

API プロセスと同一プロセスで非同期タスクとしてキューコンシューマーを起動する。
"""
from __future__ import annotations

import asyncio
import contextlib
import logging

logger = logging.getLogger(__name__)

_worker_task: asyncio.Task | None = None


async def start_worker() -> None:
    """生成ワーカーをバックグラウンドタスクとして起動する。"""
    global _worker_task
    from worker.db import async_session
    from worker.queue_consumer import QueueConsumer

    consumer = QueueConsumer(session_factory=async_session)
    _worker_task = asyncio.create_task(consumer.run(), name="generation-worker")
    logger.info("Generation worker started (task: %s)", _worker_task.get_name())


async def stop_worker() -> None:
    """生成ワーカーを停止する。"""
    global _worker_task
    if _worker_task and not _worker_task.done():
        _worker_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await _worker_task
    logger.info("Generation worker stopped")
