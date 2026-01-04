# Synthetic Data Generation Pipeline

A production-grade data synthesis workflow for generating training examples for enterprise operational system design. This pipeline ingests meeting transcripts, generates synthetic company profiles, and produces labeled requirement manifests that mirror real consulting engagements.

## Features

- **Transcript Ingestion**: Convert natural-language meeting transcripts into structured requirement scenarios
- **Synthetic Company Profiles**: Generate realistic company profiles with operational metrics, pain points, and KPIs
- **Requirement Manifests**: Produce comprehensive system requirement manifests with dependency graphs
- **Quality Validation**: Multi-layer validation using LLM-as-a-judge, schema validation, and statistical checks
- **Training Sample Output**: Generate training samples in both JSON and CSV formats
- **Versioned Dataset Registry**: Automated quality gates and dataset versioning

## Architecture

```
┌─────────────────┐
│ Meeting         │
│ Transcripts      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐
│ Scenario        │────▶│ Company Profile  │
│ Generator       │     │ Generator        │
│ (Azure OpenAI)  │     │ (Faker + LLM)    │
└────────┬────────┘     └────────┬─────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
            ┌─────────────────┐
            │ Manifest Builder │
            │ (Azure OpenAI)   │
            └────────┬─────────┘
                     │
         ┌───────────┴───────────┐
         │                         │
         ▼                         ▼
┌─────────────────┐      ┌─────────────────┐
│ Realism         │      │ Schema          │
│ Validator       │      │ Validator       │
│ (LLM-as-Judge)  │      │ (JSON Schema)   │
└────────┬────────┘      └────────┬────────┘
         │                        │
         └───────────┬────────────┘
                     ▼
            ┌─────────────────┐
            │ Quality         │
            │ Validator       │
            │ (Great Ex.)     │
            └────────┬────────┘
                     │
                     ▼
            ┌─────────────────┐
            │ Training Sample │
            │ (JSON + CSV)    │
            └─────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.10+
- Azure subscription with:
  - Azure OpenAI Service (GPT-4.1+ deployment)
  - Azure Key Vault
  - Azure ML Workspace (optional)
  - Azure Storage Account (optional)
- GitHub App or PAT for repository access

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd synthetic-data-pipeline
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure credentials (see [CREDENTIALS.md](docs/CREDENTIALS.md)):
   - Set up Azure Key Vault with all required secrets
   - Or set environment variables for local development

### Basic Usage

```python
from src.pipeline import synthetic_data_generation_flow
from pathlib import Path

# Run the pipeline
result = synthetic_data_generation_flow(
    industry="Technology",
    output_dir=Path("data/synthetic_outputs")
)

print(f"Generated sample: {result['sample']['sample_id']}")
```

### Using Prefect

```bash
# Start Prefect server (local)
prefect server start

# Create deployment
python prefect_config.py

# Run flow
prefect deployment run synthetic-data-generation/synthetic-data-generation
```

### Using Dagster

```bash
# Start Dagster UI
dagster dev

# Or use Dagster Cloud
dagster-cloud serverless deploy
```

## Project Structure

```
synthetic-data-pipeline/
├── src/
│   ├── synth_llm.py              # LLM scenario generation
│   ├── company_profiler.py       # Synthetic company profiles
│   ├── manifest_builder.py       # System requirement manifests
│   ├── pipeline.py               # Main orchestration flow
│   ├── config.py                 # Configuration management
│   └── validators/
│       ├── realism_validator.py  # LLM-as-a-judge validation
│       ├── schema_validator.py   # JSON schema validation
│       └── quality_validator.py  # Great Expectations validation
├── data/
│   ├── raw_transcripts/          # Input meeting transcripts
│   ├── synthetic_outputs/        # Generated datasets
│   └── registry/                 # Versioned approved datasets
├── schemas/
│   ├── company_profile.json      # Company profile schema
│   ├── system_manifest.json      # System manifest schema
│   └── training_sample.json      # Training sample schema
├── tests/                        # Unit and integration tests
├── docs/
│   └── CREDENTIALS.md            # Credentials documentation
├── requirements.txt              # Python dependencies
├── prefect_config.py             # Prefect orchestration config
├── dagster_config.py             # Dagster orchestration config
└── issues.md                     # Master issue backlog
```

## Configuration

All configuration is managed through Azure Key Vault or environment variables. See [CREDENTIALS.md](docs/CREDENTIALS.md) for the complete list of required credentials.

Key configuration values:
- `AZURE_KEY_VAULT_URL`: Azure Key Vault URL
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI service endpoint
- `AZURE_OPENAI_DEPLOYMENT_NAME`: Model deployment name
- `USE_LLM_ENHANCEMENT`: Enable/disable LLM enhancement (default: true)

## Data Formats

### Company Profile
- Company metadata (name, industry, revenue, employees)
- Operational metrics (ticket volumes, handoff delays, failure rates)
- KPIs and pain points
- Department structure

### System Manifest
- Requirements (functional, non-functional, compliance)
- System components with dependencies
- Dependency graph with cycle detection
- Complexity scoring

### Training Sample
- Combined company profile and system manifest
- Quality scores and validation results
- Metadata and lineage information

## Validation

The pipeline includes three layers of validation:

1. **Realism Validation**: LLM-as-a-judge scoring for believability
2. **Schema Validation**: JSON Schema compliance checking
3. **Quality Validation**: Statistical checks using Great Expectations

All samples must pass validation gates before being added to the registry.

## Development

### Running Tests

```bash
pytest tests/ -v --cov=src --cov-report=html
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/
```

### Pre-commit Hooks

```bash
pre-commit install
```

## Issue Backlog

See [issues.md](issues.md) for the complete list of pending implementations and enhancements. Issues are progressively closed as agents work through them.

## Contributing

1. Create a feature branch
2. Make your changes
3. Add tests
4. Ensure all validations pass
5. Submit a pull request

## License

[Add your license here]

## Support

For issues and questions:
- Check [issues.md](issues.md) for known issues
- Review [CREDENTIALS.md](docs/CREDENTIALS.md) for configuration help
- Open a GitHub issue for bugs or feature requests

