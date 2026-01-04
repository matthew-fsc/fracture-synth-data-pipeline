"""
Data quality validation using Great Expectations and custom checks.

Validates completeness, consistency, and quality of synthetic datasets.
"""

import logging
from typing import Dict, List, Optional
from pathlib import Path
import pandas as pd
from pydantic import BaseModel, Field

try:
    import great_expectations as ge
    GE_AVAILABLE = True
except ImportError:
    GE_AVAILABLE = False
    logging.warning("Great Expectations not available. Install with: pip install great-expectations")

logger = logging.getLogger(__name__)


class QualityCheckResult(BaseModel):
    """Result of a quality check."""
    check_name: str
    passed: bool
    score: float = 0.0  # 0.0-1.0
    message: str = ""
    details: Dict = {}


class QualityValidator:
    """Validates data quality using Great Expectations and custom checks."""
    
    def __init__(
        self,
        expectations_dir: Optional[Path] = None,
        use_great_expectations: bool = True
    ):
        """
        Initialize quality validator.
        
        Args:
            expectations_dir: Directory for Great Expectations expectations
            use_great_expectations: Whether to use Great Expectations
        """
        self.use_great_expectations = use_great_expectations and GE_AVAILABLE
        self.expectations_dir = expectations_dir or Path(__file__).parent.parent.parent / "data" / "expectations"
        self.expectations_dir.mkdir(parents=True, exist_ok=True)
    
    def validate_dataset(
        self,
        df: pd.DataFrame,
        dataset_type: str = "training_samples"
    ) -> List[QualityCheckResult]:
        """
        Validate a dataset for quality.
        
        Args:
            df: DataFrame to validate
            dataset_type: Type of dataset (for expectation selection)
            
        Returns:
            List of quality check results
        """
        results = []
        
        # Basic completeness checks
        results.append(self._check_completeness(df))
        results.append(self._check_duplicates(df))
        results.append(self._check_data_types(df))
        results.append(self._check_value_ranges(df))
        
        # Great Expectations validation if available
        if self.use_great_expectations:
            ge_results = self._validate_with_ge(df, dataset_type)
            results.extend(ge_results)
        
        return results
    
    def _check_completeness(self, df: pd.DataFrame) -> QualityCheckResult:
        """Check for missing values."""
        total_cells = df.size
        missing_cells = df.isnull().sum().sum()
        completeness = 1.0 - (missing_cells / total_cells) if total_cells > 0 else 0.0
        
        return QualityCheckResult(
            check_name="completeness",
            passed=completeness >= 0.95,
            score=completeness,
            message=f"Completeness: {completeness * 100:.1f}% ({missing_cells} missing values)",
            details={"missing_cells": int(missing_cells), "total_cells": int(total_cells)}
        )
    
    def _check_duplicates(self, df: pd.DataFrame) -> QualityCheckResult:
        """Check for duplicate rows."""
        duplicate_count = df.duplicated().sum()
        duplicate_rate = duplicate_count / len(df) if len(df) > 0 else 0.0
        
        return QualityCheckResult(
            check_name="duplicates",
            passed=duplicate_rate < 0.05,  # Allow up to 5% duplicates
            score=1.0 - duplicate_rate,
            message=f"Duplicate rate: {duplicate_rate * 100:.1f}% ({duplicate_count} duplicates)",
            details={"duplicate_count": int(duplicate_count)}
        )
    
    def _check_data_types(self, df: pd.DataFrame) -> QualityCheckResult:
        """Check data type consistency."""
        issues = []
        
        # Check for numeric columns with non-numeric values
        for col in df.select_dtypes(include=['int64', 'float64']).columns:
            non_numeric = pd.to_numeric(df[col], errors='coerce').isnull().sum()
            if non_numeric > 0:
                issues.append(f"{col}: {non_numeric} non-numeric values")
        
        score = 1.0 if len(issues) == 0 else max(0.0, 1.0 - len(issues) * 0.1)
        
        return QualityCheckResult(
            check_name="data_types",
            passed=len(issues) == 0,
            score=score,
            message=f"Data type issues: {len(issues)}" if issues else "All data types valid",
            details={"issues": issues}
        )
    
    def _check_value_ranges(self, df: pd.DataFrame) -> QualityCheckResult:
        """Check for values in expected ranges."""
        issues = []
        
        # Check for negative counts
        count_columns = [col for col in df.columns if 'count' in col.lower() or 'volume' in col.lower()]
        for col in count_columns:
            negative_count = (df[col] < 0).sum()
            if negative_count > 0:
                issues.append(f"{col}: {negative_count} negative values")
        
        # Check for rates/probabilities in [0, 1]
        rate_columns = [col for col in df.columns if 'rate' in col.lower() or 'probability' in col.lower()]
        for col in rate_columns:
            out_of_range = ((df[col] < 0) | (df[col] > 1)).sum()
            if out_of_range > 0:
                issues.append(f"{col}: {out_of_range} values outside [0, 1]")
        
        score = 1.0 if len(issues) == 0 else max(0.0, 1.0 - len(issues) * 0.1)
        
        return QualityCheckResult(
            check_name="value_ranges",
            passed=len(issues) == 0,
            score=score,
            message=f"Value range issues: {len(issues)}" if issues else "All values in expected ranges",
            details={"issues": issues}
        )
    
    def _validate_with_ge(
        self,
        df: pd.DataFrame,
        dataset_type: str
    ) -> List[QualityCheckResult]:
        """Validate using Great Expectations."""
        if not GE_AVAILABLE:
            return []
        
        results = []
        
        try:
            # Create a Great Expectations dataset
            ge_df = ge.from_pandas(df)
            
            # Basic expectations
            expectations = [
                ("expect_table_row_count_to_be_between", {"min_value": 1}),
                ("expect_table_columns_to_match_ordered_list", {"column_list": list(df.columns)}),
            ]
            
            for exp_name, exp_kwargs in expectations:
                try:
                    result = getattr(ge_df, exp_name)(**exp_kwargs)
                    results.append(QualityCheckResult(
                        check_name=f"ge_{exp_name}",
                        passed=result["success"],
                        score=1.0 if result["success"] else 0.0,
                        message=f"GE {exp_name}: {'PASSED' if result['success'] else 'FAILED'}",
                        details=result
                    ))
                except Exception as e:
                    logger.warning(f"GE expectation {exp_name} failed: {e}")
        
        except Exception as e:
            logger.error(f"Great Expectations validation error: {e}", exc_info=True)
        
        return results

