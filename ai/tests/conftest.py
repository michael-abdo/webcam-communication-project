"""Pytest configuration and fixtures for Xenodex tests."""

import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def temp_data_dir():
    """Create a temporary data directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_celebrity_data():
    """Sample celebrity data for testing."""
    return {
        "celebrities": [
            {
                "name": "Test Celebrity 1",
                "personality": {"f_t": "F", "di_de": "Di"},
                "stories": ["This is a test story about feelings."]
            },
            {
                "name": "Test Celebrity 2", 
                "personality": {"f_t": "T", "di_de": "De"},
                "stories": ["This is a logical analysis."]
            }
        ]
    }


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    return {
        "choices": [{"message": {"content": "F"}}],
        "usage": {"total_tokens": 10}
    }