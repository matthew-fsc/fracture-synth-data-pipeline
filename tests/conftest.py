"""Shared pytest fixtures for testing."""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock
from datetime import datetime

from src.company_profiler import CompanyProfile, OperationalMetrics
from src.manifest_builder import SystemManifest


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory for tests."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_company_profile():
    """Create a sample company profile for testing."""
    metrics = OperationalMetrics(
        ticket_volume_daily=50,
        ticket_volume_monthly=1500,
        handoff_delay_avg_hours=8.5,
        handoff_failure_rate=0.05,
        workflow_stall_count=10,
        compliance_failures_monthly=2,
        advisor_count=5,
        department_count=5,
        realtime_ingestion_volume_daily=1000,
        sla_breach_rate=0.02
    )
    
    return CompanyProfile(
        company_id="test_comp_123",
        company_name="Test Corp",
        industry="Technology",
        revenue_range_min=1000000,
        revenue_range_max=5000000,
        employee_count=250,
        headquarters_location="San Francisco, CA",
        departments=["Engineering", "Sales", "Support"],
        pain_points=["Slow ticket resolution", "Manual processes"],
        kpis=[],
        operational_metrics=metrics,
        generated_at=datetime.utcnow()
    )


@pytest.fixture
def sample_system_manifest(sample_company_profile):
    """Create a sample system manifest for testing."""
    from src.manifest_builder import DependencyGraph
    from src.synth_llm import RequirementScenario
    
    return SystemManifest(
        manifest_id="test_manifest_123",
        company_profile=sample_company_profile,
        source_scenarios=[],
        requirements=[],
        components=[],
        dependency_graph=DependencyGraph(),
        total_requirements=5,
        total_components=3,
        complexity_score=0.65
    )


@pytest.fixture
def mock_config():
    """Create a mock configuration dictionary."""
    return {
        "azure_openai_endpoint": "https://test.openai.azure.com",
        "azure_openai_deployment_name": "gpt-4",
        "key_vault_url": "https://test.vault.azure.net",
        "enable_realism_validation": False,  # Disable for faster tests
        "use_llm_enhancement": False
    }


@pytest.fixture
def mock_config_no_azure():
    """Create a mock configuration without Azure credentials."""
    return {
        "enable_realism_validation": False,
        "use_llm_enhancement": False
    }

