"""
Gap Analysis Module

Provides:
- Training data gap detection
- Targeted synthetic data generation for gaps
- Dataset coverage analysis
- Gap prioritization
"""

from .gap_detector import GapDetector, Gap, GapType, GapPriority
from .targeted_generator import TargetedGenerator, GenerationTarget

__all__ = [
    "GapDetector",
    "Gap",
    "GapType",
    "GapPriority",
    "TargetedGenerator",
    "GenerationTarget",
]

