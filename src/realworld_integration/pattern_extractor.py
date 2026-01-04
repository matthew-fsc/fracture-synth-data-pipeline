"""
Pattern Extractor for Real-World Data Integration

Extracts patterns from real-world data sources to enhance synthetic data generation.
Identifies common patterns, anomalies, and edge cases from historical data.
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from collections import Counter
import pandas as pd
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PatternType(str, Enum):
    """Types of patterns that can be extracted."""
    OPERATIONAL_METRIC = "operational_metric"
    PAIN_POINT = "pain_point"
    INDUSTRY_TREND = "industry_trend"
    FAILURE_CASE = "failure_case"
    EDGE_CASE = "edge_case"
    COMPLIANCE_PATTERN = "compliance_pattern"
    WORKFLOW_PATTERN = "workflow_pattern"
    STAKEHOLDER_PATTERN = "stakeholder_pattern"


class Pattern(BaseModel):
    """Extracted pattern from real-world data."""
    pattern_id: str
    pattern_type: PatternType
    pattern_name: str
    description: str
    frequency: float = Field(ge=0.0, le=1.0, description="Frequency of pattern (0-1)")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in pattern extraction")
    attributes: Dict[str, Any] = Field(default_factory=dict)
    source_data: Optional[str] = None
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PatternExtractor:
    """
    Extracts patterns from real-world data sources.
    
    Analyzes historical data, transcripts, and real datasets to identify
    common patterns, edge cases, and failure scenarios.
    """
    
    def __init__(
        self,
        patterns_dir: Optional[Path] = None,
        min_confidence: float = 0.6
    ):
        """
        Initialize pattern extractor.
        
        Args:
            patterns_dir: Directory to store extracted patterns
            min_confidence: Minimum confidence threshold for patterns
        """
        self.patterns_dir = patterns_dir or Path("data/patterns")
        self.patterns_dir.mkdir(parents=True, exist_ok=True)
        self.min_confidence = min_confidence
        self.patterns: Dict[str, Pattern] = {}
        self._load_patterns()
    
    def _load_patterns(self):
        """Load existing patterns from disk."""
        patterns_file = self.patterns_dir / "patterns.json"
        if patterns_file.exists():
            try:
                with open(patterns_file, 'r') as f:
                    data = json.load(f)
                    self.patterns = {
                        pid: Pattern(**pattern_data)
                        for pid, pattern_data in data.items()
                    }
                logger.info(f"Loaded {len(self.patterns)} patterns")
            except Exception as e:
                logger.warning(f"Failed to load patterns: {e}")
    
    def _save_patterns(self):
        """Save patterns to disk."""
        patterns_file = self.patterns_dir / "patterns.json"
        try:
            data = {
                pid: pattern.dict()
                for pid, pattern in self.patterns.items()
            }
            with open(patterns_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save patterns: {e}")
    
    def extract_from_datasets(
        self,
        datasets: List[pd.DataFrame],
        pattern_types: Optional[List[PatternType]] = None
    ) -> List[Pattern]:
        """
        Extract patterns from dataset DataFrames.
        
        Args:
            datasets: List of DataFrames containing real-world data
            pattern_types: Optional list of pattern types to extract
            
        Returns:
            List of extracted patterns
        """
        if pattern_types is None:
            pattern_types = list(PatternType)
        
        extracted_patterns = []
        
        for pattern_type in pattern_types:
            if pattern_type == PatternType.OPERATIONAL_METRIC:
                patterns = self._extract_operational_metrics(datasets)
            elif pattern_type == PatternType.PAIN_POINT:
                patterns = self._extract_pain_points(datasets)
            elif pattern_type == PatternType.FAILURE_CASE:
                patterns = self._extract_failure_cases(datasets)
            elif pattern_type == PatternType.EDGE_CASE:
                patterns = self._extract_edge_cases(datasets)
            else:
                continue
            
            extracted_patterns.extend(patterns)
        
        # Filter by confidence
        extracted_patterns = [
            p for p in extracted_patterns
            if p.confidence >= self.min_confidence
        ]
        
        # Store patterns
        for pattern in extracted_patterns:
            self.patterns[pattern.pattern_id] = pattern
        
        self._save_patterns()
        
        return extracted_patterns
    
    def _extract_operational_metrics(self, datasets: List[pd.DataFrame]) -> List[Pattern]:
        """Extract operational metric patterns."""
        patterns = []
        
        # Combine all datasets
        combined_df = pd.concat(datasets, ignore_index=True) if datasets else pd.DataFrame()
        
        if combined_df.empty:
            return patterns
        
        # Extract common metric patterns
        metric_columns = [
            col for col in combined_df.columns
            if any(keyword in col.lower() for keyword in ['volume', 'count', 'rate', 'delay', 'failure'])
        ]
        
        for col in metric_columns:
            if col not in combined_df.columns:
                continue
            
            values = combined_df[col].dropna()
            if len(values) == 0:
                continue
            
            # Calculate statistics
            mean_val = values.mean()
            std_val = values.std()
            median_val = values.median()
            
            # Identify common ranges
            q25 = values.quantile(0.25)
            q75 = values.quantile(0.75)
            
            pattern = Pattern(
                pattern_id=f"op_metric_{col}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                pattern_type=PatternType.OPERATIONAL_METRIC,
                pattern_name=f"Operational Metric Pattern: {col}",
                description=f"Common patterns for {col} metric",
                frequency=1.0 - (std_val / mean_val) if mean_val > 0 else 0.0,
                confidence=0.8,
                attributes={
                    "column": col,
                    "mean": float(mean_val),
                    "std": float(std_val),
                    "median": float(median_val),
                    "q25": float(q25),
                    "q75": float(q75),
                    "min": float(values.min()),
                    "max": float(values.max())
                },
                source_data="dataset_analysis"
            )
            patterns.append(pattern)
        
        return patterns
    
    def _extract_pain_points(self, datasets: List[pd.DataFrame]) -> List[Pattern]:
        """Extract pain point patterns from text columns."""
        patterns = []
        
        # Look for text columns that might contain pain points
        text_columns = [
            col for col in (datasets[0].columns if datasets else [])
            if datasets[0][col].dtype == 'object'
        ]
        
        # Simple keyword-based extraction (can be enhanced with NLP)
        pain_keywords = [
            'slow', 'delayed', 'failed', 'error', 'issue', 'problem',
            'bottleneck', 'inefficient', 'broken', 'complex', 'difficult'
        ]
        
        for col in text_columns[:3]:  # Limit to first 3 text columns
            if not datasets:
                continue
            
            all_text = ' '.join([
                str(val) for df in datasets
                for val in df[col].dropna().astype(str)
            ]).lower()
            
            keyword_counts = Counter()
            for keyword in pain_keywords:
                count = all_text.count(keyword)
                if count > 0:
                    keyword_counts[keyword] = count
            
            # Create pattern for frequent pain points
            total_words = len(all_text.split())
            for keyword, count in keyword_counts.most_common(5):
                frequency = count / total_words if total_words > 0 else 0.0
                if frequency > 0.001:  # At least 0.1% frequency
                    pattern = Pattern(
                        pattern_id=f"pain_point_{keyword}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                        pattern_type=PatternType.PAIN_POINT,
                        pattern_name=f"Pain Point: {keyword}",
                        description=f"Common pain point keyword: {keyword}",
                        frequency=min(frequency * 100, 1.0),
                        confidence=0.7,
                        attributes={
                            "keyword": keyword,
                            "count": count,
                            "frequency": frequency
                        },
                        source_data="text_analysis"
                    )
                    patterns.append(pattern)
        
        return patterns
    
    def _extract_failure_cases(self, datasets: List[pd.DataFrame]) -> List[Pattern]:
        """Extract failure case patterns."""
        patterns = []
        
        combined_df = pd.concat(datasets, ignore_index=True) if datasets else pd.DataFrame()
        if combined_df.empty:
            return patterns
        
        # Look for failure-related columns
        failure_columns = [
            col for col in combined_df.columns
            if any(keyword in col.lower() for keyword in ['failure', 'error', 'breach', 'stall'])
        ]
        
        for col in failure_columns:
            if col not in combined_df.columns:
                continue
            
            values = combined_df[col].dropna()
            if len(values) == 0:
                continue
            
            # Identify failure thresholds
            failure_rate = (values > 0).sum() / len(values) if len(values) > 0 else 0.0
            
            if failure_rate > 0.05:  # At least 5% failure rate
                pattern = Pattern(
                    pattern_id=f"failure_case_{col}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    pattern_type=PatternType.FAILURE_CASE,
                    pattern_name=f"Failure Case: {col}",
                    description=f"Common failure pattern for {col}",
                    frequency=failure_rate,
                    confidence=0.75,
                    attributes={
                        "column": col,
                        "failure_rate": float(failure_rate),
                        "avg_failures": float(values[values > 0].mean()) if (values > 0).any() else 0.0,
                        "max_failures": float(values.max())
                    },
                    source_data="dataset_analysis"
                )
                patterns.append(pattern)
        
        return patterns
    
    def _extract_edge_cases(self, datasets: List[pd.DataFrame]) -> List[Pattern]:
        """Extract edge case patterns (outliers, extremes)."""
        patterns = []
        
        combined_df = pd.concat(datasets, ignore_index=True) if datasets else pd.DataFrame()
        if combined_df.empty:
            return patterns
        
        numeric_columns = combined_df.select_dtypes(include=['int64', 'float64']).columns
        
        for col in numeric_columns[:5]:  # Limit to first 5 numeric columns
            values = combined_df[col].dropna()
            if len(values) < 10:
                continue
            
            # Identify outliers using IQR method
            q1 = values.quantile(0.25)
            q3 = values.quantile(0.75)
            iqr = q3 - q1
            
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            outliers = values[(values < lower_bound) | (values > upper_bound)]
            outlier_rate = len(outliers) / len(values) if len(values) > 0 else 0.0
            
            if outlier_rate > 0.05:  # At least 5% outliers
                pattern = Pattern(
                    pattern_id=f"edge_case_{col}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    pattern_type=PatternType.EDGE_CASE,
                    pattern_name=f"Edge Case: {col}",
                    description=f"Edge case patterns for {col} (outliers)",
                    frequency=outlier_rate,
                    confidence=0.7,
                    attributes={
                        "column": col,
                        "outlier_rate": float(outlier_rate),
                        "lower_bound": float(lower_bound),
                        "upper_bound": float(upper_bound),
                        "min_outlier": float(outliers.min()) if len(outliers) > 0 else None,
                        "max_outlier": float(outliers.max()) if len(outliers) > 0 else None
                    },
                    source_data="statistical_analysis"
                )
                patterns.append(pattern)
        
        return patterns
    
    def extract_from_transcripts(
        self,
        transcripts: List[str],
        pattern_types: Optional[List[PatternType]] = None
    ) -> List[Pattern]:
        """
        Extract patterns from text transcripts.
        
        Args:
            transcripts: List of transcript texts
            pattern_types: Optional list of pattern types to extract
            
        Returns:
            List of extracted patterns
        """
        if pattern_types is None:
            pattern_types = [PatternType.PAIN_POINT, PatternType.STAKEHOLDER_PATTERN]
        
        extracted_patterns = []
        
        # Combine all transcripts
        combined_text = ' '.join(transcripts).lower()
        
        # Extract pain points (simplified - can be enhanced with NLP)
        if PatternType.PAIN_POINT in pattern_types:
            pain_patterns = self._extract_pain_points_from_text(combined_text)
            extracted_patterns.extend(pain_patterns)
        
        # Store patterns
        for pattern in extracted_patterns:
            if pattern.confidence >= self.min_confidence:
                self.patterns[pattern.pattern_id] = pattern
        
        self._save_patterns()
        
        return extracted_patterns
    
    def _extract_pain_points_from_text(self, text: str) -> List[Pattern]:
        """Extract pain points from text."""
        patterns = []
        pain_keywords = [
            'slow', 'delayed', 'failed', 'error', 'issue', 'problem',
            'bottleneck', 'inefficient', 'broken', 'complex', 'difficult',
            'manual', 'time-consuming', 'redundant'
        ]
        
        words = text.split()
        total_words = len(words)
        
        for keyword in pain_keywords:
            count = text.count(keyword)
            if count > 0:
                frequency = count / total_words if total_words > 0 else 0.0
                if frequency > 0.0001:  # At least 0.01% frequency
                    pattern = Pattern(
                        pattern_id=f"pain_text_{keyword}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                        pattern_type=PatternType.PAIN_POINT,
                        pattern_name=f"Pain Point: {keyword}",
                        description=f"Pain point keyword from transcripts: {keyword}",
                        frequency=min(frequency * 1000, 1.0),
                        confidence=0.65,
                        attributes={
                            "keyword": keyword,
                            "count": count,
                            "frequency": frequency
                        },
                        source_data="transcript_analysis"
                    )
                    patterns.append(pattern)
        
        return patterns
    
    def get_patterns(
        self,
        pattern_type: Optional[PatternType] = None,
        min_frequency: float = 0.0,
        min_confidence: float = 0.0
    ) -> List[Pattern]:
        """
        Get stored patterns with optional filters.
        
        Args:
            pattern_type: Optional filter by pattern type
            min_frequency: Minimum frequency threshold
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of matching patterns
        """
        patterns = list(self.patterns.values())
        
        if pattern_type:
            patterns = [p for p in patterns if p.pattern_type == pattern_type]
        
        patterns = [p for p in patterns if p.frequency >= min_frequency]
        patterns = [p for p in patterns if p.confidence >= min_confidence]
        
        return sorted(patterns, key=lambda p: p.confidence, reverse=True)
    
    def get_pattern_by_id(self, pattern_id: str) -> Optional[Pattern]:
        """Get a specific pattern by ID."""
        return self.patterns.get(pattern_id)

