"""
Scenario Enhancer for Real-World Pattern Integration

Enhances synthetic scenarios with real-world patterns to improve realism
and diversity. Incorporates failure cases, edge cases, and common patterns.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import random

from pydantic import BaseModel, Field

from .pattern_extractor import Pattern, PatternType, PatternExtractor

logger = logging.getLogger(__name__)


class EnhancementStrategy(str, Enum):
    """Strategies for scenario enhancement."""
    ADD_PAIN_POINTS = "add_pain_points"
    ADD_FAILURE_CASES = "add_failure_cases"
    ADD_EDGE_CASES = "add_edge_cases"
    APPLY_OPERATIONAL_PATTERNS = "apply_operational_patterns"
    DIVERSIFY_METRICS = "diversify_metrics"
    COMBINE_PATTERNS = "combine_patterns"


class ScenarioEnhancer:
    """
    Enhances synthetic scenarios with real-world patterns.
    
    Uses extracted patterns to make synthetic data more realistic and diverse
    by incorporating common patterns, failure cases, and edge cases.
    """
    
    def __init__(
        self,
        pattern_extractor: Optional[PatternExtractor] = None,
        enhancement_probability: float = 0.7
    ):
        """
        Initialize scenario enhancer.
        
        Args:
            pattern_extractor: Pattern extractor instance (creates new if None)
            enhancement_probability: Probability of applying enhancements (0-1)
        """
        self.pattern_extractor = pattern_extractor or PatternExtractor()
        self.enhancement_probability = enhancement_probability
    
    def enhance_company_profile(
        self,
        company_profile: Dict[str, Any],
        strategies: Optional[List[EnhancementStrategy]] = None,
        pattern_types: Optional[List[PatternType]] = None
    ) -> Dict[str, Any]:
        """
        Enhance a company profile with real-world patterns.
        
        Args:
            company_profile: Company profile dictionary to enhance
            strategies: List of enhancement strategies to apply
            pattern_types: Optional list of pattern types to use
            
        Returns:
            Enhanced company profile dictionary
        """
        if strategies is None:
            strategies = [
                EnhancementStrategy.ADD_PAIN_POINTS,
                EnhancementStrategy.APPLY_OPERATIONAL_PATTERNS,
                EnhancementStrategy.DIVERSIFY_METRICS
            ]
        
        enhanced_profile = company_profile.copy()
        
        # Apply each strategy
        for strategy in strategies:
            if random.random() > self.enhancement_probability:
                continue
            
            if strategy == EnhancementStrategy.ADD_PAIN_POINTS:
                enhanced_profile = self._add_pain_points(enhanced_profile, pattern_types)
            elif strategy == EnhancementStrategy.APPLY_OPERATIONAL_PATTERNS:
                enhanced_profile = self._apply_operational_patterns(enhanced_profile, pattern_types)
            elif strategy == EnhancementStrategy.DIVERSIFY_METRICS:
                enhanced_profile = self._diversify_metrics(enhanced_profile, pattern_types)
            elif strategy == EnhancementStrategy.ADD_FAILURE_CASES:
                enhanced_profile = self._add_failure_cases(enhanced_profile, pattern_types)
            elif strategy == EnhancementStrategy.ADD_EDGE_CASES:
                enhanced_profile = self._add_edge_cases(enhanced_profile, pattern_types)
        
        return enhanced_profile
    
    def enhance_scenario(
        self,
        scenario: Dict[str, Any],
        strategies: Optional[List[EnhancementStrategy]] = None,
        pattern_types: Optional[List[PatternType]] = None
    ) -> Dict[str, Any]:
        """
        Enhance a requirement scenario with real-world patterns.
        
        Args:
            scenario: Scenario dictionary to enhance
            strategies: List of enhancement strategies to apply
            pattern_types: Optional list of pattern types to use
            
        Returns:
            Enhanced scenario dictionary
        """
        if strategies is None:
            strategies = [
                EnhancementStrategy.ADD_PAIN_POINTS,
                EnhancementStrategy.ADD_FAILURE_CASES
            ]
        
        enhanced_scenario = scenario.copy()
        
        for strategy in strategies:
            if random.random() > self.enhancement_probability:
                continue
            
            if strategy == EnhancementStrategy.ADD_PAIN_POINTS:
                enhanced_scenario = self._add_scenario_pain_points(enhanced_scenario, pattern_types)
            elif strategy == EnhancementStrategy.ADD_FAILURE_CASES:
                enhanced_scenario = self._add_scenario_failure_cases(enhanced_scenario, pattern_types)
        
        return enhanced_scenario
    
    def _add_pain_points(
        self,
        profile: Dict[str, Any],
        pattern_types: Optional[List[PatternType]]
    ) -> Dict[str, Any]:
        """Add pain points based on patterns."""
        pain_patterns = self.pattern_extractor.get_patterns(
            pattern_type=PatternType.PAIN_POINT,
            min_confidence=0.6
        )
        
        if not pain_patterns:
            return profile
        
        # Get existing pain points
        existing_pain_points = profile.get("pain_points", [])
        
        # Add new pain points from patterns (up to 3)
        new_pain_points = []
        for pattern in random.sample(pain_patterns, min(3, len(pain_patterns))):
            keyword = pattern.attributes.get("keyword", pattern.pattern_name)
            if keyword not in existing_pain_points:
                new_pain_points.append(keyword)
        
        profile["pain_points"] = existing_pain_points + new_pain_points[:3]
        
        return profile
    
    def _apply_operational_patterns(
        self,
        profile: Dict[str, Any],
        pattern_types: Optional[List[PatternType]]
    ) -> Dict[str, Any]:
        """Apply operational metric patterns."""
        op_patterns = self.pattern_extractor.get_patterns(
            pattern_type=PatternType.OPERATIONAL_METRIC,
            min_confidence=0.7
        )
        
        if not op_patterns or "operational_metrics" not in profile:
            return profile
        
        metrics = profile["operational_metrics"].copy()
        
        # Apply patterns to metrics (adjust values based on patterns)
        for pattern in random.sample(op_patterns, min(2, len(op_patterns))):
            column = pattern.attributes.get("column", "")
            if not column:
                continue
            
            # Map column names to metric fields (simplified mapping)
            metric_field = self._map_column_to_metric(column)
            if metric_field and metric_field in metrics:
                # Adjust metric based on pattern statistics
                mean_val = pattern.attributes.get("mean", metrics[metric_field])
                # Add some variation but keep it realistic
                metrics[metric_field] = max(0, mean_val * random.uniform(0.8, 1.2))
        
        profile["operational_metrics"] = metrics
        
        return profile
    
    def _diversify_metrics(
        self,
        profile: Dict[str, Any],
        pattern_types: Optional[List[PatternType]]
    ) -> Dict[str, Any]:
        """Diversify metrics using edge case patterns."""
        edge_patterns = self.pattern_extractor.get_patterns(
            pattern_type=PatternType.EDGE_CASE,
            min_confidence=0.6
        )
        
        if not edge_patterns or "operational_metrics" not in profile:
            return profile
        
        metrics = profile["operational_metrics"].copy()
        
        # Occasionally use edge case values (20% probability)
        if random.random() < 0.2:
            pattern = random.choice(edge_patterns)
            column = pattern.attributes.get("column", "")
            metric_field = self._map_column_to_metric(column)
            
            if metric_field and metric_field in metrics:
                # Use outlier value
                min_outlier = pattern.attributes.get("min_outlier")
                max_outlier = pattern.attributes.get("max_outlier")
                
                if min_outlier is not None or max_outlier is not None:
                    outlier_val = min_outlier if min_outlier else max_outlier
                    metrics[metric_field] = max(0, outlier_val * random.uniform(0.9, 1.1))
        
        profile["operational_metrics"] = metrics
        
        return profile
    
    def _add_failure_cases(
        self,
        profile: Dict[str, Any],
        pattern_types: Optional[List[PatternType]]
    ) -> Dict[str, Any]:
        """Add failure case patterns."""
        failure_patterns = self.pattern_extractor.get_patterns(
            pattern_type=PatternType.FAILURE_CASE,
            min_confidence=0.6
        )
        
        if not failure_patterns or "operational_metrics" not in profile:
            return profile
        
        metrics = profile["operational_metrics"].copy()
        
        # Apply failure patterns (30% probability)
        if random.random() < 0.3:
            pattern = random.choice(failure_patterns)
            column = pattern.attributes.get("column", "")
            metric_field = self._map_column_to_metric(column)
            
            if metric_field and metric_field in metrics:
                # Increase failure rate/metric based on pattern
                failure_rate = pattern.attributes.get("failure_rate", 0.0)
                avg_failures = pattern.attributes.get("avg_failures", 0.0)
                
                if "rate" in metric_field.lower() or "failure" in metric_field.lower():
                    metrics[metric_field] = min(1.0, metrics[metric_field] + failure_rate * 0.5)
                else:
                    metrics[metric_field] = max(metrics[metric_field], avg_failures)
        
        profile["operational_metrics"] = metrics
        
        return profile
    
    def _add_edge_cases(
        self,
        profile: Dict[str, Any],
        pattern_types: Optional[List[PatternType]]
    ) -> Dict[str, Any]:
        """Add edge case patterns (extreme values)."""
        edge_patterns = self.pattern_extractor.get_patterns(
            pattern_type=PatternType.EDGE_CASE,
            min_confidence=0.6
        )
        
        if not edge_patterns:
            return profile
        
        # Edge cases applied in diversify_metrics
        # This is a placeholder for additional edge case logic
        return profile
    
    def _add_scenario_pain_points(
        self,
        scenario: Dict[str, Any],
        pattern_types: Optional[List[PatternType]]
    ) -> Dict[str, Any]:
        """Add pain points to scenario."""
        pain_patterns = self.pattern_extractor.get_patterns(
            pattern_type=PatternType.PAIN_POINT,
            min_confidence=0.6
        )
        
        if not pain_patterns:
            return scenario
        
        existing_pain_points = scenario.get("pain_points", [])
        new_pain_points = []
        
        for pattern in random.sample(pain_patterns, min(2, len(pain_patterns))):
            keyword = pattern.attributes.get("keyword", pattern.pattern_name)
            if keyword not in existing_pain_points:
                new_pain_points.append(keyword)
        
        scenario["pain_points"] = existing_pain_points + new_pain_points[:2]
        
        return scenario
    
    def _add_scenario_failure_cases(
        self,
        scenario: Dict[str, Any],
        pattern_types: Optional[List[PatternType]]
    ) -> Dict[str, Any]:
        """Add failure case context to scenario."""
        failure_patterns = self.pattern_extractor.get_patterns(
            pattern_type=PatternType.FAILURE_CASE,
            min_confidence=0.6
        )
        
        if failure_patterns and random.random() < 0.3:
            pattern = random.choice(failure_patterns)
            # Add failure context to business context
            business_context = scenario.get("business_context", "")
            failure_desc = f" Note: {pattern.description}"
            scenario["business_context"] = business_context + failure_desc
        
        return scenario
    
    def _map_column_to_metric(self, column: str) -> Optional[str]:
        """Map dataset column name to company profile metric field."""
        column_lower = column.lower()
        
        mapping = {
            'ticket_volume': 'ticket_volume_daily',
            'handoff_delay': 'handoff_delay_avg_hours',
            'failure_rate': 'handoff_failure_rate',
            'stall': 'workflow_stall_count',
            'compliance': 'compliance_failures_monthly',
            'advisor': 'advisor_count',
            'sla': 'sla_breach_rate'
        }
        
        for key, metric_field in mapping.items():
            if key in column_lower:
                return metric_field
        
        return None
    
    def generate_failure_scenarios(
        self,
        base_scenario: Dict[str, Any],
        count: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Generate failure case scenarios from a base scenario.
        
        Args:
            base_scenario: Base scenario to enhance
            count: Number of failure scenarios to generate
            
        Returns:
            List of failure scenario dictionaries
        """
        failure_patterns = self.pattern_extractor.get_patterns(
            pattern_type=PatternType.FAILURE_CASE,
            min_confidence=0.6
        )
        
        failure_scenarios = []
        
        for i in range(count):
            scenario = base_scenario.copy()
            scenario["scenario_id"] = f"{base_scenario.get('scenario_id', 'scenario')}_failure_{i+1}"
            
            if failure_patterns:
                pattern = random.choice(failure_patterns)
                scenario["business_context"] = (
                    f"{scenario.get('business_context', '')} "
                    f"[FAILURE CASE: {pattern.description}]"
                )
                scenario["urgency_level"] = "high"  # Failure cases are typically high urgency
            
            failure_scenarios.append(scenario)
        
        return failure_scenarios
    
    def generate_edge_case_scenarios(
        self,
        base_profile: Dict[str, Any],
        count: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Generate edge case scenarios from a base profile.
        
        Args:
            base_profile: Base company profile
            count: Number of edge case scenarios to generate
            
        Returns:
            List of edge case profile dictionaries
        """
        edge_patterns = self.pattern_extractor.get_patterns(
            pattern_type=PatternType.EDGE_CASE,
            min_confidence=0.6
        )
        
        edge_case_profiles = []
        
        for i in range(count):
            profile = base_profile.copy()
            profile["company_id"] = f"{base_profile.get('company_id', 'company')}_edge_{i+1}"
            
            if edge_patterns and "operational_metrics" in profile:
                metrics = profile["operational_metrics"].copy()
                
                # Apply edge case values
                for pattern in random.sample(edge_patterns, min(2, len(edge_patterns))):
                    column = pattern.attributes.get("column", "")
                    metric_field = self._map_column_to_metric(column)
                    
                    if metric_field and metric_field in metrics:
                        max_outlier = pattern.attributes.get("max_outlier")
                        if max_outlier is not None:
                            metrics[metric_field] = max_outlier * random.uniform(0.9, 1.1)
                
                profile["operational_metrics"] = metrics
            
            edge_case_profiles.append(profile)
        
        return edge_case_profiles

