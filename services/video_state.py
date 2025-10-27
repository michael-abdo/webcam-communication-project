"""Shared in-memory state for legacy video/test session correlation."""

from __future__ import annotations

# Map video_session_id -> metadata
video_sessions: dict[str, dict] = {}

# Map test_session_id -> video_session_id
test_video_links: dict[str, str] = {}
