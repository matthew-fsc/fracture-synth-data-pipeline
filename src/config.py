"""
Configuration management for the synthetic data pipeline.

Loads configuration from environment variables and Azure Key Vault.
"""

import os
import logging
from typing import Dict, Optional
from pathlib import Path

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

logger = logging.getLogger(__name__)


class PipelineConfig:
    """Pipeline configuration manager."""
    
    def __init__(self, key_vault_url: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            key_vault_url: Optional Azure Key Vault URL
        """
        self.key_vault_url = key_vault_url or os.getenv("AZURE_KEY_VAULT_URL")
        self._secrets = {}
        
        if self.key_vault_url:
            self._load_from_key_vault()
    
    def _load_from_key_vault(self):
        """Load secrets from Azure Key Vault."""
        try:
            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=self.key_vault_url, credential=credential)
            
            # List of secret names to load
            secret_names = [
                "azure-openai-api-key",
                "azure-tenant-id",
                "azure-subscription-id",
                "azure-resource-group",
                "azure-ml-workspace-name",
                "azure-openai-endpoint",
                "azure-openai-deployment-name",
                "github-app-id",
                "github-app-private-key",
                "github-installation-id",
                "github-org-name",
                "github-pat",
                "service-principal-client-id",
                "service-principal-client-secret",
                "blob-storage-account-name",
                "blob-storage-container-name"
            ]
            
            for secret_name in secret_names:
                try:
                    secret = client.get_secret(secret_name)
                    self._secrets[secret_name.replace("-", "_")] = secret.value
                except Exception as e:
                    logger.warning(f"Could not load secret {secret_name}: {e}")
        
        except Exception as e:
            logger.error(f"Error loading from Key Vault: {e}", exc_info=True)
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get configuration value.
        
        Priority: Key Vault > Environment Variable > Default
        
        Args:
            key: Configuration key
            default: Default value
            
        Returns:
            Configuration value
        """
        # Try Key Vault first
        key_normalized = key.replace("-", "_").upper()
        if key_normalized in self._secrets:
            return self._secrets[key_normalized]
        
        # Try environment variable
        env_key = key_normalized.replace("_", "-")
        value = os.getenv(env_key) or os.getenv(key_normalized)
        if value:
            return value
        
        return default
    
    def get_config_dict(self) -> Dict[str, str]:
        """Get full configuration as dictionary."""
        config = {
            "azure_openai_endpoint": self.get("azure-openai-endpoint"),
            "azure_openai_deployment_name": self.get("azure-openai-deployment-name"),
            "azure_openai_api_key": self.get("azure-openai-api-key"),
            "key_vault_url": self.key_vault_url,
            "azure_tenant_id": self.get("azure-tenant-id"),
            "azure_subscription_id": self.get("azure-subscription-id"),
            "azure_resource_group": self.get("azure-resource-group"),
            "azure_ml_workspace_name": self.get("azure-ml-workspace-name"),
            "github_app_id": self.get("github-app-id"),
            "github_app_private_key": self.get("github-app-private-key"),
            "github_installation_id": self.get("github-installation-id"),
            "github_org_name": self.get("github-org-name"),
            "github_pat": self.get("github-pat"),
            "service_principal_client_id": self.get("service-principal-client-id"),
            "service_principal_client_secret": self.get("service-principal-client-secret"),
            "blob_storage_account_name": self.get("blob-storage-account-name"),
            "blob_storage_container_name": self.get("blob-storage-container-name"),
            "use_llm_enhancement": os.getenv("USE_LLM_ENHANCEMENT", "true").lower() == "true"
        }
        
        return config

