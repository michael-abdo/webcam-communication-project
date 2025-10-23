"""In-memory broadcast hub for RTMS websocket clients."""

from __future__ import annotations

import json
import threading
from typing import Any


class RTMSHub:
    """Thread-safe registry of active websocket connections."""

    def __init__(self) -> None:
        self._connections: set[Any] = set()
        self._lock = threading.Lock()

    def register(self, ws: Any) -> None:
        with self._lock:
            self._connections.add(ws)

    def unregister(self, ws: Any) -> None:
        with self._lock:
            self._connections.discard(ws)

    def broadcast(self, message: dict) -> None:
        """Send a JSON serialisable message to all connected clients."""
        payload = json.dumps(message)
        dead: list[Any] = []
        with self._lock:
            for ws in self._connections:
                try:
                    ws.send(payload)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self._connections.discard(ws)
