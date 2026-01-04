"""Validation suite for synthetic data quality and realism."""

from .realism_validator import RealismValidator
from .schema_validator import SchemaValidator
from .quality_validator import QualityValidator

# Enhanced validators
try:
    from .quality_validator_enhanced import EnhancedQualityValidator, ValidationResult
    ENHANCED_VALIDATION_AVAILABLE = True
except ImportError:
    ENHANCED_VALIDATION_AVAILABLE = False
    EnhancedQualityValidator = None
    ValidationResult = None

__all__ = [
    "RealismValidator",
    "SchemaValidator",
    "QualityValidator",
]

if ENHANCED_VALIDATION_AVAILABLE:
    __all__.extend(["EnhancedQualityValidator", "ValidationResult"])
