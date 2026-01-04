"""
Priority Scorer for Training Data Optimization

Scores and prioritizes training data samples based on value, quality, and training needs.
Identifies high-value scenarios for targeted data generation.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ScoringCriteria(str, Enum):
    """Criteria for priority scoring."""
    QUALITY = "quality"
    DIVERSITY = "diversity"
    RARITY = "rarity"
    COMPLEXITY = "complexity"
    BUSINESS_VALUE = "business_value"
    TRAINING_GAP = "training_gap"


class PriorityScore(BaseModel):
    """Priority score for a dataset sample."""
    sample_id: str
    overall_score: float = Field(ge=0.0, le=1.0, description="Overall priority score (0-1)")
    criteria_scores: Dict[str, float] = Field(default_factory=dict)
    rank: Optional[int] = None
    scored_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PriorityScorer:
    """
    Scores and prioritizes training data samples.
    
    Evaluates samples based on multiple criteria to identify
    high-value data for training.
    """
    
    def __init__(
        self,
        criteria_weights: Optional[Dict[ScoringCriteria, float]] = None
    ):
        """
        Initialize priority scorer.
        
        Args:
            criteria_weights: Optional weights for scoring criteria (defaults to equal weights)
        """
        if criteria_weights is None:
            # Default equal weights
            self.criteria_weights = {
                ScoringCriteria.QUALITY: 0.25,
                ScoringCriteria.DIVERSITY: 0.20,
                ScoringCriteria.RARITY: 0.15,
                ScoringCriteria.COMPLEXITY: 0.15,
                ScoringCriteria.BUSINESS_VALUE: 0.15,
                ScoringCriteria.TRAINING_GAP: 0.10
            }
        else:
            # Normalize weights
            total_weight = sum(criteria_weights.values())
            self.criteria_weights = {
                k: v / total_weight
                for k, v in criteria_weights.items()
            }
    
    def score_samples(
        self,
        datasets: List[Dict[str, Any]],
        criteria: Optional[List[ScoringCriteria]] = None
    ) -> List[PriorityScore]:
        """
        Score multiple dataset samples.
        
        Args:
            datasets: List of dataset dictionaries
            criteria: Optional list of criteria to use
            
        Returns:
            List of priority scores
        """
        if criteria is None:
            criteria = list(self.criteria_weights.keys())
        
        scores = []
        
        for dataset in datasets:
            version_data = dataset.get("version", {})
            sample_id = version_data.get("sample_id", dataset.get("dataset_id", "unknown"))
            
            score = self.score_sample(dataset, criteria)
            score.sample_id = sample_id
            scores.append(score)
        
        # Rank samples
        scores.sort(key=lambda s: s.overall_score, reverse=True)
        for rank, score in enumerate(scores, start=1):
            score.rank = rank
        
        return scores
    
    def score_sample(
        self,
        dataset: Dict[str, Any],
        criteria: Optional[List[ScoringCriteria]] = None
    ) -> PriorityScore:
        """
        Score a single dataset sample.
        
        Args:
            dataset: Dataset dictionary
            criteria: Optional list of criteria to use
            
        Returns:
            Priority score
        """
        if criteria is None:
            criteria = list(self.criteria_weights.keys())
        
        criteria_scores = {}
        overall_score = 0.0
        
        version_data = dataset.get("version", {})
        metadata = version_data.get("metadata", {})
        quality_scores = version_data.get("quality_scores", {})
        
        for criterion in criteria:
            if criterion == ScoringCriteria.QUALITY:
                score = self._score_quality(quality_scores)
            elif criterion == ScoringCriteria.DIVERSITY:
                score = self._score_diversity(dataset, metadata)
            elif criterion == ScoringCriteria.RARITY:
                score = self._score_rarity(dataset, metadata)
            elif criterion == ScoringCriteria.COMPLEXITY:
                score = self._score_complexity(metadata)
            elif criterion == ScoringCriteria.BUSINESS_VALUE:
                score = self._score_business_value(metadata)
            elif criterion == ScoringCriteria.TRAINING_GAP:
                score = self._score_training_gap(dataset, metadata)
            else:
                score = 0.5  # Default neutral score
            
            criteria_scores[criterion.value] = score
            
            # Weighted contribution
            weight = self.criteria_weights.get(criterion, 0.0)
            overall_score += score * weight
        
        priority_score = PriorityScore(
            sample_id=dataset.get("dataset_id", "unknown"),
            overall_score=overall_score,
            criteria_scores=criteria_scores,
            metadata={
                "dataset_id": dataset.get("dataset_id"),
                "version": version_data.get("version")
            }
        )
        
        return priority_score
    
    def _score_quality(self, quality_scores: Dict[str, Any]) -> float:
        """Score based on quality metrics."""
        if not quality_scores:
            return 0.5
        
        # Average quality scores
        scores = [
            v for v in quality_scores.values()
            if isinstance(v, (int, float)) and 0 <= v <= 1
        ]
        
        if not scores:
            return 0.5
        
        return sum(scores) / len(scores)
    
    def _score_diversity(
        self,
        dataset: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> float:
        """Score based on diversity (uniqueness)."""
        # Simplified diversity scoring
        # Would need comparison with other datasets for true diversity
        
        company_profile = metadata.get("company_profile", {})
        industry = company_profile.get("industry", "")
        metrics = company_profile.get("operational_metrics", {})
        
        # Higher diversity if has unique combinations
        diversity_factors = [
            industry != "Technology",  # Non-default industry
            len(metrics) > 5,  # Many metrics
            len(company_profile.get("pain_points", [])) > 3  # Many pain points
        ]
        
        diversity_score = sum(diversity_factors) / len(diversity_factors) if diversity_factors else 0.5
        
        return diversity_score
    
    def _score_rarity(
        self,
        dataset: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> float:
        """Score based on rarity (how uncommon the scenario is)."""
        company_profile = metadata.get("company_profile", {})
        industry = company_profile.get("industry", "")
        metrics = company_profile.get("operational_metrics", {})
        
        # Rare scenarios have unusual combinations
        rarity_factors = []
        
        # Rare industries
        rare_industries = ["Energy", "Government", "Telecommunications"]
        if industry in rare_industries:
            rarity_factors.append(1.0)
        else:
            rarity_factors.append(0.3)
        
        # Extreme metrics (edge cases)
        if metrics:
            for key, value in metrics.items():
                if isinstance(value, (int, float)):
                    # Check if value is extreme (simplified)
                    if value > 10000 or (isinstance(value, float) and value > 0.9):
                        rarity_factors.append(0.8)
                        break
        
        rarity_score = sum(rarity_factors) / len(rarity_factors) if rarity_factors else 0.5
        
        return min(1.0, rarity_score)
    
    def _score_complexity(self, metadata: Dict[str, Any]) -> float:
        """Score based on complexity."""
        system_manifest = metadata.get("system_manifest", {})
        complexity = system_manifest.get("complexity_score", 0.5)
        
        # Higher complexity = higher priority (for training)
        # But normalize: complexity of 0.5-0.8 is most valuable
        if 0.5 <= complexity <= 0.8:
            return 1.0
        elif complexity < 0.5:
            return complexity * 2  # 0-1.0
        else:
            return 1.0 - (complexity - 0.8) * 5  # Decreasing above 0.8
    
    def _score_business_value(self, metadata: Dict[str, Any]) -> float:
        """Score based on business value."""
        company_profile = metadata.get("company_profile", {})
        
        # Factors that indicate business value
        revenue_min = company_profile.get("revenue_range_min", 0)
        employee_count = company_profile.get("employee_count", 0)
        pain_points = company_profile.get("pain_points", [])
        
        value_factors = []
        
        # Larger companies = higher value
        if revenue_min > 100000000:  # $100M+
            value_factors.append(1.0)
        elif revenue_min > 10000000:  # $10M+
            value_factors.append(0.7)
        else:
            value_factors.append(0.4)
        
        # More employees = higher value
        if employee_count > 1000:
            value_factors.append(1.0)
        elif employee_count > 100:
            value_factors.append(0.7)
        else:
            value_factors.append(0.4)
        
        # More pain points = higher value (more problems to solve)
        if len(pain_points) > 5:
            value_factors.append(1.0)
        elif len(pain_points) > 2:
            value_factors.append(0.7)
        else:
            value_factors.append(0.4)
        
        return sum(value_factors) / len(value_factors) if value_factors else 0.5
    
    def _score_training_gap(
        self,
        dataset: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> float:
        """Score based on training gap (how much this fills a gap)."""
        # Simplified: would need gap analysis results
        # For now, score based on industry rarity
        
        company_profile = metadata.get("company_profile", {})
        industry = company_profile.get("industry", "")
        
        # Rare industries fill gaps
        rare_industries = ["Energy", "Government", "Telecommunications", "Education"]
        if industry in rare_industries:
            return 1.0
        else:
            return 0.5
    
    def get_high_priority_samples(
        self,
        scores: List[PriorityScore],
        top_n: int = 10,
        min_score: float = 0.7
    ) -> List[PriorityScore]:
        """
        Get high-priority samples.
        
        Args:
            scores: List of priority scores
            top_n: Number of top samples to return
            min_score: Minimum score threshold
            
        Returns:
            List of high-priority scores
        """
        high_priority = [
            score for score in scores
            if score.overall_score >= min_score
        ]
        
        high_priority.sort(key=lambda s: s.overall_score, reverse=True)
        
        return high_priority[:top_n]
    
    def identify_high_value_scenarios(
        self,
        datasets: List[Dict[str, Any]],
        top_n: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Identify high-value scenarios for targeted generation.
        
        Args:
            datasets: List of datasets
            top_n: Number of scenarios to identify
            
        Returns:
            List of high-value scenario descriptions
        """
        scores = self.score_samples(datasets)
        high_priority = self.get_high_priority_samples(scores, top_n=top_n)
        
        scenarios = []
        
        for score in high_priority:
            # Find corresponding dataset
            dataset = next(
                (d for d in datasets if d.get("dataset_id") == score.sample_id),
                None
            )
            
            if dataset:
                version_data = dataset.get("version", {})
                metadata = version_data.get("metadata", {})
                company_profile = metadata.get("company_profile", {})
                
                scenario = {
                    "sample_id": score.sample_id,
                    "priority_score": score.overall_score,
                    "industry": company_profile.get("industry"),
                    "complexity": metadata.get("system_manifest", {}).get("complexity_score"),
                    "criteria_scores": score.criteria_scores,
                    "recommendation": "Generate similar scenarios"
                }
                scenarios.append(scenario)
        
        return scenarios

