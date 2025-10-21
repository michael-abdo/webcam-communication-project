"""Application configuration helpers."""

from __future__ import annotations

import os
from functools import lru_cache


@lru_cache(maxsize=1)
def get_database_url() -> str:
    """Return the database URL, defaulting to a local SQLite file for dev."""
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url

    # Fallback to SQLite stored under the project data directory
    project_dir = os.path.abspath(os.path.dirname(__file__))
    data_dir = os.path.join(project_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    sqlite_path = os.path.join(data_dir, "app.db")
    return f"sqlite:///{sqlite_path}"
