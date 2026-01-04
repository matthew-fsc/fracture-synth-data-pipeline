"""
Main synthetic data generation pipeline.

Orchestrates the complete workflow from transcript ingestion to training sample output.
Optimized for simplicity and efficiency.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import pandas as pd

from prefect import flow, get_run_logger

try:
    from src.synth_llm import TranscriptInput, ScenarioGenerator, RequirementScenario
    from src.company_profiler import CompanyProfiler
    from src.manifest_builder import ManifestBuilder
    from src.validators import RealismValidator, SchemaValidator
except ImportError:
    from .synth_llm import TranscriptInput, ScenarioGenerator, RequirementScenario
    from .company_profiler import CompanyProfiler
    from .manifest_builder import ManifestBuilder
    from .validators import RealismValidator, SchemaValidator

logger = logging.getLogger(__name__)

# Shared schema validator instance (loaded once, reused across runs)
_SCHEMA_VALIDATOR = SchemaValidator()


@flow(name="synthetic-data-generation", log_prints=True)
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
    
    config = config or {}
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract config values once
    endpoint = config.get("azure_openai_endpoint")
    deployment = config.get("azure_openai_deployment_name")
    key_vault = config.get("key_vault_url")
    enable_realism = config.get("enable_realism_validation", True) and endpoint
    
    # Generate company profile
    profiler = CompanyProfiler(
        azure_openai_endpoint=endpoint,
        deployment_name=deployment,
        key_vault_url=key_vault,
        use_llm_enhancement=config.get("use_llm_enhancement", True)
    )
    company_profile = profiler.generate_profile(industry=industry)
    logger.info(f"Generated company profile: {company_profile.company_id}")
    
    # Extract or generate scenarios
    scenarios = []
    if transcript_path:
        transcript_path = Path(transcript_path)
        if transcript_path.exists():
            scenario_gen = ScenarioGenerator(endpoint, deployment, key_vault)
            with open(transcript_path, 'r', encoding='utf-8') as f:
                transcript = TranscriptInput(
                    transcript_id=transcript_path.stem,
                    transcript_text=f.read(),
                    meeting_date=datetime.utcnow(),
                    participants=[]
                )
            scenarios = scenario_gen.extract_scenarios(transcript)
            logger.info(f"Extracted {len(scenarios)} scenarios from transcript")
    
    # Generate scenarios from pain points if none extracted
    if not scenarios:
        industry_domain = industry or company_profile.industry
        scenarios = [
            RequirementScenario(
                scenario_id=f"scenario_{i+1}",
                source_transcript_id="synthetic",
                business_context=pp,
                pain_points=[pp],
                urgency_level="medium",
                industry_domain=industry_domain,
                confidence_score=0.8
            )
            for i, pp in enumerate(company_profile.pain_points[:3])
        ]
    
    # Build manifest
    manifest_builder = ManifestBuilder(endpoint, deployment, key_vault)
    manifest = manifest_builder.build_manifest(company_profile, scenarios)
    logger.info(f"Built manifest: {manifest.manifest_id} with {manifest.total_requirements} requirements")
    
    # Validate
    timestamp = datetime.utcnow()
    validation_results = {}
    
    # Convert to dict once (used in validation and output)
    manifest_dict = manifest.dict()
    
    # Schema validation (reuse shared instance - schemas loaded once)
    schema_result = _SCHEMA_VALIDATOR.validate_system_manifest(manifest_dict)
    schema_passed = schema_result.passed
    validation_results["schema"] = {
        "manifest_validation": schema_result.dict(),
        "all_passed": schema_passed
    }
    logger.info(f"Schema validation: {'PASSED' if schema_passed else 'FAILED'}")
    
    # Realism validation (optional)
    realism_score = 0.8  # Default
    if enable_realism:
        profile_dict = company_profile.dict()
        realism_validator = RealismValidator(endpoint, deployment, key_vault)
        profile_score = realism_validator.validate_company_profile(profile_dict)
        realism_score = profile_score.overall_score
        validation_results["realism"] = {
            "profile_score": profile_score.dict(),
            "all_passed": profile_score.passed
        }
        logger.info(f"Realism validation: {'PASSED' if profile_score.passed else 'FAILED'}")
    else:
        profile_dict = company_profile.dict()
    
    # Create training sample
    sample_id = f"sample_{timestamp.strftime('%Y%m%d_%H%M%S')}"
    timestamp_iso = timestamp.isoformat()
    
    training_sample = {
        "sample_id": sample_id,
        "company_profile": profile_dict,
        "system_manifest": manifest_dict,
        "created_at": timestamp_iso,
        "quality_scores": {
            "realism_score": realism_score,
            "schema_validation_passed": schema_passed
        },
        "metadata": {
            "pipeline_version": "0.1.0",
            "validation_timestamp": timestamp_iso
        }
    }
    
    # Save JSON
    json_path = output_dir / f"{sample_id}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(training_sample, f, indent=2, default=str)
    
    # Save CSV (optimized single-row DataFrame)
    csv_path = output_dir / f"{sample_id}.csv"
    pd.DataFrame([{
        "sample_id": sample_id,
        "company_id": company_profile.company_id,
        "company_name": company_profile.company_name,
        "industry": company_profile.industry,
        "employee_count": company_profile.employee_count,
        "requirements_count": manifest.total_requirements,
        "components_count": manifest.total_components,
        "complexity_score": manifest.complexity_score,
        "realism_score": realism_score,
        "created_at": timestamp_iso
    }]).to_csv(csv_path, index=False)
    
    logger.info(f"Pipeline completed successfully: {sample_id}")
    
    return {
        "sample": {
            "sample_id": sample_id,
            "json_path": str(json_path),
            "csv_path": str(csv_path),
            "training_sample": training_sample
        },
        "validation": validation_results,
        "company_profile_id": company_profile.company_id,
        "manifest_id": manifest.manifest_id
    }


if __name__ == "__main__":
    result = synthetic_data_generation_flow(
        industry="Technology",
        output_dir=Path("data/synthetic_outputs")
    )
    print(f"Generated sample: {result['sample']['sample_id']}")
