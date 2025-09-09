"""
Baseline Capture Validation Module

Provides quality validation for baseline capture including:
- Face detection confidence validation (>0.8)
- Audio SNR validation (>20dB)
- Real-time feedback for capture quality
"""

from .quality_validator import QualityValidator

__all__ = ['QualityValidator']