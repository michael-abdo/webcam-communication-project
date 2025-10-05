"""
Baseline Capture API Module

Provides REST API endpoints for baseline capture workflow:
- Session initialization and management
- Face and speech baseline upload handling
- Real-time quality feedback
- Baseline completion and results retrieval
"""

from .baseline_api import baseline_router

__all__ = ['baseline_router']