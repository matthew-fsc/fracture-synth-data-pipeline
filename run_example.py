#!/usr/bin/env python3
"""
Example script to run the synthetic data generation pipeline.

This demonstrates basic usage without requiring full Azure setup.
"""

import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# For local testing without Azure, you can mock the configuration
# In production, use Azure Key Vault
config = {
    "azure_openai_endpoint": None,  # Set to your endpoint
    "azure_openai_deployment_name": None,  # Set to your deployment
    "key_vault_url": None,  # Set to your Key Vault URL
    "use_llm_enhancement": False  # Set to False for local testing without Azure
}

if __name__ == "__main__":
    print("Synthetic Data Generation Pipeline - Example Run")
    print("=" * 50)
    
    # Check if running with Azure credentials
    if not config.get("azure_openai_endpoint"):
        print("\n⚠️  Running in local mode without Azure OpenAI.")
        print("   Set azure_openai_endpoint in config to enable LLM features.")
        print("   Company profiles will be generated using Faker only.\n")
    
    try:
        from src.pipeline import synthetic_data_generation_flow
        
        # Run the pipeline
        result = synthetic_data_generation_flow(
            industry="Technology",
            output_dir=Path("data/synthetic_outputs"),
            config=config
        )
        
        print("\n✅ Pipeline completed successfully!")
        print(f"   Sample ID: {result['sample']['sample_id']}")
        print(f"   Company Profile ID: {result['company_profile_id']}")
        print(f"   Manifest ID: {result['manifest_id']}")
        print(f"\n   Output files:")
        print(f"   - JSON: {result['sample']['json_path']}")
        print(f"   - CSV: {result['sample']['csv_path']}")
        
        # Check validation results
        validation = result.get('validation', {})
        realism_passed = validation.get('realism', {}).get('all_passed', False)
        schema_passed = validation.get('schema', {}).get('all_passed', False)
        
        print(f"\n   Validation Results:")
        print(f"   - Realism: {'✅ PASSED' if realism_passed else '❌ FAILED'}")
        print(f"   - Schema: {'✅ PASSED' if schema_passed else '❌ FAILED'}")
        
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("   Make sure all dependencies are installed:")
        print("   pip install -r requirements.txt")
    except Exception as e:
        print(f"\n❌ Error running pipeline: {e}")
        import traceback
        traceback.print_exc()

