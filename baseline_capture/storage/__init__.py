"""
Baseline Capture Storage Module

Provides storage capabilities for baseline capture data including:
- S3 storage for baseline video/audio
- Local JSON storage for baseline metrics
- Session correlation with assessment data
"""

from .baseline_storage import BaselineStorage

__all__ = ['BaselineStorage']