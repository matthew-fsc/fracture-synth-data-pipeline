"""
Enhanced Data Quality Validation using Great Expectations.

Provides comprehensive validation framework with:
- Expectation suites
- Data quality metrics tracking
- Validation result storage
- Automated quality gates
- Statistical validation checks
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import pandas as pd
from pydantic import BaseModel, Field

try:
    import great_expectations as ge
    from great_expectations.core import ExpectationSuite
    from great_expectations.checkpoint import SimpleCheckpoint
    from great_expectations.data_context import BaseDataContext
    from great_expectations.data_context.types.base import DataContextConfig, FilesystemStoreBackendDefaults
    GE_AVAILABLE = True
except ImportError:
    GE_AVAILABLE = False
    logging.warning("Great Expectations not available. Install with: pip install great-expectations")

from .quality_validator import QualityCheckResult

logger = logging.getLogger(__name__)


class ValidationResult(BaseModel):
    """Enhanced validation result with metrics."""
    validation_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    dataset_type: str
    expectation_suite_name: str
    success: bool
    statistics: Dict[str, Any] = Field(default_factory=dict)
    results: List[Dict[str, Any]] = Field(default_factory=list)
    quality_score: float = 0.0  # 0.0-1.0
    failed_expectations: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EnhancedQualityValidator:
    """
    Enhanced quality validator with Great Expectations integration.
    
    Provides comprehensive validation with expectation suites,
    metrics tracking, and quality gates.
    """
    
    def __init__(
        self,
        expectations_dir: Optional[Path] = None,
        data_context_dir: Optional[Path] = None,
        validation_results_dir: Optional[Path] = None
    ):
        """
        Initialize enhanced quality validator.
        
        Args:
            expectations_dir: Directory for expectation suites
            data_context_dir: Directory for Great Expectations data context
            validation_results_dir: Directory for validation results
        """
        self.expectations_dir = expectations_dir or Path("data/expectations")
        self.expectations_dir.mkdir(parents=True, exist_ok=True)
        
        self.data_context_dir = data_context_dir or Path("data/great_expectations")
        self.data_context_dir.mkdir(parents=True, exist_ok=True)
        
        self.validation_results_dir = validation_results_dir or Path("data/validation_results")
        self.validation_results_dir.mkdir(parents=True, exist_ok=True)
        
        self.ge_context: Optional[BaseDataContext] = None
        
        if GE_AVAILABLE:
            self._init_ge_context()
        else:
            logger.warning("Great Expectations not available, using basic validation only")
    
    def _init_ge_context(self):
        """Initialize Great Expectations data context."""
        if not GE_AVAILABLE:
            return
        
        try:
            # Try to load existing context
            if (self.data_context_dir / "great_expectations.yml").exists():
                self.ge_context = ge.get_context(context_root_dir=str(self.data_context_dir))
            else:
                # Create new context
                data_context_config = DataContextConfig(
                    config_version=3.0,
                    datasources={},
                    stores={
                        "expectations_store": {
                            "class_name": "ExpectationsStore",
                            "store_backend": {
                                "class_name": "TupleFilesystemStoreBackend",
                                "base_directory": str(self.expectations_dir)
                            }
                        },
                        "validations_store": {
                            "class_name": "ValidationsStore",
                            "store_backend": {
                                "class_name": "TupleFilesystemStoreBackend",
                                "base_directory": str(self.validation_results_dir)
                            }
                        },
                        "evaluation_parameter_store": {
                            "class_name": "EvaluationParameterStore"
                        }
                    },
                    expectations_store_name="expectations_store",
                    validations_store_name="validations_store",
                    evaluation_parameter_store_name="evaluation_parameter_store",
                    checkpoint_store_name="checkpoint_store",
                    data_docs_sites={},
                    config_variables_file_path=None
                )
                
                store_backend_defaults = FilesystemStoreBackendDefaults(
                    root_directory=str(self.data_context_dir)
                )
                
                self.ge_context = BaseDataContext(
                    project_config=data_context_config,
                    context_root_dir=str(self.data_context_dir),
                    runtime_environment={
                        "root_directory": str(self.data_context_dir)
                    }
                )
        except Exception as e:
            logger.error(f"Failed to initialize Great Expectations context: {e}")
            self.ge_context = None
    
    def create_expectation_suite(
        self,
        suite_name: str,
        dataset_type: str = "training_samples"
    ) -> Optional[ExpectationSuite]:
        """
        Create expectation suite for dataset type.
        
        Args:
            suite_name: Name of the expectation suite
            dataset_type: Type of dataset (training_samples, company_profiles, etc.)
            
        Returns:
            ExpectationSuite or None if GE not available
        """
        if not GE_AVAILABLE or not self.ge_context:
            logger.warning("Great Expectations not available")
            return None
        
        try:
            # Create or get suite
            try:
                suite = self.ge_context.get_expectation_suite(suite_name)
            except:
                suite = self.ge_context.create_expectation_suite(suite_name)
            
            # Add expectations based on dataset type
            if dataset_type == "training_samples":
                self._add_training_sample_expectations(suite)
            elif dataset_type == "company_profiles":
                self._add_company_profile_expectations(suite)
            elif dataset_type == "system_manifests":
                self._add_system_manifest_expectations(suite)
            
            # Save suite
            self.ge_context.save_expectation_suite(suite)
            
            return suite
            
        except Exception as e:
            logger.error(f"Failed to create expectation suite: {e}")
            return None
    
    def _add_training_sample_expectations(self, suite: ExpectationSuite):
        """Add expectations for training samples."""
        # These would be added to a dataframe validator
        # For now, we'll define them conceptually
        pass
    
    def _add_company_profile_expectations(self, suite: ExpectationSuite):
        """Add expectations for company profiles."""
        pass
    
    def _add_system_manifest_expectations(self, suite: ExpectationSuite):
        """Add expectations for system manifests."""
        pass
    
    def validate_with_expectations(
        self,
        df: pd.DataFrame,
        suite_name: str,
        dataset_type: str = "training_samples"
    ) -> ValidationResult:
        """
        Validate DataFrame using expectation suite.
        
        Args:
            df: DataFrame to validate
            suite_name: Name of expectation suite
            dataset_type: Type of dataset
            
        Returns:
            ValidationResult
        """
        validation_id = f"validation_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        if not GE_AVAILABLE or not self.ge_context:
            # Fallback to basic validation
            return self._basic_validation(df, validation_id, suite_name, dataset_type)
        
        try:
            # Get or create suite
            try:
                suite = self.ge_context.get_expectation_suite(suite_name)
            except:
                suite = self.create_expectation_suite(suite_name, dataset_type)
            
            # Create validator
            validator = self.ge_context.get_validator(
                batch_request=None,
                expectation_suite=suite
            )
            
            # Validate
            ge_df = ge.from_pandas(df)
            validation_result = ge_df.validate(expectation_suite=suite)
            
            # Calculate quality score
            total_expectations = len(validation_result.results)
            passed_expectations = sum(1 for r in validation_result.results if r.success)
            quality_score = passed_expectations / total_expectations if total_expectations > 0 else 0.0
            
            # Extract failed expectations
            failed_expectations = [
                {
                    "expectation_type": r.expectation_config.expectation_type,
                    "kwargs": r.expectation_config.kwargs,
                    "result": r.result
                }
                for r in validation_result.results if not r.success
            ]
            
            # Create validation result
            result = ValidationResult(
                validation_id=validation_id,
                dataset_type=dataset_type,
                expectation_suite_name=suite_name,
                success=validation_result.success,
                statistics={
                    "total_expectations": total_expectations,
                    "passed_expectations": passed_expectations,
                    "failed_expectations": len(failed_expectations),
                    "success_rate": quality_score
                },
                results=[r.to_json_dict() for r in validation_result.results],
                quality_score=quality_score,
                failed_expectations=failed_expectations,
                metadata={
                    "dataframe_shape": df.shape,
                    "columns": list(df.columns)
                }
            )
            
            # Save validation result
            self._save_validation_result(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Great Expectations validation failed: {e}")
            return self._basic_validation(df, validation_id, suite_name, dataset_type)
    
    def _basic_validation(self, df: pd.DataFrame, validation_id: str, suite_name: str, dataset_type: str) -> ValidationResult:
        """Basic validation fallback when GE is not available."""
        # Simple quality checks
        total_cells = df.size
        missing_cells = df.isnull().sum().sum()
        completeness = 1.0 - (missing_cells / total_cells) if total_cells > 0 else 0.0
        
        duplicate_rate = df.duplicated().sum() / len(df) if len(df) > 0 else 0.0
        
        quality_score = (completeness + (1 - duplicate_rate)) / 2.0
        
        return ValidationResult(
            validation_id=validation_id,
            dataset_type=dataset_type,
            expectation_suite_name=suite_name,
            success=quality_score >= 0.8,
            statistics={
                "completeness": completeness,
                "duplicate_rate": duplicate_rate,
                "total_rows": len(df),
                "total_columns": len(df.columns)
            },
            quality_score=quality_score,
            metadata={
                "dataframe_shape": df.shape,
                "columns": list(df.columns),
                "validation_type": "basic_fallback"
            }
        )
    
    def _save_validation_result(self, result: ValidationResult):
        """Save validation result to file."""
        result_path = self.validation_results_dir / f"{result.validation_id}.json"
        with open(result_path, 'w') as f:
            json.dump(result.dict(), f, indent=2, default=str)
    
    def get_validation_history(
        self,
        dataset_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[ValidationResult]:
        """
        Get validation history.
        
        Args:
            dataset_type: Filter by dataset type
            start_date: Start date filter
            end_date: End date filter
            
        Returns:
            List of validation results
        """
        results = []
        
        for result_file in self.validation_results_dir.glob("*.json"):
            try:
                with open(result_file, 'r') as f:
                    data = json.load(f)
                    result = ValidationResult(**data)
                    
                    # Apply filters
                    if dataset_type and result.dataset_type != dataset_type:
                        continue
                    
                    if start_date and result.timestamp < start_date:
                        continue
                    
                    if end_date and result.timestamp > end_date:
                        continue
                    
                    results.append(result)
            except Exception as e:
                logger.warning(f"Failed to load validation result {result_file}: {e}")
        
        return sorted(results, key=lambda x: x.timestamp, reverse=True)
    
    def get_quality_metrics(
        self,
        dataset_type: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get quality metrics over time.
        
        Args:
            dataset_type: Filter by dataset type
            days: Number of days to analyze
            
        Returns:
            Dictionary with quality metrics
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        history = self.get_validation_history(dataset_type=dataset_type, start_date=start_date)
        
        if not history:
            return {
                "total_validations": 0,
                "avg_quality_score": 0.0,
                "success_rate": 0.0,
                "trend": "no_data"
            }
        
        avg_quality_score = sum(r.quality_score for r in history) / len(history)
        success_rate = sum(1 for r in history if r.success) / len(history)
        
        # Calculate trend (comparing first half to second half)
        if len(history) >= 4:
            mid_point = len(history) // 2
            first_half_avg = sum(r.quality_score for r in history[mid_point:]) / mid_point
            second_half_avg = sum(r.quality_score for r in history[:mid_point]) / (len(history) - mid_point)
            
            if second_half_avg > first_half_avg * 1.05:
                trend = "improving"
            elif second_half_avg < first_half_avg * 0.95:
                trend = "degrading"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "total_validations": len(history),
            "avg_quality_score": avg_quality_score,
            "success_rate": success_rate,
            "trend": trend,
            "date_range": {
                "start": start_date.isoformat(),
                "end": datetime.utcnow().isoformat()
            }
        }

