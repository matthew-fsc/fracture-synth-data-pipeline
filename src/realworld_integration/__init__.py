"""
Real-World Integration Module

Provides:
- Pattern extraction from real-world data
- Scenario enhancement with real-world patterns
- Failure case generation (edge cases)
- Data diversity optimization through real-world incorporation
"""

from .pattern_extractor import PatternExtractor, Pattern, PatternType
from .scenario_enhancer import ScenarioEnhancer, EnhancementStrategy

__all__ = [
    "PatternExtractor",
    "Pattern",
    "PatternType",
    "ScenarioEnhancer",
    "EnhancementStrategy",
]

