"""
Targeted Generator for Gap Filling

Generates synthetic data targeted at specific gaps identified in training datasets.
Creates focused datasets to fill coverage gaps.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

from .gap_detector import Gap, GapType, GapDetector

logger = logging.getLogger(__name__)


class GenerationTarget(BaseModel):
    """Target for targeted data generation."""
    target_id: str
    gap: Gap
    generation_params: Dict[str, Any] = Field(default_factory=dict)
    target_count: int = Field(ge=1, description="Number of samples to generate")
    priority: str = Field(description="Priority level")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TargetedGenerator:
    """
    Generates synthetic data targeted at specific gaps.
    
    Uses gap analysis results to generate focused synthetic datasets
    that fill identified coverage gaps.
    """
    
    def __init__(self, gap_detector: Optional[GapDetector] = None):
        """
        Initialize targeted generator.
        
        Args:
            gap_detector: Gap detector instance (creates new if None)
        """
        self.gap_detector = gap_detector or GapDetector()
    
    def create_generation_targets(
        self,
        gaps: List[Gap],
        max_targets: int = 10
    ) -> List[GenerationTarget]:
        """
        Create generation targets from gaps.
        
        Args:
            gaps: List of gaps to target
            max_targets: Maximum number of targets to create
            
        Returns:
            List of generation targets
        """
        targets = []
        
        # Sort gaps by priority and size
        sorted_gaps = sorted(
            gaps,
            key=lambda g: (
                g.priority.value,
                g.gap_size
            ),
            reverse=True
        )
        
        # Create targets for top gaps
        for gap in sorted_gaps[:max_targets]:
            target = self._create_target_from_gap(gap)
            targets.append(target)
        
        return targets
    
    def _create_target_from_gap(self, gap: Gap) -> GenerationTarget:
        """Create a generation target from a gap."""
        generation_params = {}
        target_count = 5  # Default
        
        if gap.gap_type == GapType.INDUSTRY_COVERAGE:
            generation_params = {
                "industry": gap.attributes.get("industry"),
                "target_coverage": gap.target_coverage
            }
            target_count = max(1, int(gap.gap_size * 20))  # Scale by gap size
        
        elif gap.gap_type == GapType.COMPLEXITY_LEVEL:
            generation_params = {
                "complexity_level": gap.attributes.get("complexity_level"),
                "complexity_range": gap.attributes.get("range", "0.33-0.66")
            }
            target_count = max(1, int(gap.gap_size * 15))
        
        elif gap.gap_type == GapType.FAILURE_CASE:
            generation_params = {
                "include_failures": True,
                "failure_rate": 0.3
            }
            target_count = 10  # Generate more failure cases
        
        elif gap.gap_type == GapType.EDGE_CASE:
            generation_params = {
                "include_edge_cases": True,
                "edge_case_metrics": gap.attributes.get("edge_case_count", [])
            }
            target_count = 8
        
        elif gap.gap_type == GapType.METRIC_RANGE:
            generation_params = {
                "metric": gap.attributes.get("metric"),
                "target_variance": 0.5,
                "increase_diversity": True
            }
            target_count = max(1, int(gap.gap_size * 12))
        
        else:
            generation_params = gap.attributes.copy()
            target_count = 5
        
        target = GenerationTarget(
            target_id=f"target_{gap.gap_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            gap=gap,
            generation_params=generation_params,
            target_count=target_count,
            priority=gap.priority.value
        )
        
        return target
    
    def generate_targeted_data(
        self,
        target: GenerationTarget,
        company_profiler: Any,
        scenario_generator: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate targeted data for a specific target.
        
        Args:
            target: Generation target
            company_profiler: Company profiler instance
            scenario_generator: Optional scenario generator instance
            
        Returns:
            List of generated company profiles/scenarios
        """
        generated_data = []
        
        gap_type = target.gap.gap_type
        params = target.generation_params
        
        for i in range(target.target_count):
            if gap_type == GapType.INDUSTRY_COVERAGE:
                # Generate for specific industry
                industry = params.get("industry", "Technology")
                profile = company_profiler.generate_profile(industry=industry)
                generated_data.append(profile.dict())
            
            elif gap_type == GapType.COMPLEXITY_LEVEL:
                # Generate with specific complexity
                complexity_level = params.get("complexity_level", "medium")
                industry = params.get("industry", "Technology")
                profile = company_profiler.generate_profile(industry=industry)
                # Note: Complexity would be set in manifest builder
                generated_data.append(profile.dict())
            
            elif gap_type == GapType.FAILURE_CASE:
                # Generate with failure cases
                industry = params.get("industry", "Technology")
                profile = company_profiler.generate_profile(industry=industry)
                # Enhance with failure patterns
                metrics = profile.operational_metrics
                # Increase failure rates
                if hasattr(metrics, 'handoff_failure_rate'):
                    metrics.handoff_failure_rate = min(1.0, metrics.handoff_failure_rate * 1.5)
                if hasattr(metrics, 'sla_breach_rate'):
                    metrics.sla_breach_rate = min(1.0, metrics.sla_breach_rate * 1.5)
                generated_data.append(profile.dict())
            
            elif gap_type == GapType.EDGE_CASE:
                # Generate edge cases (extreme values)
                industry = params.get("industry", "Technology")
                profile = company_profiler.generate_profile(industry=industry)
                # Apply edge case values
                metrics = profile.operational_metrics
                # Multiply certain metrics by large factors
                if hasattr(metrics, 'ticket_volume_daily'):
                    metrics.ticket_volume_daily = int(metrics.ticket_volume_daily * 3)
                generated_data.append(profile.dict())
            
            elif gap_type == GapType.METRIC_RANGE:
                # Generate with diverse metric values
                industry = params.get("industry", "Technology")
                profile = company_profiler.generate_profile(industry=industry)
                # Apply diverse values (would need more sophisticated logic)
                generated_data.append(profile.dict())
            
            else:
                # Generic generation
                industry = params.get("industry", "Technology")
                profile = company_profiler.generate_profile(industry=industry)
                generated_data.append(profile.dict())
        
        logger.info(f"Generated {len(generated_data)} samples for target {target.target_id}")
        
        return generated_data
    
    def generate_for_gaps(
        self,
        gaps: List[Gap],
        company_profiler: Any,
        max_samples_per_gap: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate data for multiple gaps.
        
        Args:
            gaps: List of gaps to fill
            company_profiler: Company profiler instance
            max_samples_per_gap: Maximum samples per gap
            
        Returns:
            Dictionary mapping gap IDs to generated data
        """
        results = {}
        
        targets = self.create_generation_targets(gaps, max_targets=len(gaps))
        
        for target in targets:
            # Limit target count
            target.target_count = min(target.target_count, max_samples_per_gap)
            
            generated_data = self.generate_targeted_data(
                target=target,
                company_profiler=company_profiler
            )
            
            results[target.gap.gap_id] = generated_data
        
        return results

