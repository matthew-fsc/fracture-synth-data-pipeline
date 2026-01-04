"""
Realism validation using LLM-as-a-judge and statistical checks.

Validates that synthetic data is believable and realistic.
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

from pydantic import BaseModel, Field
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from openai import AzureOpenAI

logger = logging.getLogger(__name__)


class RealismScore(BaseModel):
    """Realism score breakdown."""
    overall_score: float = Field(ge=0.0, le=1.0)
    business_context_score: float = Field(ge=0.0, le=1.0)
    metrics_realism_score: float = Field(ge=0.0, le=1.0)
    pain_point_alignment_score: float = Field(ge=0.0, le=1.0)
    industry_consistency_score: float = Field(ge=0.0, le=1.0)
    issues: List[str] = Field(default_factory=list)
    passed: bool = False
    threshold: float = 0.7


class RealismValidator:
    """Validates realism of synthetic data using LLM and statistical methods."""
    
    def __init__(
        self,
        azure_openai_endpoint: str,
        deployment_name: str,
        api_version: str = "2024-02-15-preview",
        key_vault_url: Optional[str] = None,
        threshold: float = 0.7
    ):
        """
        Initialize the realism validator.
        
        Args:
            azure_openai_endpoint: Azure OpenAI endpoint
            deployment_name: Deployment name
            api_version: API version
            key_vault_url: Optional Key Vault URL
            threshold: Minimum realism score to pass (0-1)
        """
        self.threshold = threshold
        
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
        self.deployment_name = deployment_name
    
    def validate_company_profile(
        self,
        company_profile: Dict
    ) -> RealismScore:
        """
        Validate company profile realism.
        
        Args:
            company_profile: Company profile dictionary
            
        Returns:
            Realism score with breakdown
        """
        prompt = f"""
Evaluate the realism of this synthetic company profile:

Company: {company_profile.get('company_name')}
Industry: {company_profile.get('industry')}
Employees: {company_profile.get('employee_count')}
Revenue: ${company_profile.get('revenue_range_min'):,.0f} - ${company_profile.get('revenue_range_max'):,.0f}

Operational Metrics:
- Daily Tickets: {company_profile.get('operational_metrics', {}).get('ticket_volume_daily')}
- Handoff Delay: {company_profile.get('operational_metrics', {}).get('handoff_delay_avg_hours')} hours
- Handoff Failures: {company_profile.get('operational_metrics', {}).get('handoff_failure_rate', 0) * 100:.1f}%
- Advisors: {company_profile.get('operational_metrics', {}).get('advisor_count')}
- Departments: {company_profile.get('operational_metrics', {}).get('department_count')}

Pain Points:
{chr(10).join(f"- {pp}" for pp in company_profile.get('pain_points', []))}

Evaluate on these dimensions (0.0-1.0 each):
1. Business Context: Are revenue, employees, and industry aligned?
2. Metrics Realism: Are operational metrics believable for this company size?
3. Pain Point Alignment: Do pain points logically follow from the metrics?
4. Industry Consistency: Is everything consistent with the stated industry?

Also identify any specific issues or inconsistencies.

Output JSON with:
{{
    "overall_score": 0.85,
    "business_context_score": 0.9,
    "metrics_realism_score": 0.8,
    "pain_point_alignment_score": 0.85,
    "industry_consistency_score": 0.9,
    "issues": ["Issue 1", "Issue 2"]
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert business analyst evaluating data realism."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            score = RealismScore(
                overall_score=float(result.get("overall_score", 0.0)),
                business_context_score=float(result.get("business_context_score", 0.0)),
                metrics_realism_score=float(result.get("metrics_realism_score", 0.0)),
                pain_point_alignment_score=float(result.get("pain_point_alignment_score", 0.0)),
                industry_consistency_score=float(result.get("industry_consistency_score", 0.0)),
                issues=result.get("issues", []),
                threshold=self.threshold
            )
            
            score.passed = score.overall_score >= self.threshold
            
            return score
            
        except Exception as e:
            logger.error(f"Error validating realism: {e}", exc_info=True)
            # Return failing score on error
            return RealismScore(
                overall_score=0.0,
                business_context_score=0.0,
                metrics_realism_score=0.0,
                pain_point_alignment_score=0.0,
                industry_consistency_score=0.0,
                issues=[f"Validation error: {str(e)}"],
                passed=False,
                threshold=self.threshold
            )
    
    def validate_requirement_scenario(
        self,
        scenario: Dict
    ) -> RealismScore:
        """
        Validate requirement scenario realism.
        
        Args:
            scenario: Requirement scenario dictionary
            
        Returns:
            Realism score
        """
        prompt = f"""
Evaluate the realism of this requirement scenario:

Business Context: {scenario.get('business_context')}
Pain Points: {', '.join(scenario.get('pain_points', []))}
Stakeholders: {', '.join(scenario.get('stakeholders', []))}
Urgency: {scenario.get('urgency_level')}
Industry: {scenario.get('industry_domain')}

Evaluate:
1. Completeness: Is the scenario complete and actionable?
2. Ambiguity: Is it clear and unambiguous?
3. Solution Applicability: Can this lead to concrete system requirements?
4. Realism: Does this sound like a real consulting engagement scenario?

Output JSON with scores (0.0-1.0) and issues.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert evaluating requirement scenarios."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Map scenario-specific scores to standard format
            score = RealismScore(
                overall_score=float(result.get("overall_score", 0.0)),
                business_context_score=float(result.get("completeness_score", 0.0)),
                metrics_realism_score=float(result.get("realism_score", 0.0)),
                pain_point_alignment_score=float(result.get("solution_applicability_score", 0.0)),
                industry_consistency_score=float(result.get("ambiguity_score", 0.0)),
                issues=result.get("issues", []),
                threshold=self.threshold
            )
            
            score.passed = score.overall_score >= self.threshold
            
            return score
            
        except Exception as e:
            logger.error(f"Error validating scenario: {e}", exc_info=True)
            return RealismScore(
                overall_score=0.0,
                issues=[f"Validation error: {str(e)}"],
                passed=False,
                threshold=self.threshold
            )

