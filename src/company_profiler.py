"""
Synthetic company profile generation with realistic operational characteristics.

Generates believable business entities with revenue ranges, advisor counts,
ticket volumes, handoff delays, compliance failures, and operational metrics.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from faker import Faker
from pydantic import BaseModel, Field, validator
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from openai import AzureOpenAI

logger = logging.getLogger(__name__)

fake = Faker()


class OperationalMetrics(BaseModel):
    """Operational metrics for a company."""
    ticket_volume_daily: int = Field(ge=0, description="Average daily ticket volume")
    ticket_volume_monthly: int = Field(ge=0, description="Average monthly ticket volume")
    handoff_delay_avg_hours: float = Field(ge=0.0, description="Average handoff delay in hours")
    handoff_failure_rate: float = Field(ge=0.0, le=1.0, description="Handoff failure rate (0-1)")
    workflow_stall_count: int = Field(ge=0, description="Number of workflow stalls per month")
    compliance_failures_monthly: int = Field(ge=0, description="Monthly compliance failures")
    advisor_count: int = Field(ge=0, description="Number of advisors/consultants")
    department_count: int = Field(ge=1, description="Number of departments")
    realtime_ingestion_volume_daily: int = Field(ge=0, description="Daily realtime ingestion volume")
    sla_breach_rate: float = Field(ge=0.0, le=1.0, description="SLA breach rate (0-1)")


class KPI(BaseModel):
    """Key Performance Indicator."""
    kpi_name: str
    kpi_value: float
    kpi_unit: str
    target_value: Optional[float] = None
    trend: str = Field(..., pattern="^(improving|stable|declining)$")
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class CompanyProfile(BaseModel):
    """Synthetic company profile with operational characteristics."""
    company_id: str
    company_name: str
    industry: str
    naics_code: Optional[str] = None
    revenue_range_min: Decimal = Field(..., description="Annual revenue minimum (USD)")
    revenue_range_max: Decimal = Field(..., description="Annual revenue maximum (USD)")
    employee_count: int = Field(ge=1)
    headquarters_location: str
    operational_metrics: OperationalMetrics
    kpis: List[KPI] = Field(default_factory=list)
    pain_points: List[str] = Field(default_factory=list)
    departments: List[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    realism_score: float = Field(ge=0.0, le=1.0, description="LLM-assessed realism score")
    
    @validator('revenue_range_max')
    def revenue_max_greater_than_min(cls, v, values):
        if 'revenue_range_min' in values and v <= values['revenue_range_min']:
            raise ValueError('revenue_range_max must be greater than revenue_range_min')
        return v


class CompanyProfiler:
    """Generates synthetic company profiles with realistic operational data."""
    
    def __init__(
        self,
        azure_openai_endpoint: Optional[str] = None,
        deployment_name: Optional[str] = None,
        api_version: str = "2024-02-15-preview",
        key_vault_url: Optional[str] = None,
        use_llm_enhancement: bool = True
    ):
        """
        Initialize the company profiler.
        
        Args:
            azure_openai_endpoint: Optional Azure OpenAI endpoint for LLM enhancement
            deployment_name: Optional deployment name
            api_version: API version
            key_vault_url: Optional Key Vault URL
            use_llm_enhancement: Whether to use LLM for realism enhancement
        """
        self.use_llm_enhancement = use_llm_enhancement
        self.client = None
        
        if use_llm_enhancement and azure_openai_endpoint:
            credential = DefaultAzureCredential()
            
            if key_vault_url:
                kv_client = SecretClient(vault_url=key_vault_url, credential=credential)
                api_key = kv_client.get_secret("azure-openai-api-key").value
            else:
                api_key = None
            
            self.client = AzureOpenAI(
                azure_endpoint=azure_openai_endpoint,
                api_key=api_key,
                api_version=api_version
            )
    
    def generate_profile(
        self,
        industry: Optional[str] = None,
        employee_count_range: tuple = (50, 5000),
        revenue_range: Optional[tuple] = None
    ) -> CompanyProfile:
        """
        Generate a synthetic company profile.
        
        Args:
            industry: Optional industry to target
            employee_count_range: Tuple of (min, max) employee count
            revenue_range: Optional tuple of (min, max) revenue in USD
            
        Returns:
            Generated company profile
        """
        # Generate base company data
        company_name = fake.company()
        company_id = f"comp_{fake.uuid4()}"
        
        if not industry:
            industry = fake.random_element(elements=(
                "Technology", "Healthcare", "Financial Services",
                "Manufacturing", "Retail", "Professional Services",
                "Energy", "Telecommunications", "Transportation"
            ))
        
        employee_count = fake.random_int(min=employee_count_range[0], max=employee_count_range[1])
        headquarters = f"{fake.city()}, {fake.state_abbr()}, {fake.country()}"
        
        # Calculate revenue based on employee count (rough estimate)
        if not revenue_range:
            revenue_per_employee = fake.random_int(min=100000, max=500000)
            base_revenue = employee_count * revenue_per_employee
            revenue_min = Decimal(str(int(base_revenue * 0.8)))
            revenue_max = Decimal(str(int(base_revenue * 1.2)))
        else:
            revenue_min = Decimal(str(revenue_range[0]))
            revenue_max = Decimal(str(revenue_range[1]))
        
        # Generate operational metrics
        metrics = self._generate_operational_metrics(employee_count, industry)
        
        # Generate departments
        departments = self._generate_departments(employee_count)
        
        # Generate KPIs
        kpis = self._generate_kpis(industry, metrics)
        
        # Generate pain points
        pain_points = self._generate_pain_points(metrics, industry)
        
        profile = CompanyProfile(
            company_id=company_id,
            company_name=company_name,
            industry=industry,
            naics_code=self._get_naics_code(industry),
            revenue_range_min=revenue_min,
            revenue_range_max=revenue_max,
            employee_count=employee_count,
            headquarters_location=headquarters,
            operational_metrics=metrics,
            kpis=kpis,
            pain_points=pain_points,
            departments=departments
        )
        
        # Enhance with LLM if enabled
        if self.use_llm_enhancement and self.client:
            profile = self._enhance_with_llm(profile)
        
        return profile
    
    def _generate_operational_metrics(
        self,
        employee_count: int,
        industry: str
    ) -> OperationalMetrics:
        """Generate realistic operational metrics."""
        # Scale metrics based on company size
        base_ticket_volume = employee_count * fake.random_int(min=1, max=5)
        
        return OperationalMetrics(
            ticket_volume_daily=fake.random_int(min=base_ticket_volume // 30, max=base_ticket_volume // 20),
            ticket_volume_monthly=base_ticket_volume,
            handoff_delay_avg_hours=fake.random_int(min=2, max=48) + fake.random() * 0.99,
            handoff_failure_rate=round(fake.random() * 0.15, 3),  # 0-15% failure rate
            workflow_stall_count=fake.random_int(min=5, max=50),
            compliance_failures_monthly=fake.random_int(min=0, max=20),
            advisor_count=fake.random_int(min=max(1, employee_count // 50), max=employee_count // 10),
            department_count=fake.random_int(min=3, max=min(20, employee_count // 10)),
            realtime_ingestion_volume_daily=fake.random_int(min=100, max=100000),
            sla_breach_rate=round(fake.random() * 0.25, 3)  # 0-25% breach rate
        )
    
    def _generate_departments(self, employee_count: int) -> List[str]:
        """Generate department list."""
        core_departments = ["IT", "Operations", "Finance", "HR", "Sales", "Marketing"]
        additional_departments = [
            "Customer Success", "Product", "Engineering", "Legal",
            "Compliance", "Security", "Support", "Procurement"
        ]
        
        dept_count = min(fake.random_int(min=len(core_departments), max=len(core_departments) + 5), employee_count // 20)
        departments = core_departments.copy()
        
        for _ in range(dept_count - len(core_departments)):
            dept = fake.random_element(elements=additional_departments)
            if dept not in departments:
                departments.append(dept)
        
        return departments
    
    def _generate_kpis(self, industry: str, metrics: OperationalMetrics) -> List[KPI]:
        """Generate realistic KPIs."""
        kpis = [
            KPI(
                kpi_name="Ticket Resolution Time",
                kpi_value=metrics.handoff_delay_avg_hours,
                kpi_unit="hours",
                target_value=metrics.handoff_delay_avg_hours * 0.8,
                trend=fake.random_element(elements=("improving", "stable", "declining"))
            ),
            KPI(
                kpi_name="Handoff Success Rate",
                kpi_value=(1 - metrics.handoff_failure_rate) * 100,
                kpi_unit="percent",
                target_value=95.0,
                trend=fake.random_element(elements=("improving", "stable", "declining"))
            ),
            KPI(
                kpi_name="SLA Compliance Rate",
                kpi_value=(1 - metrics.sla_breach_rate) * 100,
                kpi_unit="percent",
                target_value=98.0,
                trend=fake.random_element(elements=("improving", "stable", "declining"))
            )
        ]
        
        return kpis
    
    def _generate_pain_points(self, metrics: OperationalMetrics, industry: str) -> List[str]:
        """Generate pain points based on metrics."""
        pain_points = []
        
        if metrics.handoff_failure_rate > 0.1:
            pain_points.append("High handoff failure rate causing workflow disruptions")
        
        if metrics.handoff_delay_avg_hours > 24:
            pain_points.append("Excessive handoff delays impacting customer satisfaction")
        
        if metrics.workflow_stall_count > 20:
            pain_points.append("Frequent workflow stalls reducing operational efficiency")
        
        if metrics.compliance_failures_monthly > 5:
            pain_points.append("Compliance failures creating regulatory risk")
        
        if metrics.sla_breach_rate > 0.15:
            pain_points.append("SLA breaches affecting service quality")
        
        if metrics.realtime_ingestion_volume_daily > 50000:
            pain_points.append("High-volume realtime ingestion causing system strain")
        
        # Add industry-specific pain points
        if industry == "Healthcare":
            pain_points.append("HIPAA compliance challenges with data handoffs")
        elif industry == "Financial Services":
            pain_points.append("Regulatory reporting delays")
        elif industry == "Technology":
            pain_points.append("Rapid scaling causing operational bottlenecks")
        
        return pain_points if pain_points else ["General operational inefficiencies"]
    
    def _get_naics_code(self, industry: str) -> str:
        """Get NAICS code for industry (simplified mapping)."""
        mapping = {
            "Technology": "541511",
            "Healthcare": "621111",
            "Financial Services": "522110",
            "Manufacturing": "311111",
            "Retail": "441110",
            "Professional Services": "541611",
            "Energy": "211111",
            "Telecommunications": "517110",
            "Transportation": "481111"
        }
        return mapping.get(industry, "541611")
    
    def _enhance_with_llm(self, profile: CompanyProfile) -> CompanyProfile:
        """Enhance profile with LLM for better realism."""
        if not self.client:
            return profile
        
        prompt = f"""
