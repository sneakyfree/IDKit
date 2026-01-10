#!/usr/bin/env python3
"""Entry point for Voice GPU Worker."""

import asyncio
import logging
import sys

from worker.voice import VoiceWorker
from worker.base import WorkerConfig


def main():
    """Main entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    config = WorkerConfig(worker_type="voice")
    worker = VoiceWorker(config)

    try:
        asyncio.run(worker.start())
    except KeyboardInterrupt:
        asyncio.run(worker.stop())
        sys.exit(0)


if __name__ == "__main__":
    main()
