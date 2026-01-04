"""
Main synthetic data generation pipeline.

Orchestrates the complete workflow from transcript ingestion to training sample output.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd

from prefect import flow, task, get_run_logger
from prefect.task_runners import SequentialTaskRunner

try:
    from src.synth_llm import TranscriptInput, ScenarioGenerator, RequirementScenario
    from src.company_profiler import CompanyProfiler, CompanyProfile
    from src.manifest_builder import ManifestBuilder, SystemManifest
    from src.validators import RealismValidator, SchemaValidator, QualityValidator
except ImportError:
    # Fallback for relative imports
    from .synth_llm import TranscriptInput, ScenarioGenerator, RequirementScenario
    from .company_profiler import CompanyProfiler, CompanyProfile
    from .manifest_builder import ManifestBuilder, SystemManifest
    from .validators import RealismValidator, SchemaValidator, QualityValidator

logger = logging.getLogger(__name__)


@task
def load_transcript(transcript_path: Path) -> TranscriptInput:
    """Load a meeting transcript from file."""
    logger = get_run_logger()
    
    with open(transcript_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse transcript (assumes simple format; can be enhanced)
    transcript_id = transcript_path.stem
    transcript = TranscriptInput(
        transcript_id=transcript_id,
        transcript_text=content,
        meeting_date=datetime.utcnow(),  # Could parse from filename or content
        participants=[]  # Could extract from content
    )
    
    logger.info(f"Loaded transcript: {transcript_id}")
    return transcript


@task
def extract_scenarios(
    transcript: TranscriptInput,
    scenario_generator: ScenarioGenerator
) -> List[RequirementScenario]:
    """Extract requirement scenarios from transcript."""
    logger = get_run_logger()
    scenarios = scenario_generator.extract_scenarios(transcript)
    logger.info(f"Extracted {len(scenarios)} scenarios")
    return scenarios


@task
def generate_company_profile(
    industry: Optional[str],
    profiler: CompanyProfiler
) -> CompanyProfile:
    """Generate a synthetic company profile."""
    logger = get_run_logger()
    profile = profiler.generate_profile(industry=industry)
    logger.info(f"Generated company profile: {profile.company_id}")
    return profile


@task
def build_manifest(
    company_profile: CompanyProfile,
    scenarios: List[RequirementScenario],
    manifest_builder: ManifestBuilder
) -> SystemManifest:
    """Build system requirement manifest."""
    logger = get_run_logger()
    manifest = manifest_builder.build_manifest(company_profile, scenarios)
    logger.info(f"Built manifest: {manifest.manifest_id} with {manifest.total_requirements} requirements")
    return manifest


@task
def validate_realism(
    company_profile: CompanyProfile,
    scenarios: List[RequirementScenario],
    validator: RealismValidator
) -> Dict:
    """Validate realism of generated data."""
    logger = get_run_logger()
    
    profile_score = validator.validate_company_profile(company_profile.dict())
    scenario_scores = [
        validator.validate_requirement_scenario(scenario.dict())
        for scenario in scenarios
    ]
    
    all_passed = profile_score.passed and all(s.passed for s in scenario_scores)
    
    logger.info(f"Realism validation: {'PASSED' if all_passed else 'FAILED'}")
    
    return {
        "profile_score": profile_score.dict(),
        "scenario_scores": [s.dict() for s in scenario_scores],
        "all_passed": all_passed
    }


@task
def validate_schema(
    company_profile: CompanyProfile,
    manifest: SystemManifest,
    validator: SchemaValidator
) -> Dict:
    """Validate schema compliance."""
    logger = get_run_logger()
    
    profile_result = validator.validate_company_profile(company_profile.dict())
    manifest_result = validator.validate_system_manifest(manifest.dict())
    
    all_passed = profile_result.passed and manifest_result.passed
    
    logger.info(f"Schema validation: {'PASSED' if all_passed else 'FAILED'}")
    
    return {
        "profile_validation": profile_result.dict(),
        "manifest_validation": manifest_result.dict(),
        "all_passed": all_passed
    }


@task
def create_training_sample(
    company_profile: CompanyProfile,
    manifest: SystemManifest,
    validation_results: Dict,
    output_dir: Path
) -> Dict:
    """Create training sample in JSON and CSV formats."""
    logger = get_run_logger()
    
    sample_id = f"sample_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    # Create JSON sample
    training_sample = {
        "sample_id": sample_id,
        "company_profile": company_profile.dict(),
        "system_manifest": manifest.dict(),
        "created_at": datetime.utcnow().isoformat(),
        "quality_scores": {
            "realism_score": validation_results.get("realism", {}).get("profile_score", {}).get("overall_score", 0.0),
            "completeness_score": 1.0,  # Could calculate from validation
            "schema_validation_passed": validation_results.get("schema", {}).get("all_passed", False),
            "quality_checks": []
        },
        "metadata": {
            "pipeline_version": "0.1.0",
            "validation_timestamp": datetime.utcnow().isoformat()
        }
    }
    
    # Save JSON
    json_path = output_dir / f"{sample_id}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(training_sample, f, indent=2, default=str)
    
    # Create CSV representation
    csv_data = {
        "sample_id": [sample_id],
        "company_id": [company_profile.company_id],
        "company_name": [company_profile.company_name],
        "industry": [company_profile.industry],
        "employee_count": [company_profile.employee_count],
        "revenue_min": [float(company_profile.revenue_range_min)],
        "revenue_max": [float(company_profile.revenue_range_max)],
        "ticket_volume_daily": [company_profile.operational_metrics.ticket_volume_daily],
        "handoff_delay_hours": [company_profile.operational_metrics.handoff_delay_avg_hours],
        "handoff_failure_rate": [company_profile.operational_metrics.handoff_failure_rate],
        "advisor_count": [company_profile.operational_metrics.advisor_count],
        "requirements_count": [manifest.total_requirements],
        "components_count": [manifest.total_components],
        "complexity_score": [manifest.complexity_score],
        "realism_score": [training_sample["quality_scores"]["realism_score"]],
        "created_at": [datetime.utcnow().isoformat()]
    }
    
    df = pd.DataFrame(csv_data)
    csv_path = output_dir / f"{sample_id}.csv"
    df.to_csv(csv_path, index=False)
    
    logger.info(f"Created training sample: {sample_id}")
    
    return {
        "sample_id": sample_id,
        "json_path": str(json_path),
        "csv_path": str(csv_path),
        "training_sample": training_sample
    }


@flow(
    name="synthetic-data-generation",
    task_runner=SequentialTaskRunner(),
    log_prints=True
)
def synthetic_data_generation_flow(
    transcript_path: Optional[Path] = None,
    industry: Optional[str] = None,
    output_dir: Path = Path("data/synthetic_outputs"),
    config: Optional[Dict] = None
) -> Dict:
    """
    Main pipeline flow for synthetic data generation.
    
    Args:
        transcript_path: Path to meeting transcript (optional)
        industry: Target industry for company profile
        output_dir: Output directory for training samples
        config: Configuration dictionary with Azure credentials
        
    Returns:
        Dictionary with pipeline results
    """
    logger = get_run_logger()
    logger.info("Starting synthetic data generation pipeline")
    
    # Initialize components
    if config is None:
        config = {}
    
    scenario_generator = ScenarioGenerator(
        azure_openai_endpoint=config.get("azure_openai_endpoint"),
        deployment_name=config.get("azure_openai_deployment_name"),
        key_vault_url=config.get("key_vault_url")
    )
    
    profiler = CompanyProfiler(
        azure_openai_endpoint=config.get("azure_openai_endpoint"),
        deployment_name=config.get("azure_openai_deployment_name"),
        key_vault_url=config.get("key_vault_url"),
        use_llm_enhancement=config.get("use_llm_enhancement", True)
    )
    
    manifest_builder = ManifestBuilder(
        azure_openai_endpoint=config.get("azure_openai_endpoint"),
        deployment_name=config.get("azure_openai_deployment_name"),
        key_vault_url=config.get("key_vault_url")
    )
    
    realism_validator = RealismValidator(
        azure_openai_endpoint=config.get("azure_openai_endpoint"),
        deployment_name=config.get("azure_openai_deployment_name"),
        key_vault_url=config.get("key_vault_url")
    )
    
    schema_validator = SchemaValidator()
    quality_validator = QualityValidator()
    
    # Execute pipeline
    scenarios = []
    if transcript_path and transcript_path.exists():
        transcript = load_transcript(transcript_path)
        scenarios = extract_scenarios(transcript, scenario_generator)
    else:
        logger.info("No transcript provided, generating scenarios from company profile")
    
    company_profile = generate_company_profile(industry, profiler)
    
    # If no scenarios from transcript, generate from pain points
    if not scenarios:
        # Create minimal scenarios from pain points
        try:
            from src.synth_llm import RequirementScenario
        except ImportError:
            from .synth_llm import RequirementScenario
        scenarios = [
            RequirementScenario(
                scenario_id=f"scenario_{i+1}",
                source_transcript_id="synthetic",
                business_context=pp,
                pain_points=[pp],
                urgency_level="medium",
                industry_domain=industry or company_profile.industry,
                confidence_score=0.8
            )
            for i, pp in enumerate(company_profile.pain_points[:3])
        ]
    
    manifest = build_manifest(company_profile, scenarios, manifest_builder)
    
    # Validate
    realism_results = validate_realism(company_profile, scenarios, realism_validator)
    schema_results = validate_schema(company_profile, manifest, schema_validator)
    
    validation_results = {
        "realism": realism_results,
        "schema": schema_results
    }
    
    # Create training sample
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    sample_result = create_training_sample(
        company_profile,
        manifest,
        validation_results,
        output_dir
    )
    
    logger.info("Pipeline completed successfully")
    
    return {
        "sample": sample_result,
        "validation": validation_results,
        "company_profile_id": company_profile.company_id,
        "manifest_id": manifest.manifest_id
    }


if __name__ == "__main__":
    # Example usage
    synthetic_data_generation_flow(
        industry="Technology",
        output_dir=Path("data/synthetic_outputs")
    )

