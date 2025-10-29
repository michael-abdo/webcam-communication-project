"""StatsD metrics helper for Phase 1 telemetry."""

from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import logging
from functools import lru_cache
from typing import Optional

try:
    from statsd import StatsClient
except ImportError:  # pragma: no cover
    StatsClient = None  # type: ignore

from src.config import (
    get_metrics_enabled,
    get_metrics_host,
    get_metrics_port,
    get_metrics_prefix,
)

logger = logging.getLogger(__name__)


class Metrics:
    """Thin wrapper around StatsD client that no-ops when disabled."""

    def __init__(self) -> None:
        self._client: Optional[StatsClient] = None
        if get_metrics_enabled():
            if StatsClient is None:
                logger.warning("StatsD client not installed; metrics disabled")
                return
            host = get_metrics_host()
            port = get_metrics_port()
            prefix = get_metrics_prefix()
            try:
                self._client = StatsClient(host=host, port=port, prefix=prefix)
                logger.info(
                    "Metrics client initialised",
                    extra={"host": host, "port": port, "prefix": prefix},
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to initialise StatsD client: %s", exc)
                self._client = None

    @property
    def enabled(self) -> bool:
        return self._client is not None

    def incr(self, name: str, count: int = 1, rate: float = 1.0) -> None:
        if not self._client:
            return
        try:
            self._client.incr(name, count=count, rate=rate)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Metrics incr failed for %s: %s", name, exc)

    def timing(self, name: str, value: float, rate: float = 1.0) -> None:
        if not self._client:
            return
        try:
            self._client.timing(name, value, rate=rate)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Metrics timing failed for %s: %s", name, exc)


@lru_cache(maxsize=1)
def metrics() -> Metrics:
    return Metrics()
