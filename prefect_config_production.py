"""
Production Prefect Configuration

Supports deployment to:
- Prefect Cloud
- Prefect Server (self-hosted)
- Azure Container Instances
- Azure Kubernetes Service
"""

import os
from pathlib import Path
from prefect import flow
from prefect.deployments import Deployment
from prefect.server.schemas.schedules import CronSchedule, IntervalSchedule
from prefect.filesystems import Azure, LocalFileSystem, S3
from prefect.infrastructure import (
    Process,
    DockerContainer,
    KubernetesJob,
    AzureContainerInstance
)

from src.pipeline import synthetic_data_generation_flow
from src.config import PipelineConfig


def get_storage():
    """
    Get storage backend based on environment.
    
    Priority:
    1. Azure Blob Storage (if configured)
    2. S3 (if configured)
    3. Local filesystem
    """
    # Try Azure Blob Storage
    storage_account = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    container = os.getenv("AZURE_STORAGE_CONTAINER", "prefect-storage")
    
    if storage_account:
        try:
            return Azure(
                azure_storage_account_name=storage_account,
                container_path=container
            )
        except Exception as e:
            print(f"Failed to initialize Azure storage: {e}")
    
    # Try S3
    s3_bucket = os.getenv("S3_BUCKET")
    if s3_bucket:
        try:
            return S3(bucket_path=s3_bucket)
        except Exception as e:
            print(f"Failed to initialize S3 storage: {e}")
    
    # Fallback to local
    return LocalFileSystem(basepath=".")


def get_infrastructure():
    """
    Get infrastructure backend based on environment.
    
    Priority:
    1. Azure Container Instances (if configured)
    2. Kubernetes (if configured)
    3. Docker (if configured)
    4. Process (local)
    """
    # Try Azure Container Instances
    resource_group = os.getenv("AZURE_RESOURCE_GROUP")
    if resource_group:
        try:
            return AzureContainerInstance(
                resource_group_name=resource_group,
                cpu=2,
                memory=4,
                env={
                    "AZURE_KEY_VAULT_URL": os.getenv("AZURE_KEY_VAULT_URL", ""),
                }
            )
        except Exception as e:
            print(f"Failed to initialize ACI infrastructure: {e}")
    
    # Try Kubernetes
    k8s_namespace = os.getenv("KUBERNETES_NAMESPACE", "prefect")
    if os.getenv("KUBERNETES_CONFIG"):
        try:
            return KubernetesJob(
                namespace=k8s_namespace,
                image="prefecthq/prefect:2-python3.11",
                env={
                    "AZURE_KEY_VAULT_URL": os.getenv("AZURE_KEY_VAULT_URL", ""),
                }
            )
        except Exception as e:
            print(f"Failed to initialize Kubernetes infrastructure: {e}")
    
    # Try Docker
    if os.getenv("DOCKER_ENABLED", "false").lower() == "true":
        try:
            return DockerContainer(
                image="prefecthq/prefect:2-python3.11",
                env={
                    "AZURE_KEY_VAULT_URL": os.getenv("AZURE_KEY_VAULT_URL", ""),
                }
            )
        except Exception as e:
            print(f"Failed to initialize Docker infrastructure: {e}")
    
    # Fallback to Process (local)
    return Process(env={
        "AZURE_KEY_VAULT_URL": os.getenv("AZURE_KEY_VAULT_URL", ""),
    })


def create_production_deployment():
    """
    Create production deployment configuration.
    
    Environment variables:
    - PREFECT_API_URL: Prefect API URL (for Prefect Cloud or Server)
    - PREFECT_API_KEY: API key (for Prefect Cloud)
    - DEPLOYMENT_ENV: Deployment environment (dev, staging, prod)
    - SCHEDULE_CRON: Cron expression for scheduling (optional)
    """
    # Load configuration
    config = PipelineConfig()
    config_dict = config.get_config_dict()
    
    # Get deployment environment
    deployment_env = os.getenv("DEPLOYMENT_ENV", "dev")
    
    # Get storage and infrastructure
    storage = get_storage()
    infrastructure = get_infrastructure()
    
    # Parse schedule
    schedule = None
    schedule_cron = os.getenv("SCHEDULE_CRON")
    if schedule_cron:
        try:
            schedule = CronSchedule(cron=schedule_cron, timezone="UTC")
        except Exception as e:
            print(f"Invalid cron expression: {e}")
    
    # Default schedule: Daily at 2 AM UTC
    if not schedule:
        schedule = CronSchedule(cron="0 2 * * *", timezone="UTC")
    
    # Create deployment
    deployment = Deployment.build_from_flow(
        flow=synthetic_data_generation_flow,
        name=f"synthetic-data-generation-{deployment_env}",
        work_queue_name=f"synthetic-data-{deployment_env}",
        work_pool_name=os.getenv("PREFECT_WORK_POOL", "default-agent-pool"),
        parameters={
            "industry": os.getenv("DEFAULT_INDUSTRY", "Technology"),
            "output_dir": os.getenv("OUTPUT_DIR", "data/synthetic_outputs"),
            "config": config_dict
        },
        schedule=schedule,
        storage=storage,
        infrastructure=infrastructure,
        tags=["synthetic-data", "training-samples", deployment_env],
        description="Production synthetic data generation pipeline"
    )
    
    return deployment


def create_prefect_cloud_deployment():
    """
    Create deployment for Prefect Cloud.
    
    Requires:
    - PREFECT_API_URL: Prefect Cloud API URL
    - PREFECT_API_KEY: Prefect Cloud API key
    """
    deployment = create_production_deployment()
    deployment.name = deployment.name.replace("production", "cloud")
    return deployment


def create_prefect_server_deployment():
    """
    Create deployment for self-hosted Prefect Server.
    
    Requires:
    - PREFECT_API_URL: Prefect Server API URL
    """
    deployment = create_production_deployment()
    deployment.name = deployment.name.replace("production", "server")
    return deployment


if __name__ == "__main__":
    import sys
    
    deployment_type = sys.argv[1] if len(sys.argv) > 1 else "production"
    
    if deployment_type == "cloud":
        deployment = create_prefect_cloud_deployment()
    elif deployment_type == "server":
        deployment = create_prefect_server_deployment()
    else:
        deployment = create_production_deployment()
    
    deployment.apply()
    print(f"Deployment '{deployment.name}' created successfully")

