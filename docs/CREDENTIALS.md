# Credentials and Configuration Guide

This document lists all credentials and configuration values required to enable the synthetic data generation pipeline. All sensitive values should be stored in **Azure Key Vault** for secure access.

## Azure Key Vault Setup

1. Create an Azure Key Vault in your subscription
2. Store all secrets listed below in the Key Vault
3. Ensure the service principal or managed identity has `Get` and `List` permissions on secrets

## Required Credentials

### GitHub & DevOps

| Secret Name | Description | Example |
|------------|-------------|---------|
| `github-app-id` | GitHub App ID for repository access | `123456` |
| `github-app-private-key` | GitHub App Private Key (PEM format) | `-----BEGIN RSA PRIVATE KEY-----\n...` |
| `github-installation-id` | GitHub App Installation ID | `789012` |
| `github-org-name` | GitHub Organization Name | `your-org` |
| `github-pat` | Personal Access Token (classic or fine-grained) with repo read/write for dataset commits | `ghp_xxxxxxxxxxxx` |

**Note:** The PAT should have permissions to:
- Read repository contents
- Write/commit to repository
- Create and update issues (for issue backlog)

### Azure Tenant & AI Training

| Secret Name | Description | Example |
|------------|-------------|---------|
| `azure-tenant-id` | Azure Active Directory Tenant ID | `12345678-1234-1234-1234-123456789012` |
| `azure-subscription-id` | Azure Subscription ID | `87654321-4321-4321-4321-210987654321` |
| `azure-resource-group` | Resource Group for ML workspace + OpenAI | `rg-synthetic-data` |
| `azure-ml-workspace-name` | Azure ML Workspace Name | `mlw-synthetic-data` |
| `azure-openai-endpoint` | Azure OpenAI Service Endpoint | `https://your-resource.openai.azure.com/` |
| `azure-openai-deployment-name` | OpenAI Deployment Name (GPT-4.1+) | `gpt-4-turbo` |
| `azure-openai-api-key` | Azure OpenAI API Key (if not using managed identity) | `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |

### Service Principal Authentication

| Secret Name | Description | Example |
|------------|-------------|---------|
| `service-principal-client-id` | Service Principal Client ID | `12345678-1234-1234-1234-123456789012` |
| `service-principal-client-secret` | Service Principal Client Secret | `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |

**Note:** The service principal should have:
- `Contributor` role on the resource group
- `Key Vault Secrets User` role on the Key Vault
- Access to Azure OpenAI Service

### Storage & Runtime

| Secret Name | Description | Example |
|------------|-------------|---------|
| `blob-storage-account-name` | Blob Storage Account Name for dataset artifacts | `stsynthdata` |
| `blob-storage-container-name` | Blob Storage Container Name | `synthetic-datasets` |

**Optional:** If using SQL for retrieval-augmented synthesis:

| Secret Name | Description | Example |
|------------|-------------|---------|
| `sql-endpoint` | SQL Server Endpoint | `your-server.database.windows.net` |
| `sql-database-name` | SQL Database Name | `synthetic-data-db` |
| `sql-username` | SQL Username | `sqladmin` |
| `sql-password` | SQL Password | `xxxxxxxxxxxx` |

### Data Enrichment & Realism

| Secret Name | Description | Example |
|------------|-------------|---------|
| `company-revenue-api-key` | API Key for company revenue lookup service (optional) | `xxxxxxxxxxxx` |
| `industry-classification-api-key` | API Key for industry classification service (optional) | `xxxxxxxxxxxx` |

## Environment Variables

The following environment variables can be used as alternatives to Key Vault (for local development):

```bash
# Azure Configuration
export AZURE_KEY_VAULT_URL="https://your-keyvault.vault.azure.net/"
export AZURE_TENANT_ID="your-tenant-id"
export AZURE_SUBSCRIPTION_ID="your-subscription-id"
export AZURE_RESOURCE_GROUP="your-resource-group"
export AZURE_ML_WORKSPACE_NAME="your-workspace-name"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4-turbo"
export AZURE_OPENAI_API_KEY="your-api-key"

# GitHub Configuration
export GITHUB_APP_ID="your-app-id"
export GITHUB_APP_PRIVATE_KEY="your-private-key"
export GITHUB_INSTALLATION_ID="your-installation-id"
export GITHUB_ORG_NAME="your-org"
export GITHUB_PAT="your-pat"

# Storage
export BLOB_STORAGE_ACCOUNT_NAME="your-account"
export BLOB_STORAGE_CONTAINER_NAME="your-container"

# Feature Flags
export USE_LLM_ENHANCEMENT="true"
```

