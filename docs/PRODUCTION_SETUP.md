# Production Setup Guide

This document provides guidance for setting up the synthetic data pipeline in production environments.

## Overview

The production setup includes:
- Production orchestration (Prefect Cloud/Server)
- Azure infrastructure (Storage, Application Insights, Log Analytics)
- Monitoring and observability
- Enhanced validation framework
- Dataset registry with versioning
- Cost tracking and optimization

## Prerequisites

1. Azure subscription with appropriate permissions
2. Prefect Cloud account OR self-hosted Prefect Server
3. Azure Key Vault with all required secrets
4. Python 3.10+ environment

## Infrastructure Deployment

### 1. Deploy Azure Infrastructure

Deploy the Bicep templates to create required Azure resources:

```bash
# Set variables
RESOURCE_GROUP="rg-synth-data-prod"
LOCATION="eastus"
ENVIRONMENT="prod"

# Deploy infrastructure
az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --template-file infra/bicep/main.bicep \
  --parameters \
    environment=$ENVIRONMENT \
    location=$LOCATION \
    projectName="synthdata"
```

### 2. Configure Key Vault

Ensure all required secrets are in Azure Key Vault:

- `azure-openai-endpoint`
- `azure-openai-api-key`
- `azure-openai-deployment-name`
- `applicationinsights-connection-string` (from deployed App Insights)
- `storage-account-connection-string` (from deployed storage)

## Prefect Deployment

### Option 1: Prefect Cloud

1. Get Prefect Cloud API key from https://app.prefect.cloud

2. Set environment variables:
```bash
export PREFECT_API_URL="https://api.prefect.cloud/api/accounts/[ACCOUNT-ID]/workspaces/[WORKSPACE-ID]"
export PREFECT_API_KEY="your-api-key"
export DEPLOYMENT_ENV="prod"
```

3. Create deployment:
```bash
python prefect_config_production.py cloud
```

### Option 2: Prefect Server (Self-Hosted)

1. Start Prefect Server:
```bash
prefect server start
```

2. Set environment variables:
```bash
export PREFECT_API_URL="http://localhost:4200/api"
export DEPLOYMENT_ENV="prod"
```

3. Create deployment:
```bash
python prefect_config_production.py server
```

## Monitoring Setup

### Application Insights

The infrastructure deployment creates an Application Insights workspace. Use the connection string from the deployment outputs:

```bash
# Get connection string
az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name main \
  --query properties.outputs.appInsightsConnectionString \
  --output tsv
```

Add to Key Vault:
```bash
az keyvault secret set \
  --vault-name your-keyvault \
  --name applicationinsights-connection-string \
  --value "<connection-string>"
```

### Log Analytics

Logs are automatically sent to the deployed Log Analytics workspace. Access via Azure Portal or Azure Monitor.

## Configuration

### Environment Variables

Required environment variables:

```bash
# Azure
export AZURE_KEY_VAULT_URL="https://your-keyvault.vault.azure.net/"
export AZURE_TENANT_ID="your-tenant-id"
export AZURE_SUBSCRIPTION_ID="your-subscription-id"

# Prefect
export PREFECT_API_URL="your-prefect-api-url"
export PREFECT_API_KEY="your-prefect-api-key"  # For Prefect Cloud
export DEPLOYMENT_ENV="prod"

# Pipeline
export DEFAULT_INDUSTRY="Technology"
export OUTPUT_DIR="data/synthetic_outputs"
```

## Validation

### Great Expectations

The enhanced validation framework uses Great Expectations. Expectation suites are stored in `data/expectations/`.

To create custom expectation suites:
```python
from src.validators.quality_validator_enhanced import EnhancedQualityValidator

validator = EnhancedQualityValidator()
suite = validator.create_expectation_suite(
    suite_name="training_samples_v1",
    dataset_type="training_samples"
)
```

## Dataset Registry

The enhanced dataset registry supports versioning and lineage tracking:

```python
from src.dataset_registry_enhanced import EnhancedDatasetRegistry

registry = EnhancedDatasetRegistry()

# Register dataset
version_id = registry.register_dataset(
    sample_id="sample_123",
    json_path="path/to/sample.json",
    csv_path="path/to/sample.csv",
    quality_scores={"realism_score": 0.95},
    validation_results={"schema": {"all_passed": True}},
    metadata={"industry": "Technology"}
)

# Approve dataset
registry.approve_dataset(
    dataset_id="dataset_sample_123",
    version="1.0.0",
    approved_by="admin"
)
```

## Cost Monitoring

Cost tracking is built into the pipeline. View costs:

```python
from src.llm_management.openai_manager import OpenAIManager

manager = OpenAIManager(...)
cost_summary = manager.get_cost_summary()
print(cost_summary)
```

## Troubleshooting

### Pipeline Failures

Check Prefect UI for execution details and logs.

### Application Insights

View telemetry in Azure Portal under Application Insights.

### Storage Issues

Verify storage account connection string and container permissions.

## Security

- All secrets stored in Azure Key Vault
- Managed Identity used for authentication where possible
- Storage accounts use private endpoints (recommended for production)
- Enable RBAC on all resources

## Next Steps

1. Set up alerting rules in Azure Monitor
2. Configure automated backups
3. Set up data retention policies
4. Configure CI/CD pipelines for deployment
5. Set up cost alerts

