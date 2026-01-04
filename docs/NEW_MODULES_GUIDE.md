# New Modules Guide - Pipeline Manager Enhancements

This guide covers the new modules added for enhanced data generation, gap analysis, and data optimization.

## Overview

Three new module groups have been added:

1. **Real-World Integration** (`src/realworld_integration/`)
   - Pattern extraction from real-world data
   - Scenario enhancement with real-world patterns
   - Failure case and edge case generation

2. **Gap Analysis** (`src/gap_analysis/`)
   - Training data gap detection
   - Targeted data generation for gaps
   - Coverage analysis

3. **Data Optimization** (`src/data_optimization/`)
   - Dataset balancing across dimensions
   - Priority scoring for training data
   - High-value scenario identification

## Real-World Integration

### Pattern Extractor

Extracts patterns from real-world data sources:

```python
from src.realworld_integration import PatternExtractor, PatternType

extractor = PatternExtractor()

# Extract patterns from datasets
import pandas as pd
datasets = [pd.read_csv("data/real_data.csv")]
patterns = extractor.extract_from_datasets(
    datasets=datasets,
    pattern_types=[PatternType.OPERATIONAL_METRIC, PatternType.PAIN_POINT]
)

# Extract patterns from transcripts
transcripts = ["transcript text 1", "transcript text 2"]
patterns = extractor.extract_from_transcripts(transcripts)

# Get stored patterns
operational_patterns = extractor.get_patterns(
    pattern_type=PatternType.OPERATIONAL_METRIC,
    min_confidence=0.7
)
```

### Scenario Enhancer

Enhances synthetic scenarios with real-world patterns:

```python
from src.realworld_integration import ScenarioEnhancer, EnhancementStrategy

enhancer = ScenarioEnhancer(pattern_extractor=extractor)

# Enhance company profile
company_profile = {...}  # Your company profile dict
enhanced_profile = enhancer.enhance_company_profile(
    company_profile=company_profile,
    strategies=[
        EnhancementStrategy.ADD_PAIN_POINTS,
        EnhancementStrategy.APPLY_OPERATIONAL_PATTERNS
    ]
)

# Enhance scenario
scenario = {...}  # Your scenario dict
enhanced_scenario = enhancer.enhance_scenario(scenario)

# Generate failure cases
failure_scenarios = enhancer.generate_failure_scenarios(
    base_scenario=scenario,
    count=3
)

# Generate edge cases
edge_case_profiles = enhancer.generate_edge_case_scenarios(
    base_profile=company_profile,
    count=2
)
```

## Gap Analysis

### Gap Detector

Identifies gaps in training datasets:

```python
from src.gap_analysis import GapDetector, GapType, GapPriority

detector = GapDetector(
    min_coverage_threshold=0.1,
    target_coverage=0.8
)

# Detect gaps
datasets = [...]  # Your dataset dictionaries
gaps = detector.detect_gaps(
    datasets=datasets,
    gap_types=[
        GapType.INDUSTRY_COVERAGE,
        GapType.COMPLEXITY_LEVEL,
        GapType.FAILURE_CASE
    ]
)

# Get gaps by priority
critical_gaps = detector.get_gaps(
    priority=GapPriority.CRITICAL,
    min_gap_size=0.3
)

# Analyze specific gap types
industry_gaps = detector.get_gaps(gap_type=GapType.INDUSTRY_COVERAGE)
```

### Targeted Generator

Generates data targeted at specific gaps:

```python
from src.gap_analysis import TargetedGenerator
from src.company_profiler import CompanyProfiler

generator = TargetedGenerator(gap_detector=detector)
profiler = CompanyProfiler(...)

# Create generation targets from gaps
targets = generator.create_generation_targets(gaps, max_targets=10)

# Generate targeted data for a specific target
target = targets[0]
generated_data = generator.generate_targeted_data(
    target=target,
    company_profiler=profiler
)

# Generate data for multiple gaps
results = generator.generate_for_gaps(
    gaps=critical_gaps,
    company_profiler=profiler,
    max_samples_per_gap=10
)
```

## Data Optimization

### Dataset Balancer

Balances datasets across dimensions:

