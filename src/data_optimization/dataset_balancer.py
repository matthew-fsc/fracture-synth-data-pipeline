"""
Dataset Balancer for Training Data Optimization

Balances training datasets across industries, complexity levels, and other dimensions
to ensure optimal distribution for model training.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from collections import Counter, defaultdict
import pandas as pd
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class BalancingStrategy(str, Enum):
    """Strategies for dataset balancing."""
    EQUAL_DISTRIBUTION = "equal_distribution"
    WEIGHTED_BY_PRIORITY = "weighted_by_priority"
    PROPORTIONAL_TO_GAPS = "proportional_to_gaps"
    DIVERSITY_FOCUSED = "diversity_focused"


class BalanceReport(BaseModel):
    """Report on dataset balance."""
    report_id: str
    dimension: str
    balance_score: float = Field(ge=0.0, le=1.0, description="Balance score (1.0 = perfectly balanced)")
    distribution: Dict[str, int] = Field(default_factory=dict)
    target_distribution: Dict[str, int] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class DatasetBalancer:
    """
    Balances training datasets across multiple dimensions.
    
    Analyzes dataset distribution and recommends rebalancing strategies
    to optimize training data quality.
    """
    
    def __init__(
        self,
        strategy: BalancingStrategy = BalancingStrategy.EQUAL_DISTRIBUTION,
        target_balance_score: float = 0.8
    ):
        """
        Initialize dataset balancer.
        
        Args:
            strategy: Balancing strategy to use
            target_balance_score: Target balance score (0-1)
        """
        self.strategy = strategy
        self.target_balance_score = target_balance_score
    
    def analyze_balance(
        self,
        datasets: List[Dict[str, Any]],
        dimensions: Optional[List[str]] = None
    ) -> List[BalanceReport]:
        """
        Analyze balance across dimensions.
        
        Args:
            datasets: List of dataset dictionaries
            dimensions: Optional list of dimensions to analyze
            
        Returns:
            List of balance reports
        """
        if dimensions is None:
            dimensions = ["industry", "complexity", "scenario_type"]
        
        reports = []
        
        for dimension in dimensions:
            report = self._analyze_dimension(datasets, dimension)
            if report:
                reports.append(report)
        
        return reports
    
    def _analyze_dimension(
        self,
        datasets: List[Dict[str, Any]],
        dimension: str
    ) -> Optional[BalanceReport]:
        """Analyze balance for a specific dimension."""
        distribution = self._extract_distribution(datasets, dimension)
        
        if not distribution:
            return None
        
        total = sum(distribution.values())
        if total == 0:
            return None
        
        # Calculate balance score (using coefficient of variation)
        counts = list(distribution.values())
        mean_count = sum(counts) / len(counts) if counts else 0
        variance = sum((c - mean_count) ** 2 for c in counts) / len(counts) if counts else 0
        std_dev = variance ** 0.5
        
        cv = std_dev / mean_count if mean_count > 0 else 1.0
        balance_score = max(0.0, 1.0 - min(cv, 1.0))  # Inverse of CV, capped at 1.0
        
        # Calculate target distribution based on strategy
        target_distribution = self._calculate_target_distribution(distribution, total)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(distribution, target_distribution, dimension)
        
        report = BalanceReport(
            report_id=f"balance_{dimension}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            dimension=dimension,
            balance_score=balance_score,
            distribution=distribution,
            target_distribution=target_distribution,
            recommendations=recommendations
        )
        
        return report
    
    def _extract_distribution(
        self,
        datasets: List[Dict[str, Any]],
        dimension: str
    ) -> Dict[str, int]:
        """Extract distribution for a dimension."""
        distribution = Counter()
        
        for dataset in datasets:
            version_data = dataset.get("version", {})
            metadata = version_data.get("metadata", {})
            
            if dimension == "industry":
                company_profile = metadata.get("company_profile", {})
                industry = company_profile.get("industry", "Unknown")
                distribution[industry] += 1
            
            elif dimension == "complexity":
                system_manifest = metadata.get("system_manifest", {})
                complexity = system_manifest.get("complexity_score", 0.5)
                # Bucket complexity
                if complexity < 0.33:
                    bucket = "low"
                elif complexity < 0.66:
                    bucket = "medium"
                else:
                    bucket = "high"
                distribution[bucket] += 1
            
            elif dimension == "scenario_type":
                # Placeholder - would need scenario type in metadata
                distribution["general"] += 1
            
            else:
                # Generic dimension
                value = metadata.get(dimension, "unknown")
                distribution[str(value)] += 1
        
        return dict(distribution)
    
    def _calculate_target_distribution(
        self,
        current_distribution: Dict[str, int],
        total: int
    ) -> Dict[str, int]:
        """Calculate target distribution based on strategy."""
        if self.strategy == BalancingStrategy.EQUAL_DISTRIBUTION:
            # Equal distribution
            num_categories = len(current_distribution)
            target_per_category = total // num_categories if num_categories > 0 else 0
            remainder = total % num_categories
            
            target = {
                category: target_per_category + (1 if i < remainder else 0)
                for i, category in enumerate(current_distribution.keys())
            }
            return target
        
        elif self.strategy == BalancingStrategy.WEIGHTED_BY_PRIORITY:
            # Weighted distribution (would need priority weights)
            # For now, use current distribution as baseline
            return current_distribution.copy()
        
        elif self.strategy == BalancingStrategy.DIVERSITY_FOCUSED:
            # Encourage diversity (slightly more equal)
            return self._calculate_target_distribution(
                current_distribution, total
            )  # Same as equal for now
        
        else:
            # Default: keep current
            return current_distribution.copy()
    
    def _generate_recommendations(
        self,
        current: Dict[str, int],
        target: Dict[str, int],
        dimension: str
    ) -> List[str]:
        """Generate recommendations for rebalancing."""
        recommendations = []
        
        for category in current.keys():
            current_count = current.get(category, 0)
            target_count = target.get(category, 0)
            diff = target_count - current_count
            
            if diff > 0:
                recommendations.append(
                    f"Generate {diff} more samples for {dimension}={category}"
                )
            elif diff < 0:
                recommendations.append(
                    f"Consider reducing samples for {dimension}={category} (currently {current_count}, target {target_count})"
                )
        
        if not recommendations:
            recommendations.append(f"Distribution for {dimension} is well-balanced")
        
        return recommendations
    
    def balance_dataset(
        self,
        datasets: List[Dict[str, Any]],
        target_size: Optional[int] = None,
        dimensions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate balancing plan for dataset.
        
        Args:
            datasets: Current datasets
            target_size: Optional target dataset size
            dimensions: Dimensions to balance
            
        Returns:
            Balancing plan dictionary
        """
        if dimensions is None:
            dimensions = ["industry", "complexity"]
        
        reports = self.analyze_balance(datasets, dimensions)
        
        # Aggregate recommendations
        all_recommendations = []
        for report in reports:
            all_recommendations.extend(report.recommendations)
        
        # Calculate overall balance score
        overall_score = sum(r.balance_score for r in reports) / len(reports) if reports else 0.0
        
        plan = {
            "overall_balance_score": overall_score,
            "dimension_reports": [r.dict() for r in reports],
            "recommendations": all_recommendations,
            "needs_balancing": overall_score < self.target_balance_score,
            "target_balance_score": self.target_balance_score
        }
        
        return plan
    
    def prioritize_for_balancing(
        self,
        datasets: List[Dict[str, Any]],
        dimensions: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Prioritize datasets for balancing (identify what to generate more of).
        
        Args:
            datasets: Current datasets
            dimensions: Dimensions to consider
            
        Returns:
            List of prioritized generation targets
        """
        reports = self.analyze_balance(datasets, dimensions)
        
        priorities = []
        
        for report in reports:
            for category in report.distribution.keys():
                current = report.distribution[category]
                target = report.target_distribution.get(category, current)
                diff = target - current
                
                if diff > 0:
                    priorities.append({
                        "dimension": report.dimension,
                        "category": category,
                        "current_count": current,
                        "target_count": target,
                        "needed": diff,
                        "priority": "high" if diff > 5 else "medium"
                    })
        
        # Sort by priority and needed count
        priorities.sort(key=lambda x: (x["priority"] == "high", x["needed"]), reverse=True)
        
        return priorities

