"""
Baseline Capture Core Module

Provides core orchestration for baseline capture sessions including:
- Session management and coordination
- 10-second neutral face baseline capture
- 15-second speech calibration capture
- Quality validation integration
- Retry logic and error handling
"""

from .capture_session import BaselineCapture

__all__ = ['BaselineCapture']