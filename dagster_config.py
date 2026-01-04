"""
Dagster configuration as alternative to Prefect.

Provides asset-based orchestration for the synthetic data pipeline.
"""

from dagster import (
    asset,
    AssetExecutionContext,
    Definitions,
    ScheduleDefinition,
    define_asset_job,
    DailyPartitionsDefinition
)
from pathlib import Path
from typing import Dict

from src.pipeline import synthetic_data_generation_flow
from src.config import PipelineConfig


@asset(
    group_name="synthetic_data",
    description="Synthetic company profiles"
)
def company_profiles(context: AssetExecutionContext) -> Dict:
    """Generate synthetic company profiles."""
    config = PipelineConfig()
    config_dict = config.get_config_dict()
    
    # Run pipeline for company profile generation
    result = synthetic_data_generation_flow(
        industry="Technology",
        output_dir=Path("data/synthetic_outputs"),
        config=config_dict
    )
    
    return result


@asset(
    group_name="synthetic_data",
    deps=[company_profiles],
    description="System requirement manifests"
)
def system_manifests(context: AssetExecutionContext, company_profiles: Dict) -> Dict:
    """Generate system requirement manifests."""
    # Manifests are created as part of the pipeline
    return company_profiles


@asset(
    group_name="synthetic_data",
    deps=[system_manifests],
    description="Validated training samples"
)
def training_samples(context: AssetExecutionContext, system_manifests: Dict) -> Dict:
    """Create validated training samples."""
    # Training samples are created as part of the pipeline
    return system_manifests


# Define job
synthetic_data_job = define_asset_job(
    "synthetic_data_generation",
    selection=[company_profiles, system_manifests, training_samples]
)

# Define schedule
synthetic_data_schedule = ScheduleDefinition(
    job=synthetic_data_job,
    cron_schedule="0 2 * * *",  # Daily at 2 AM
    name="daily_synthetic_data_generation"
)

# Create definitions
defs = Definitions(
    assets=[company_profiles, system_manifests, training_samples],
    jobs=[synthetic_data_job],
    schedules=[synthetic_data_schedule]
)

