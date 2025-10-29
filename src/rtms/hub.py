"""In-memory broadcast hub for RTMS websocket clients."""

from __future__ import annotations

import json
import logging
import threading
from typing import Any


LOGGER = logging.getLogger(__name__)


class RTMSHub:
    """Thread-safe registry of active websocket connections."""

    def __init__(self) -> None:
        self._connections: dict[Any, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def register(self, ws: Any, metadata: dict[str, Any] | None = None) -> None:
        details = metadata or {}
        with self._lock:
            self._connections[ws] = details

    def unregister(self, ws: Any) -> None:
        with self._lock:
            self._connections.pop(ws, None)

    def connection_count(self) -> int:
        with self._lock:
            return len(self._connections)

    def connected_clients_metadata(self) -> list[dict[str, Any]]:
        with self._lock:
            return [
                {key: value for key, value in details.items() if value is not None}
                for details in self._connections.values()
            ]

    def broadcast(self, message: dict) -> None:
        """Send a JSON serialisable message to all connected clients."""
        payload = json.dumps(message)
        dead: list[Any] = []
        with self._lock:
            for ws in self._connections:
                try:
                    ws.send(payload)
                except Exception as exc:  # pragma: no cover - defensive logging
                    LOGGER.warning("rtms.hub.broadcast_failed", exc_info=exc)
                    dead.append(ws)
            for ws in dead:
                self._connections.pop(ws, None)