## Key Vault Secret Creation Script

Use the following Azure CLI commands to create secrets:

```bash
# Set variables
KEY_VAULT_NAME="your-keyvault-name"
RESOURCE_GROUP="your-resource-group"

# Create Key Vault (if not exists)
az keyvault create --name $KEY_VAULT_NAME --resource-group $RESOURCE_GROUP

# Add secrets
az keyvault secret set --vault-name $KEY_VAULT_NAME --name "azure-openai-endpoint" --value "https://your-resource.openai.azure.com/"
az keyvault secret set --vault-name $KEY_VAULT_NAME --name "azure-openai-deployment-name" --value "gpt-4-turbo"
az keyvault secret set --vault-name $KEY_VAULT_NAME --name "azure-openai-api-key" --value "your-api-key"
az keyvault secret set --vault-name $KEY_VAULT_NAME --name "azure-tenant-id" --value "your-tenant-id"
az keyvault secret set --vault-name $KEY_VAULT_NAME --name "azure-subscription-id" --value "your-subscription-id"
az keyvault secret set --vault-name $KEY_VAULT_NAME --name "azure-resource-group" --value "your-resource-group"
az keyvault secret set --vault-name $KEY_VAULT_NAME --name "azure-ml-workspace-name" --value "your-workspace-name"
az keyvault secret set --vault-name $KEY_VAULT_NAME --name "github-app-id" --value "your-app-id"
az keyvault secret set --vault-name $KEY_VAULT_NAME --name "github-app-private-key" --value "$(cat github-app-private-key.pem)"
az keyvault secret set --vault-name $KEY_VAULT_NAME --name "github-installation-id" --value "your-installation-id"
az keyvault secret set --vault-name $KEY_VAULT_NAME --name "github-org-name" --value "your-org"
az keyvault secret set --vault-name $KEY_VAULT_NAME --name "github-pat" --value "your-pat"
az keyvault secret set --vault-name $KEY_VAULT_NAME --name "service-principal-client-id" --value "your-client-id"
az keyvault secret set --vault-name $KEY_VAULT_NAME --name "service-principal-client-secret" --value "your-client-secret"
az keyvault secret set --vault-name $KEY_VAULT_NAME --name "blob-storage-account-name" --value "your-account-name"
az keyvault secret set --vault-name $KEY_VAULT_NAME --name "blob-storage-container-name" --value "your-container-name"
```

## Access Permissions

Ensure the following permissions are configured:

1. **Service Principal / Managed Identity:**
   - Key Vault: `Key Vault Secrets User` role
   - Resource Group: `Contributor` role
   - Azure OpenAI: Access granted
   - Azure ML Workspace: `Contributor` role

2. **GitHub App:**
   - Repository: Read and Write access
   - Issues: Read and Write access
   - Contents: Read and Write access

3. **Storage Account:**
   - Blob Storage: `Storage Blob Data Contributor` role

## Verification

Test your configuration:

```python
from src.config import PipelineConfig

config = PipelineConfig()
config_dict = config.get_config_dict()

# Check required values
required_keys = [
    "azure_openai_endpoint",
    "azure_openai_deployment_name",
    "azure_tenant_id"
]

missing = [k for k in required_keys if not config_dict.get(k)]
if missing:
    print(f"Missing configuration: {missing}")
else:
    print("Configuration loaded successfully")
```

## Security Best Practices

1. **Never commit secrets to version control**
2. **Use Azure Key Vault for all production secrets**
3. **Rotate secrets regularly**
4. **Use managed identities where possible instead of service principals**
5. **Limit access using Azure RBAC**
6. **Enable Key Vault logging and monitoring**
7. **Use separate Key Vaults for dev/staging/prod environments**

