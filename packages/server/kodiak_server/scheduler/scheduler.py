"""Basic scheduler for Kodiak Server.

Runs strategy evaluation cycles on a configurable interval.
This replaces the cron-based scheduling from the CLI package
with an in-process scheduler managed by the server.

TODO: Add support for:
- Trigger-based scheduling (price alerts, volume spikes)
- Memory/state persistence across restarts
- Automated decision-making hooks
"""

from __future__ import annotations

import asyncio
import logging

logger = logging.getLogger("kodiak.scheduler")


class Scheduler:
    """Simple asyncio-based scheduler for periodic strategy evaluation."""

    def __init__(self, interval_seconds: int = 60, dry_run: bool = False):
        self.interval = interval_seconds
        self.dry_run = dry_run
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the scheduler loop."""
        if self._running:
            logger.warning("Scheduler already running")
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("Scheduler started (interval=%ds, dry_run=%s)", self.interval, self.dry_run)

    async def stop(self) -> None:
        """Stop the scheduler loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Scheduler stopped")

    async def _loop(self) -> None:
        """Main scheduler loop."""
        while self._running:
            try:
                await self._tick()
            except Exception:
                logger.exception("Scheduler tick failed")
            await asyncio.sleep(self.interval)

    async def _tick(self) -> None:
        """Single scheduler tick — evaluate strategies.

        TODO: This is a stub. Wire up to kodiak.core.engine.TradingEngine.run_once()
        when the server-managed engine is implemented.
        """
        logger.debug("Scheduler tick (stub — not yet wired to engine)")

    @property
    def is_running(self) -> bool:
        return self._running
