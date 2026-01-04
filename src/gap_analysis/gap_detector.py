"""
Gap Detector for Training Data Analysis

Identifies gaps in training datasets to guide targeted synthetic data generation.
Analyzes coverage across industries, scenarios, complexity levels, and edge cases.
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime
from enum import Enum
from collections import Counter, defaultdict
import pandas as pd
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class GapType(str, Enum):
    """Types of gaps in training data."""
    INDUSTRY_COVERAGE = "industry_coverage"
    COMPLEXITY_LEVEL = "complexity_level"
    SCENARIO_TYPE = "scenario_type"
    EDGE_CASE = "edge_case"
    FAILURE_CASE = "failure_case"
    METRIC_RANGE = "metric_range"
    PAIN_POINT_COVERAGE = "pain_point_coverage"
    STAKEHOLDER_DIVERSITY = "stakeholder_diversity"


class GapPriority(str, Enum):
    """Priority levels for gaps."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Gap(BaseModel):
    """Identified gap in training data."""
    gap_id: str
    gap_type: GapType
    description: str
    priority: GapPriority
    coverage_score: float = Field(ge=0.0, le=1.0, description="Current coverage (0-1)")
    target_coverage: float = Field(ge=0.0, le=1.0, description="Target coverage (0-1)")
    gap_size: float = Field(ge=0.0, description="Gap size (target - current)")
    attributes: Dict[str, Any] = Field(default_factory=dict)
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GapDetector:
    """
    Detects gaps in training datasets.
    
    Analyzes existing datasets to identify areas with insufficient coverage
    and recommends targeted data generation to fill gaps.
    """
    
    def __init__(
        self,
        gaps_dir: Optional[Path] = None,
        min_coverage_threshold: float = 0.1,
        target_coverage: float = 0.8
    ):
        """
        Initialize gap detector.
        
        Args:
            gaps_dir: Directory to store gap analysis results
            min_coverage_threshold: Minimum coverage threshold (below this = gap)
            target_coverage: Target coverage level (0-1)
        """
        self.gaps_dir = gaps_dir or Path("data/gap_analysis")
        self.gaps_dir.mkdir(parents=True, exist_ok=True)
        self.min_coverage_threshold = min_coverage_threshold
        self.target_coverage = target_coverage
        self.detected_gaps: Dict[str, Gap] = {}
    
    def detect_gaps(
        self,
        datasets: List[Dict[str, Any]],
        gap_types: Optional[List[GapType]] = None
    ) -> List[Gap]:
        """
        Detect gaps in training datasets.
        
        Args:
            datasets: List of dataset dictionaries (from registry)
            gap_types: Optional list of gap types to detect
            
        Returns:
            List of detected gaps
        """
        if gap_types is None:
            gap_types = list(GapType)
        
        gaps = []
        
        # Extract data for analysis
        dataset_data = self._extract_dataset_data(datasets)
        
        # Detect gaps by type
        if GapType.INDUSTRY_COVERAGE in gap_types:
            gaps.extend(self._detect_industry_gaps(dataset_data))
        
        if GapType.COMPLEXITY_LEVEL in gap_types:
            gaps.extend(self._detect_complexity_gaps(dataset_data))
        
        if GapType.SCENARIO_TYPE in gap_types:
            gaps.extend(self._detect_scenario_type_gaps(dataset_data))
        
        if GapType.EDGE_CASE in gap_types:
            gaps.extend(self._detect_edge_case_gaps(dataset_data))
        
        if GapType.FAILURE_CASE in gap_types:
            gaps.extend(self._detect_failure_case_gaps(dataset_data))
        
        if GapType.METRIC_RANGE in gap_types:
            gaps.extend(self._detect_metric_range_gaps(dataset_data))
        
        if GapType.PAIN_POINT_COVERAGE in gap_types:
            gaps.extend(self._detect_pain_point_gaps(dataset_data))
        
        # Store gaps
        for gap in gaps:
            self.detected_gaps[gap.gap_id] = gap
        
        # Save gaps
        self._save_gaps()
        
        return gaps
    
    def _extract_dataset_data(self, datasets: List[Dict]) -> Dict[str, List]:
        """Extract relevant data from datasets for analysis."""
        data = {
            "industries": [],
            "complexity_scores": [],
            "scenario_types": [],
            "metrics": defaultdict(list),
            "pain_points": [],
            "edge_cases": [],
            "failure_cases": []
        }
        
        for dataset in datasets:
            version_data = dataset.get("version", {})
            metadata = version_data.get("metadata", {})
            company_profile = metadata.get("company_profile", {})
            system_manifest = metadata.get("system_manifest", {})
            quality_scores = version_data.get("quality_scores", {})
            
            # Extract industry
            if "industry" in company_profile:
                data["industries"].append(company_profile["industry"])
            
            # Extract complexity
            if "complexity_score" in system_manifest:
                data["complexity_scores"].append(system_manifest["complexity_score"])
            
            # Extract metrics
            operational_metrics = company_profile.get("operational_metrics", {})
            for key, value in operational_metrics.items():
                if isinstance(value, (int, float)):
                    data["metrics"][key].append(value)
            
            # Extract pain points
            pain_points = company_profile.get("pain_points", [])
            data["pain_points"].extend(pain_points)
            
            # Extract edge cases (high/low values)
            for key, values in data["metrics"].items():
                if values:
                    q1 = pd.Series(values).quantile(0.25)
                    q3 = pd.Series(values).quantile(0.75)
                    iqr = q3 - q1
                    upper_bound = q3 + 1.5 * iqr
                    lower_bound = q1 - 1.5 * iqr
                    
                    if any(v > upper_bound or v < lower_bound for v in values):
                        data["edge_cases"].append(key)
        
        return data
    
    def _detect_industry_gaps(self, dataset_data: Dict) -> List[Gap]:
        """Detect gaps in industry coverage."""
        gaps = []
        
        # Common industries (can be expanded)
        common_industries = [
            "Technology", "Healthcare", "Finance", "Manufacturing",
            "Retail", "Energy", "Transportation", "Education",
            "Government", "Telecommunications"
        ]
        
        industry_counts = Counter(dataset_data["industries"])
        total_datasets = len(dataset_data["industries"])
        
        if total_datasets == 0:
            # No data - all industries are gaps
            for industry in common_industries:
                gap = Gap(
                    gap_id=f"industry_{industry}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    gap_type=GapType.INDUSTRY_COVERAGE,
                    description=f"Missing coverage for {industry} industry",
                    priority=GapPriority.HIGH,
                    coverage_score=0.0,
                    target_coverage=self.target_coverage,
                    gap_size=self.target_coverage,
                    attributes={"industry": industry, "current_count": 0}
                )
                gaps.append(gap)
        else:
            for industry in common_industries:
                count = industry_counts.get(industry, 0)
                coverage = count / total_datasets if total_datasets > 0 else 0.0
                
                if coverage < self.min_coverage_threshold:
                    gap_size = self.target_coverage - coverage
                    priority = GapPriority.CRITICAL if coverage == 0.0 else GapPriority.HIGH
                    
                    gap = Gap(
                        gap_id=f"industry_{industry}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                        gap_type=GapType.INDUSTRY_COVERAGE,
                        description=f"Low coverage for {industry} industry ({coverage:.1%})",
                        priority=priority,
                        coverage_score=coverage,
                        target_coverage=self.target_coverage,
                        gap_size=gap_size,
                        attributes={
                            "industry": industry,
                            "current_count": count,
                            "total_datasets": total_datasets
                        }
                    )
                    gaps.append(gap)
        
        return gaps
    
    def _detect_complexity_gaps(self, dataset_data: Dict) -> List[Gap]:
        """Detect gaps in complexity level coverage."""
        gaps = []
        
        complexity_scores = dataset_data["complexity_scores"]
        if not complexity_scores:
            # No complexity data - create gap
            gap = Gap(
                gap_id=f"complexity_none_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                gap_type=GapType.COMPLEXITY_LEVEL,
                description="Missing complexity score data",
                priority=GapPriority.MEDIUM,
                coverage_score=0.0,
                target_coverage=self.target_coverage,
                gap_size=self.target_coverage,
                attributes={}
            )
            gaps.append(gap)
            return gaps
        
        # Define complexity buckets
        complexity_buckets = {
            "low": (0.0, 0.33),
            "medium": (0.33, 0.66),
            "high": (0.66, 1.0)
        }
        
        total = len(complexity_scores)
        bucket_counts = defaultdict(int)
        
        for score in complexity_scores:
            for bucket_name, (min_val, max_val) in complexity_buckets.items():
                if min_val <= score < max_val:
                    bucket_counts[bucket_name] += 1
                    break
        
        for bucket_name, (min_val, max_val) in complexity_buckets.items():
            count = bucket_counts[bucket_name]
            coverage = count / total if total > 0 else 0.0
            
            if coverage < self.min_coverage_threshold:
                gap_size = self.target_coverage - coverage
                
                gap = Gap(
                    gap_id=f"complexity_{bucket_name}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    gap_type=GapType.COMPLEXITY_LEVEL,
                    description=f"Low coverage for {bucket_name} complexity ({coverage:.1%})",
                    priority=GapPriority.HIGH if coverage == 0.0 else GapPriority.MEDIUM,
                    coverage_score=coverage,
                    target_coverage=self.target_coverage,
                    gap_size=gap_size,
                    attributes={
                        "complexity_level": bucket_name,
                        "range": f"{min_val:.2f}-{max_val:.2f}",
                        "current_count": count,
                        "total": total
                    }
                )
                gaps.append(gap)
        
        return gaps
    
    def _detect_scenario_type_gaps(self, dataset_data: Dict) -> List[Gap]:
        """Detect gaps in scenario type coverage."""
        # This is a placeholder - scenario types would need to be defined
        # based on business context (e.g., migration, new system, enhancement)
        gaps = []
        
        # Simplified implementation
        gap = Gap(
            gap_id=f"scenario_type_general_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            gap_type=GapType.SCENARIO_TYPE,
            description="Need to analyze scenario type distribution",
            priority=GapPriority.MEDIUM,
            coverage_score=0.5,  # Unknown
            target_coverage=self.target_coverage,
            gap_size=0.3,
            attributes={}
        )
        gaps.append(gap)
        
        return gaps
    
    def _detect_edge_case_gaps(self, dataset_data: Dict) -> List[Gap]:
        """Detect gaps in edge case coverage."""
        gaps = []
        
        edge_cases = dataset_data["edge_cases"]
        metrics = dataset_data["metrics"]
        
        # If we have edge cases but low representation, it's a gap
        if edge_cases and len(set(edge_cases)) < len(metrics) * 0.5:
            gap = Gap(
                gap_id=f"edge_case_coverage_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                gap_type=GapType.EDGE_CASE,
                description="Insufficient edge case coverage across metrics",
                priority=GapPriority.MEDIUM,
                coverage_score=len(set(edge_cases)) / len(metrics) if metrics else 0.0,
                target_coverage=self.target_coverage,
                gap_size=0.3,
                attributes={
                    "edge_case_count": len(set(edge_cases)),
                    "total_metrics": len(metrics)
                }
            )
            gaps.append(gap)
        
        return gaps
    
    def _detect_failure_case_gaps(self, dataset_data: Dict) -> List[Gap]:
        """Detect gaps in failure case coverage."""
        gaps = []
        
        # Check for failure-related metrics
        failure_metrics = [
            key for key in dataset_data["metrics"].keys()
            if any(keyword in key.lower() for keyword in ['failure', 'error', 'breach', 'stall'])
        ]
        
        if not failure_metrics:
            gap = Gap(
                gap_id=f"failure_case_missing_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                gap_type=GapType.FAILURE_CASE,
                description="Missing failure case scenarios",
                priority=GapPriority.HIGH,
                coverage_score=0.0,
                target_coverage=self.target_coverage,
                gap_size=self.target_coverage,
                attributes={}
            )
            gaps.append(gap)
        
        return gaps
    
    def _detect_metric_range_gaps(self, dataset_data: Dict) -> List[Gap]:
        """Detect gaps in metric value ranges."""
        gaps = []
        
        metrics = dataset_data["metrics"]
        
        for metric_name, values in metrics.items():
            if not values or len(values) < 5:
                continue
            
            # Check distribution
            value_series = pd.Series(values)
            q1 = value_series.quantile(0.25)
            q3 = value_series.quantile(0.75)
            
            # If most values are clustered (low variance), we need more diversity
            iqr = q3 - q1
            mean_val = value_series.mean()
            
            if mean_val > 0:
                cv = iqr / mean_val  # Coefficient of variation (simplified)
                if cv < 0.2:  # Low variance
                    gap = Gap(
                        gap_id=f"metric_range_{metric_name}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                        gap_type=GapType.METRIC_RANGE,
                        description=f"Low variance in {metric_name} metric - need more diverse values",
                        priority=GapPriority.MEDIUM,
                        coverage_score=cv / 0.5,  # Normalized
                        target_coverage=0.5,
                        gap_size=0.5 - cv / 0.5,
                        attributes={
                            "metric": metric_name,
                            "coefficient_of_variation": float(cv),
                            "mean": float(mean_val),
                            "iqr": float(iqr)
                        }
                    )
                    gaps.append(gap)
        
        return gaps
    
    def _detect_pain_point_gaps(self, dataset_data: Dict) -> List[Gap]:
        """Detect gaps in pain point coverage."""
        gaps = []
        
        pain_points = dataset_data["pain_points"]
        pain_point_counts = Counter(pain_points)
        
        if not pain_points:
            gap = Gap(
                gap_id=f"pain_point_missing_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                gap_type=GapType.PAIN_POINT_COVERAGE,
                description="Missing pain point data",
                priority=GapPriority.MEDIUM,
                coverage_score=0.0,
                target_coverage=self.target_coverage,
                gap_size=self.target_coverage,
                attributes={}
            )
            gaps.append(gap)
        else:
            # Check diversity of pain points
            unique_pain_points = len(set(pain_points))
            total_pain_points = len(pain_points)
            
            if unique_pain_points / total_pain_points < 0.5:  # Low diversity
                gap = Gap(
                    gap_id=f"pain_point_diversity_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    gap_type=GapType.PAIN_POINT_COVERAGE,
                    description="Low diversity in pain points - need more variety",
                    priority=GapPriority.MEDIUM,
                    coverage_score=unique_pain_points / total_pain_points,
                    target_coverage=0.7,
                    gap_size=0.7 - (unique_pain_points / total_pain_points),
                    attributes={
                        "unique_pain_points": unique_pain_points,
                        "total_pain_points": total_pain_points
                    }
                )
                gaps.append(gap)
        
        return gaps
    
    def get_gaps(
        self,
        gap_type: Optional[GapType] = None,
        priority: Optional[GapPriority] = None,
        min_gap_size: float = 0.0
    ) -> List[Gap]:
        """
        Get detected gaps with optional filters.
        
        Args:
            gap_type: Optional filter by gap type
            priority: Optional filter by priority
            min_gap_size: Minimum gap size threshold
            
        Returns:
            List of matching gaps
        """
        gaps = list(self.detected_gaps.values())
        
        if gap_type:
            gaps = [g for g in gaps if g.gap_type == gap_type]
        
        if priority:
            gaps = [g for g in gaps if g.priority == priority]
        
        gaps = [g for g in gaps if g.gap_size >= min_gap_size]
        
        return sorted(gaps, key=lambda g: (
            GapPriority.__members__[g.priority.value].value,
            g.gap_size
        ), reverse=True)
    
    def _save_gaps(self):
        """Save detected gaps to disk."""
        gaps_file = self.gaps_dir / "gaps.json"
        try:
            data = {
                gap_id: gap.dict()
                for gap_id, gap in self.detected_gaps.items()
            }
            with open(gaps_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save gaps: {e}")