Review and enhance this synthetic company profile for realism:

Company: {profile.company_name}
Industry: {profile.industry}
Employees: {profile.employee_count}
Revenue: ${profile.revenue_range_min:,.0f} - ${profile.revenue_range_max:,.0f}
Departments: {', '.join(profile.departments)}
Metrics:
- Daily Tickets: {profile.operational_metrics.ticket_volume_daily}
- Handoff Delay: {profile.operational_metrics.handoff_delay_avg_hours} hours
- Handoff Failures: {profile.operational_metrics.handoff_failure_rate * 100:.1f}%
- Advisors: {profile.operational_metrics.advisor_count}

Provide:
1. Realism score (0.0-1.0)
2. Enhanced pain points that align with the metrics
3. Additional realistic KPIs if needed

Output JSON with realism_score, enhanced_pain_points, and optional additional_kpis.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "You are an expert business analyst assessing company profiles."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            if "realism_score" in result:
                profile.realism_score = float(result["realism_score"])
            
            if "enhanced_pain_points" in result:
                profile.pain_points = result["enhanced_pain_points"]
            
            if "additional_kpis" in result:
                for kpi_data in result["additional_kpis"]:
                    profile.kpis.append(KPI(**kpi_data))
            
            logger.info(f"Enhanced profile {profile.company_id} with realism score {profile.realism_score}")
            
        except Exception as e:
            logger.warning(f"LLM enhancement failed: {e}, using original profile")
        
        return profile

