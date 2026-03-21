import asyncio
import logging

from worker.db import async_session
from worker.queue_consumer import QueueConsumer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


async def main():
    consumer = QueueConsumer(session_factory=async_session)
    await consumer.run()


if __name__ == "__main__":
    asyncio.run(main())
