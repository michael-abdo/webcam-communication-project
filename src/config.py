"""Application configuration helpers."""

from __future__ import annotations

import os
from functools import lru_cache


@lru_cache(maxsize=1)
def get_database_url() -> str:
    """Return the database URL, defaulting to a local SQLite file for dev."""
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        if env_url.startswith("postgres://"):
            env_url = env_url.replace("postgres://", "postgresql+psycopg2://", 1)
        return env_url

    # Fallback to SQLite stored under the project data directory
    project_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))  # Go up to project root
    data_dir = os.path.join(project_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    sqlite_path = os.path.join(data_dir, "app.db")
    return f"sqlite:///{sqlite_path}"


# Removed get_capture_api_token - legacy Phase-1 function


@lru_cache(maxsize=1)
def get_metrics_enabled() -> bool:
    return os.getenv('METRICS_ENABLED', 'false').lower() in {'1', 'true', 'yes'}


@lru_cache(maxsize=1)
def get_metrics_host() -> str:
    return os.getenv('METRICS_STATSD_HOST', 'localhost')


@lru_cache(maxsize=1)
def get_metrics_port() -> int:
    try:
        return int(os.getenv('METRICS_STATSD_PORT', '8125'))
    except ValueError:
        return 8125


@lru_cache(maxsize=1)
def get_metrics_prefix() -> str:
    return os.getenv('METRICS_PREFIX', 'webcam')
