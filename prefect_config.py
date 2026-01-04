"""
Prefect configuration for workflow orchestration.

Supports both local execution and cloud deployment.
"""

from prefect import flow
from prefect.deployments import Deployment
from prefect.server.schemas.schedules import CronSchedule
from prefect.filesystems import LocalFileSystem

from src.pipeline import synthetic_data_generation_flow
from src.config import PipelineConfig


def create_deployment():
    """Create Prefect deployment configuration."""
    
    # Load configuration
    config = PipelineConfig()
    config_dict = config.get_config_dict()
    
    # Create deployment
    deployment = Deployment.build_from_flow(
        flow=synthetic_data_generation_flow,
        name="synthetic-data-generation",
        work_queue_name="synthetic-data",
        work_pool_name="default-agent-pool",
        parameters={
            "industry": "Technology",
            "output_dir": "data/synthetic_outputs",
            "config": config_dict
        },
        schedule=CronSchedule(cron="0 2 * * *", timezone="UTC"),  # Daily at 2 AM UTC
        storage=LocalFileSystem(basepath="."),
        tags=["synthetic-data", "training-samples"]
    )
    
    return deployment


if __name__ == "__main__":
    deployment = create_deployment()
    deployment.apply()

