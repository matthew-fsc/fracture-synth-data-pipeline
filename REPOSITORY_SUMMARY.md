# Repository Summary

This repository implements a production-grade synthetic data generation pipeline for creating training examples for enterprise operational system design.

## Repository Structure

```
synthetic-data-pipeline/
├── src/                          # Core source code
│   ├── synth_llm.py             # LLM scenario generation from transcripts
│   ├── company_profiler.py       # Synthetic company profile generation
│   ├── manifest_builder.py        # System requirement manifest builder
│   ├── pipeline.py               # Main orchestration flow (Prefect)
│   ├── config.py                 # Configuration management
│   ├── dataset_registry.py       # Versioned dataset registry
│   └── validators/               # Validation suite
│       ├── realism_validator.py  # LLM-as-a-judge validation
│       ├── schema_validator.py   # JSON schema validation
│       └── quality_validator.py  # Great Expectations validation
│
├── data/                         # Data directories
│   ├── raw_transcripts/          # Input meeting transcripts
│   ├── synthetic_outputs/        # Generated training samples
│   └── registry/                 # Versioned approved datasets
│
├── schemas/                      # JSON schemas
│   ├── company_profile.json      # Company profile schema
│   ├── system_manifest.json      # System manifest schema
│   └── training_sample.json      # Training sample schema
│
├── tests/                        # Test suite
│   ├── test_company_profiler.py
│   └── test_schema_validator.py
│
├── docs/                         # Documentation
│   └── CREDENTIALS.md            # Credentials and configuration guide
│
├── requirements.txt              # Python dependencies
├── setup.py                      # Package setup
├── pyproject.toml                # Project configuration
├── prefect_config.py             # Prefect orchestration config
├── dagster_config.py             # Dagster orchestration config
├── run_example.py                # Example execution script
├── issues.md                     # Master issue backlog
├── README.md                     # Main documentation
├── CONTRIBUTING.md               # Contribution guidelines
├── LICENSE                       # MIT License
└── .gitignore                    # Git ignore rules
```

## Key Features Implemented

✅ **Core Pipeline Components**
- Transcript ingestion and scenario extraction
- Synthetic company profile generation with Faker + LLM
- System requirement manifest building with dependency graphs
- Multi-layer validation (realism, schema, quality)

✅ **Orchestration**
- Prefect workflow orchestration (local-first, cloud-ready)
- Dagster alternative configuration
- Task-based pipeline execution

✅ **Validation & Quality**
- LLM-as-a-judge realism validation
- JSON Schema validation
- Great Expectations integration (framework ready)
- Quality gates for dataset registry

✅ **Data Management**
- Versioned dataset registry
- JSON + CSV output formats
- Quality scoring and lineage tracking

✅ **Configuration**
- Azure Key Vault integration
- Environment variable support
- Comprehensive credentials documentation

## Pending Implementations

See [issues.md](issues.md) for the complete backlog. High-priority items include:

- Ragas integration for evaluation
- Weights & Biases integration
- Azure ML Workspace integration
- Enhanced transcript parsing
- Comprehensive test coverage

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure credentials:**
   - Set up Azure Key Vault (see [docs/CREDENTIALS.md](docs/CREDENTIALS.md))
   - Or set environment variables for local development

3. **Run example:**
   ```bash
   python run_example.py
   ```

4. **Or use Prefect:**
   ```bash
   prefect server start
   python prefect_config.py
   ```

## Next Steps

1. Set up Azure resources (Key Vault, OpenAI, ML Workspace)
2. Configure credentials in Key Vault
3. Run initial pipeline execution
4. Work through issues in [issues.md](issues.md)
5. Expand test coverage
6. Integrate additional services (W&B, Ragas, etc.)

## Architecture Highlights

- **Modular Design**: Each component is independently testable
- **Type Safety**: Pydantic models enforce data correctness
- **Validation Layers**: Multiple validation stages ensure quality
- **Cloud-Ready**: Supports both local and cloud deployment
- **Extensible**: Easy to add new validators, generators, or integrations

## Technology Stack

- **Python 3.10+**
- **Azure OpenAI** (GPT-4.1+)
- **Pydantic** for data validation
- **Faker** for synthetic data generation
- **Prefect/Dagster** for orchestration
- **Great Expectations** for data quality
- **Pandas** for data processing
- **JSON Schema** for schema validation

## License

MIT License - see [LICENSE](LICENSE) file.

