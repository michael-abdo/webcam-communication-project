"""
Baseline Capture Analysis Module

Provides analysis capabilities for baseline capture data including:
- Face landmark analysis and baseline metrics calculation
- Eye openness, blink rate, and facial expression baselines
- Speech analysis including pitch, tone, and speaking rate baselines
- Statistical analysis and baseline validation
"""

from .baseline_analyzer import BaselineAnalyzer

__all__ = ['BaselineAnalyzer']