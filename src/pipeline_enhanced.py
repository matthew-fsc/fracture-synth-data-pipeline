"""
Enhanced Pipeline with Integration of New Modules

Integrates real-world patterns, gap analysis, data optimization,
enhanced validation, monitoring, and LLM management.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from prefect import flow, task, get_run_logger
from prefect.task_runners import SequentialTaskRunner

try:
    from src.synth_llm import TranscriptInput, ScenarioGenerator, RequirementScenario
    from src.company_profiler import CompanyProfiler, CompanyProfile
    from src.manifest_builder import ManifestBuilder, SystemManifest
    from src.validators import RealismValidator, SchemaValidator, QualityValidator
    from src.validators.quality_validator_enhanced import EnhancedQualityValidator
    from src.llm_management import OpenAIManager
    from src.monitoring import PipelineMonitor, AppInsightsClient
    from src.dataset_registry_enhanced import EnhancedDatasetRegistry, DatasetStatus
    from src.realworld_integration import PatternExtractor, ScenarioEnhancer, EnhancementStrategy
    from src.gap_analysis import GapDetector, TargetedGenerator, GapType, GapPriority
    from src.data_optimization import DatasetBalancer, PriorityScorer, BalancingStrategy, ScoringCriteria
except ImportError:
    # Fallback for relative imports
    from .synth_llm import TranscriptInput, ScenarioGenerator, RequirementScenario
    from .company_profiler import CompanyProfiler, CompanyProfile
    from .manifest_builder import ManifestBuilder, SystemManifest
    from .validators import RealismValidator, SchemaValidator, QualityValidator
    from .validators.quality_validator_enhanced import EnhancedQualityValidator
    from .llm_management import OpenAIManager
    from .monitoring import PipelineMonitor, AppInsightsClient
    from .dataset_registry_enhanced import EnhancedDatasetRegistry, DatasetStatus
    from .realworld_integration import PatternExtractor, ScenarioEnhancer, EnhancementStrategy
    from .gap_analysis import GapDetector, TargetedGenerator, GapType, GapPriority
    from .data_optimization import DatasetBalancer, PriorityScorer, BalancingStrategy, ScoringCriteria

logger = logging.getLogger(__name__)


@task
def initialize_enhanced_components(config: Dict[str, Any]) -> Dict[str, Any]:
    """Initialize enhanced pipeline components."""
    logger = get_run_logger()
    
    components = {}
    
    # Initialize LLM Manager for cost tracking
    if config.get("azure_openai_endpoint"):
        try:
            components["llm_manager"] = OpenAIManager(
                azure_openai_endpoint=config["azure_openai_endpoint"],
                deployment_name=config.get("azure_openai_deployment_name", "gpt-4-turbo"),
                key_vault_url=config.get("key_vault_url")
            )
            logger.info("LLM Manager initialized for cost tracking")
        except Exception as e:
            logger.warning(f"Failed to initialize LLM Manager: {e}")
            components["llm_manager"] = None
    
    # Initialize Application Insights
    app_insights_conn_str = config.get("applicationinsights_connection_string")
    if app_insights_conn_str:
        try:
            components["app_insights"] = AppInsightsClient(
                connection_string=app_insights_conn_str
            )
            logger.info("Application Insights client initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Application Insights: {e}")
            components["app_insights"] = None
    else:
        components["app_insights"] = None
    
    # Initialize enhanced validators
    try:
        components["enhanced_validator"] = EnhancedQualityValidator()
        logger.info("Enhanced quality validator initialized")
    except Exception as e:
        logger.warning(f"Enhanced validator not available: {e}")
        components["enhanced_validator"] = None
    
    # Initialize dataset registry
    try:
        components["registry"] = EnhancedDatasetRegistry()
        logger.info("Enhanced dataset registry initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize enhanced registry: {e}")
        components["registry"] = None
    
    # Initialize real-world integration components
    try:
        components["pattern_extractor"] = PatternExtractor()
        components["scenario_enhancer"] = ScenarioEnhancer(
            pattern_extractor=components["pattern_extractor"]
        )
        logger.info("Real-world integration components initialized")
    except Exception as e:
        logger.warning(f"Real-world integration not available: {e}")
        components["pattern_extractor"] = None
        components["scenario_enhancer"] = None
    
    return components


@task
def enhance_with_realworld_patterns(
    company_profile: CompanyProfile,
    scenario_enhancer: Optional[ScenarioEnhancer],
    enable_enhancement: bool = True
) -> CompanyProfile:
    """Enhance company profile with real-world patterns."""
    logger = get_run_logger()
    
    if not enable_enhancement or not scenario_enhancer:
        return company_profile
    
    try:
        enhanced_dict = scenario_enhancer.enhance_company_profile(
            company_profile=company_profile.dict(),
            strategies=[
                EnhancementStrategy.ADD_PAIN_POINTS,
                EnhancementStrategy.APPLY_OPERATIONAL_PATTERNS,
                EnhancementStrategy.DIVERSIFY_METRICS
            ]
        )
        
        # Reconstruct CompanyProfile from enhanced dict
        # Note: This is a simplified approach - in practice, you'd want to preserve the Pydantic model
        enhanced_profile = CompanyProfile(**enhanced_dict)
        logger.info("Enhanced company profile with real-world patterns")
        return enhanced_profile
    except Exception as e:
        logger.warning(f"Failed to enhance with real-world patterns: {e}")
        return company_profile


@task
def validate_with_enhanced_validator(
    sample_data: Dict[str, Any],
    enhanced_validator: Optional[EnhancedQualityValidator],
    dataset_type: str = "training_samples"
) -> Dict[str, Any]:
    """Validate with enhanced quality validator."""
    logger = get_run_logger()
    
    if not enhanced_validator:
        return {"enhanced_validation": None}
    
    try:
        import pandas as pd
        
        # Convert sample to DataFrame for validation
        # This is simplified - you'd want to properly extract the relevant data
        df = pd.DataFrame([sample_data])
        
        result = enhanced_validator.validate_with_expectations(
            df=df,
            suite_name=f"{dataset_type}_v1",
            dataset_type=dataset_type
        )
        
        logger.info(f"Enhanced validation completed: {result.success}")
        
        return {
            "enhanced_validation": result.dict(),
            "quality_score": result.quality_score,
            "validation_passed": result.success
        }
    except Exception as e:
        logger.warning(f"Enhanced validation failed: {e}")
        return {"enhanced_validation": None, "error": str(e)}


@flow(
    name="enhanced-synthetic-data-generation",
    task_runner=SequentialTaskRunner(),
    log_prints=True
)
def enhanced_synthetic_data_generation_flow(
    transcript_path: Optional[Path] = None,
    industry: Optional[str] = None,
    output_dir: Path = Path("data/synthetic_outputs"),
    config: Optional[Dict[str, Any]] = None,
    enable_realworld_enhancement: bool = True,
    enable_enhanced_validation: bool = True,
    enable_monitoring: bool = True,
    register_to_registry: bool = True
) -> Dict[str, Any]:
    """
    Enhanced pipeline flow with integration of new modules.
    
    Args:
        transcript_path: Path to meeting transcript (optional)
        industry: Target industry for company profile
        output_dir: Output directory for training samples
        config: Configuration dictionary with Azure credentials
        enable_realworld_enhancement: Enable real-world pattern enhancement
        enable_enhanced_validation: Enable enhanced validation
        enable_monitoring: Enable monitoring and cost tracking
        register_to_registry: Register dataset to enhanced registry
        
    Returns:
        Dictionary with pipeline results
    """
    logger = get_run_logger()
    execution_id = str(uuid.uuid4())
    
    logger.info(f"Starting enhanced synthetic data generation pipeline (execution_id: {execution_id})")
    
    # Initialize configuration
    if config is None:
        config = {}
    
    # Initialize enhanced components
    components = initialize_enhanced_components(config)
    
    # Initialize monitoring
    monitor = None
    if enable_monitoring:
        try:
            monitor = PipelineMonitor(
                execution_id=execution_id,
                pipeline_name="enhanced-synthetic-data-generation",
                app_insights_client=components.get("app_insights")
            )
            logger.info("Pipeline monitoring initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize monitoring: {e}")
    
    try:
        # Import base pipeline tasks (reuse existing logic)
        from src.pipeline import (
            load_transcript, extract_scenarios, generate_company_profile,
            build_manifest, validate_realism, validate_schema, create_training_sample
        )
        
        # Execute base pipeline steps
        scenarios = []
        if transcript_path and transcript_path.exists():
            transcript = load_transcript(transcript_path)
            scenario_generator = ScenarioGenerator(
                azure_openai_endpoint=config.get("azure_openai_endpoint"),
                deployment_name=config.get("azure_openai_deployment_name"),
                key_vault_url=config.get("key_vault_url")
            )
            scenarios = extract_scenarios(transcript, scenario_generator)
        else:
            logger.info("No transcript provided, generating scenarios from company profile")
        
        profiler = CompanyProfiler(
            azure_openai_endpoint=config.get("azure_openai_endpoint"),
            deployment_name=config.get("azure_openai_deployment_name"),
            key_vault_url=config.get("key_vault_url"),
            use_llm_enhancement=config.get("use_llm_enhancement", True)
        )
        
        company_profile = generate_company_profile(industry, profiler)
        
        # Enhance with real-world patterns
        if enable_realworld_enhancement and components.get("scenario_enhancer"):
            company_profile = enhance_with_realworld_patterns(
                company_profile,
                components["scenario_enhancer"],
                enable_enhancement=True
            )
        
        # Generate scenarios if needed
        if not scenarios:
            from src.synth_llm import RequirementScenario
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
        
        manifest_builder = ManifestBuilder(
            azure_openai_endpoint=config.get("azure_openai_endpoint"),
            deployment_name=config.get("azure_openai_deployment_name"),
            key_vault_url=config.get("key_vault_url")
        )
        manifest = build_manifest(company_profile, scenarios, manifest_builder)
        
        # Validate
        realism_validator = RealismValidator(
            azure_openai_endpoint=config.get("azure_openai_endpoint"),
            deployment_name=config.get("azure_openai_deployment_name"),
            key_vault_url=config.get("key_vault_url")
        )
        schema_validator = SchemaValidator()
        
        realism_results = validate_realism(company_profile, scenarios, realism_validator)
        schema_results = validate_schema(company_profile, manifest, schema_validator)
        
        validation_results = {
            "realism": realism_results,
            "schema": schema_results
        }
        
        # Enhanced validation
        if enable_enhanced_validation:
            sample_dict = {
                "company_profile": company_profile.dict(),
                "system_manifest": manifest.dict()
            }
            enhanced_validation = validate_with_enhanced_validator(
                sample_dict,
                components.get("enhanced_validator"),
                dataset_type="training_samples"
            )
            validation_results["enhanced"] = enhanced_validation
        
        # Create training sample
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        sample_result = create_training_sample(
            company_profile,
            manifest,
            validation_results,
            output_dir
        )
        
        # Track metrics
        if monitor:
            # Track costs if LLM manager available
            if components.get("llm_manager"):
                cost_summary = components["llm_manager"].get_cost_summary()
                monitor.record_cost(cost_summary.get("daily_cost", 0.0))
                usage_stats = components["llm_manager"].get_usage_stats()
                monitor.record_tokens(usage_stats.get("total_tokens", 0))
            
            monitor.record_samples_generated(1)
            validation_passed = (
                validation_results.get("schema", {}).get("all_passed", False) and
                validation_results.get("realism", {}).get("all_passed", False)
            )
            monitor.record_validation_result(validation_passed)
        
        # Register to enhanced registry
        if register_to_registry and components.get("registry"):
            try:
                enhanced_quality_score = validation_results.get("enhanced", {}).get("quality_score", 0.8)
                
                version_id = components["registry"].register_dataset(
                    sample_id=sample_result["sample_id"],
                    json_path=sample_result["json_path"],
                    csv_path=sample_result["csv_path"],
                    quality_scores={
                        "realism_score": validation_results.get("realism", {}).get("profile_score", {}).get("overall_score", 0.8),
                        "enhanced_quality_score": enhanced_quality_score
                    },
                    validation_results=validation_results,
                    metadata={
                        "company_profile": company_profile.dict(),
                        "system_manifest": manifest.dict(),
                        "industry": industry,
                        "execution_id": execution_id
                    }
                )
                logger.info(f"Dataset registered: {version_id}")
                sample_result["registry_version_id"] = version_id
            except Exception as e:
                logger.warning(f"Failed to register dataset: {e}")
        
        # Complete monitoring
        if monitor:
            monitor.complete(success=True)
        
        logger.info("Enhanced pipeline completed successfully")
        
        return {
            "sample": sample_result,
            "validation": validation_results,
            "company_profile_id": company_profile.company_id,
            "manifest_id": manifest.manifest_id,
            "execution_id": execution_id,
            "monitoring": monitor.get_metrics().dict() if monitor else None
        }
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        if monitor:
            monitor.complete(success=False, error_message=str(e))
        raise


if __name__ == "__main__":
    # Example usage
    enhanced_synthetic_data_generation_flow(
        industry="Technology",
        output_dir=Path("data/synthetic_outputs"),
        enable_realworld_enhancement=True,
        enable_enhanced_validation=True,
        enable_monitoring=True
    )

