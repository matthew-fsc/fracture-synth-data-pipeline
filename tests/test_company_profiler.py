"""Tests for company profiler."""

import pytest
from src.company_profiler import CompanyProfiler, CompanyProfile


def test_company_profiler_initialization():
    """Test company profiler initialization."""
    profiler = CompanyProfiler(use_llm_enhancement=False)
    assert profiler is not None


def test_generate_profile_basic():
    """Test basic company profile generation."""
    profiler = CompanyProfiler(use_llm_enhancement=False)
    profile = profiler.generate_profile(industry="Technology")
    
    assert isinstance(profile, CompanyProfile)
    assert profile.company_id is not None
    assert profile.company_name is not None
    assert profile.industry == "Technology"
    assert profile.employee_count > 0
    assert profile.revenue_range_min > 0
    assert profile.revenue_range_max >= profile.revenue_range_min
    assert len(profile.departments) > 0
    assert len(profile.pain_points) > 0


def test_operational_metrics():
    """Test operational metrics generation."""
    profiler = CompanyProfiler(use_llm_enhancement=False)
    profile = profiler.generate_profile()
    
    metrics = profile.operational_metrics
    assert metrics.ticket_volume_daily >= 0
    assert metrics.handoff_delay_avg_hours >= 0
    assert 0 <= metrics.handoff_failure_rate <= 1
    assert metrics.advisor_count >= 0
    assert metrics.department_count >= 1
    assert 0 <= metrics.sla_breach_rate <= 1


def test_kpi_generation():
    """Test KPI generation."""
    profiler = CompanyProfiler(use_llm_enhancement=False)
    profile = profiler.generate_profile()
    
    assert len(profile.kpis) > 0
    for kpi in profile.kpis:
        assert kpi.kpi_name is not None
        assert kpi.kpi_value is not None
        assert kpi.kpi_unit is not None
        assert kpi.trend in ["improving", "stable", "declining"]


def test_industry_specific_pain_points():
    """Test industry-specific pain point generation."""
    profiler = CompanyProfiler(use_llm_enhancement=False)
    
    healthcare_profile = profiler.generate_profile(industry="Healthcare")
    assert len(healthcare_profile.pain_points) > 0
    
    finance_profile = profiler.generate_profile(industry="Financial Services")
    assert len(finance_profile.pain_points) > 0

