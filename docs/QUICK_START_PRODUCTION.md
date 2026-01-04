# Quick Start Guide - Production Features

This guide provides quick examples for using the new production features added to the synthetic data pipeline.

## Azure OpenAI Service Management

Track token usage and costs for Azure OpenAI API calls:

```python
from src.llm_management import OpenAIManager, RateLimiter, RetryHandler
from src.llm_management.retry_handler import with_retry

# Initialize manager
manager = OpenAIManager(
    azure_openai_endpoint="https://your-endpoint.openai.azure.com/",
    deployment_name="gpt-4-turbo",
    key_vault_url="https://your-keyvault.vault.azure.net/"
)

# Make API calls (usage is automatically tracked)
response = manager.chat_completion(
    messages=[{"role": "user", "content": "Hello"}]
)

# Get cost summary
cost_summary = manager.get_cost_summary()
print(f"Total cost: ${cost_summary['total_cost']:.2f}")
print(f"Daily cost: ${cost_summary['daily_cost']:.2f}")
print(f"Monthly cost: ${cost_summary['monthly_cost']:.2f}")

# Get usage statistics
usage_stats = manager.get_usage_stats()
print(f"Total tokens: {usage_stats['total_tokens']}")
print(f"Total cost: ${usage_stats['total_cost']:.2f}")

# Save usage report
manager.save_usage_report()
```

### Rate Limiting

```python
from src.llm_management import RateLimiter, RateLimitConfig

# Configure rate limits
config = RateLimitConfig(
    requests_per_minute=60,
    tokens_per_minute=90000,
    requests_per_day=10000
)

limiter = RateLimiter(config)

# Before making API call
limiter.wait_if_needed(tokens=1000)  # Estimated tokens
response = manager.chat_completion(...)
limiter.record_usage(actual_tokens_used)
```

### Retry Logic

```python
from src.llm_management import RetryHandler

handler = RetryHandler(max_retries=3, base_delay=1.0)

# As decorator
@handler.retry
def my_api_call():
    return manager.chat_completion(...)

# Or execute with retry
result = handler.execute(manager.chat_completion, messages=[...])
```

## Enhanced Validation Framework

Use Great Expectations for comprehensive data quality validation:

```python
from src.validators.quality_validator_enhanced import EnhancedQualityValidator
import pandas as pd

# Initialize validator
validator = EnhancedQualityValidator()

# Create expectation suite
suite = validator.create_expectation_suite(
    suite_name="training_samples_v1",
    dataset_type="training_samples"
)

# Validate dataset
df = pd.read_csv("data/synthetic_outputs/sample.csv")
result = validator.validate_with_expectations(
    df=df,
    suite_name="training_samples_v1",
    dataset_type="training_samples"
)

print(f"Validation passed: {result.success}")
print(f"Quality score: {result.quality_score:.2f}")
print(f"Failed expectations: {len(result.failed_expectations)}")

# Get quality metrics over time
metrics = validator.get_quality_metrics(dataset_type="training_samples", days=30)
print(f"Average quality score: {metrics['avg_quality_score']:.2f}")
print(f"Trend: {metrics['trend']}")
```

## Enhanced Dataset Registry

Manage datasets with versioning and lineage:

```python
from src.dataset_registry_enhanced import EnhancedDatasetRegistry, DatasetStatus

registry = EnhancedDatasetRegistry()

# Register dataset
version_id = registry.register_dataset(
    sample_id="sample_20240101_001",
    json_path="data/synthetic_outputs/sample_20240101_001.json",
    csv_path="data/synthetic_outputs/sample_20240101_001.csv",
    quality_scores={"realism_score": 0.95, "completeness_score": 0.98},
    validation_results={
        "schema": {"all_passed": True},
        "realism": {"all_passed": True}
    },
    metadata={"industry": "Technology", "complexity": 0.75},
    created_by="pipeline"
)

print(f"Registered version: {version_id}")

# Approve dataset
registry.approve_dataset(
    dataset_id="dataset_sample_20240101_001",
    version="1.0.0",
    approved_by="admin"
)

# Search datasets
results = registry.search_datasets(
    industry="Technology",
    min_realism_score=0.9,
    status=DatasetStatus.APPROVED
)

# Get lineage
lineage = registry.get_lineage("dataset_sample_20240101_001")
print(f"Versions: {lineage['versions']}")
print(f"Parent datasets: {lineage['parent_datasets']}")
```

## Pipeline Monitoring

Monitor pipeline execution:

```python
from src.monitoring import PipelineMonitor, AppInsightsClient

# Initialize Application Insights client (optional)
app_insights = AppInsightsClient(
    connection_string="InstrumentationKey=...;IngestionEndpoint=..."
)

# Create monitor
monitor = PipelineMonitor(
    execution_id="exec_20240101_001",
    pipeline_name="synthetic-data-generation",
    app_insights_client=app_insights
)

# Track metrics during execution
monitor.record_cost(0.05)  # $0.05
monitor.record_tokens(1500)
monitor.record_samples_generated(10)
monitor.record_validation_result(True)
monitor.record_metric("custom_metric", 42)

# Mark as complete
monitor.complete(success=True)

# Get metrics
metrics = monitor.get_metrics()
print(f"Duration: {metrics.duration_seconds:.2f}s")
print(f"Cost: ${metrics.cost_usd:.2f}")
print(f"Tokens: {metrics.tokens_used}")
```

## Production Deployment

### Deploy Infrastructure

```bash
# Set variables
RESOURCE_GROUP="rg-synth-data-prod"
LOCATION="eastus"

# Deploy
az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --template-file infra/bicep/main.bicep \
  --parameters environment=prod location=$LOCATION
```

### Deploy Prefect

```bash
# Set environment variables
export PREFECT_API_URL="https://api.prefect.cloud/api/..."
export PREFECT_API_KEY="your-key"
export DEPLOYMENT_ENV="prod"

# Create deployment
python prefect_config_production.py cloud
```

## Integration Example

Complete pipeline integration:

```python
from src.pipeline import synthetic_data_generation_flow
from src.llm_management import OpenAIManager
from src.monitoring import PipelineMonitor
from src.dataset_registry_enhanced import EnhancedDatasetRegistry
from pathlib import Path
import uuid

# Initialize components
execution_id = str(uuid.uuid4())
monitor = PipelineMonitor(execution_id, "synthetic-data-generation")
registry = EnhancedDatasetRegistry()

# Run pipeline
result = synthetic_data_generation_flow(
    industry="Technology",
    output_dir=Path("data/synthetic_outputs"),
    config=config_dict
)

# Track metrics
monitor.record_samples_generated(1)
monitor.complete(success=True)

# Register dataset
version_id = registry.register_dataset(
    sample_id=result["sample"]["sample_id"],
    json_path=result["sample"]["json_path"],
    csv_path=result["sample"]["csv_path"],
    quality_scores=result["sample"]["training_sample"]["quality_scores"],
    validation_results=result["validation"]
)

print(f"Pipeline completed. Dataset version: {version_id}")
```

## Next Steps

- See `docs/PRODUCTION_SETUP.md` for detailed production setup
- See `IMPLEMENTATION_STATUS.md` for complete feature list
- Review infrastructure templates in `infra/bicep/`