```python
from src.data_optimization import DatasetBalancer, BalancingStrategy

balancer = DatasetBalancer(
    strategy=BalancingStrategy.EQUAL_DISTRIBUTION,
    target_balance_score=0.8
)

# Analyze balance
datasets = [...]  # Your datasets
reports = balancer.analyze_balance(
    datasets=datasets,
    dimensions=["industry", "complexity"]
)

# Get balancing plan
plan = balancer.balance_dataset(
    datasets=datasets,
    target_size=1000,
    dimensions=["industry", "complexity"]
)

print(f"Overall balance score: {plan['overall_balance_score']:.2f}")
print(f"Needs balancing: {plan['needs_balancing']}")

# Prioritize for balancing
priorities = balancer.prioritize_for_balancing(
    datasets=datasets,
    dimensions=["industry"]
)

for priority in priorities:
    print(f"Generate {priority['needed']} more for {priority['dimension']}={priority['category']}")
```

### Priority Scorer

Scores and prioritizes training data:

```python
from src.data_optimization import PriorityScorer, ScoringCriteria

scorer = PriorityScorer(
    criteria_weights={
        ScoringCriteria.QUALITY: 0.3,
        ScoringCriteria.DIVERSITY: 0.25,
        ScoringCriteria.COMPLEXITY: 0.2,
        ScoringCriteria.BUSINESS_VALUE: 0.15,
        ScoringCriteria.RARITY: 0.10
    }
)

# Score samples
scores = scorer.score_samples(datasets)

# Get high-priority samples
high_priority = scorer.get_high_priority_samples(
    scores=scores,
    top_n=20,
    min_score=0.7
)

# Identify high-value scenarios
scenarios = scorer.identify_high_value_scenarios(
    datasets=datasets,
    top_n=20
)

for scenario in scenarios:
    print(f"Industry: {scenario['industry']}, Score: {scenario['priority_score']:.2f}")
```

## Complete Workflow Example

```python
from src.realworld_integration import PatternExtractor, ScenarioEnhancer
from src.gap_analysis import GapDetector, TargetedGenerator
from src.data_optimization import DatasetBalancer, PriorityScorer
from src.dataset_registry_enhanced import EnhancedDatasetRegistry

# 1. Extract patterns from real data
extractor = PatternExtractor()
patterns = extractor.extract_from_datasets(real_datasets)

# 2. Detect gaps in training data
registry = EnhancedDatasetRegistry()
datasets = registry.list_all_datasets()

detector = GapDetector()
gaps = detector.detect_gaps(datasets)

# 3. Generate targeted data for gaps
generator = TargetedGenerator(detector)
targets = generator.create_generation_targets(gaps)

# Generate data for each target
for target in targets[:5]:  # Top 5 gaps
    generated = generator.generate_targeted_data(target, profiler)
    # Register generated data...

# 4. Enhance scenarios with real-world patterns
enhancer = ScenarioEnhancer(extractor)
enhanced_profiles = [
    enhancer.enhance_company_profile(profile)
    for profile in generated_profiles
]

# 5. Balance dataset
balancer = DatasetBalancer()
plan = balancer.balance_dataset(datasets)
if plan["needs_balancing"]:
    priorities = balancer.prioritize_for_balancing(datasets)
    # Generate more data based on priorities...

# 6. Score and prioritize
scorer = PriorityScorer()
scores = scorer.score_samples(datasets)
high_value = scorer.get_high_priority_samples(scores, top_n=50)

# 7. Generate more of high-value scenarios
for score in high_value[:10]:
    # Generate similar high-value scenarios...
    pass
```

## Integration with Pipeline

These modules can be integrated into the main pipeline:

```python
from src.pipeline import synthetic_data_generation_flow
from src.realworld_integration import ScenarioEnhancer

# Enhance pipeline output
enhancer = ScenarioEnhancer()

# In pipeline, enhance generated profiles
enhanced_profile = enhancer.enhance_company_profile(
    company_profile=company_profile.dict(),
    strategies=[EnhancementStrategy.ADD_PAIN_POINTS]
)
```

## Next Steps

1. **Pattern Extraction**: Feed real-world data to extract patterns
2. **Gap Analysis**: Run gap detection on existing datasets
3. **Targeted Generation**: Generate data to fill identified gaps
4. **Enhancement**: Use real-world patterns to enhance synthetic data
5. **Balancing**: Balance datasets for optimal training
6. **Prioritization**: Identify and generate high-value scenarios

## Notes

- Pattern extraction requires real-world data sources
- Gap detection works best with a substantial dataset (50+ samples)
- Enhancement strategies can be combined for maximum effect
- Balancing should be done periodically as datasets grow
- Priority scoring helps focus generation efforts on high-value data

