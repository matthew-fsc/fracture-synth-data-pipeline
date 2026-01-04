"""
LLM-powered scenario generation from meeting transcripts.

This module ingests natural-language meeting transcripts and converts them
into structured requirement scenarios using Azure OpenAI Service.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from pydantic import BaseModel, Field, validator
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from openai import AzureOpenAI

logger = logging.getLogger(__name__)


class TranscriptInput(BaseModel):
    """Input model for meeting transcript."""
    transcript_id: str
    transcript_text: str
    meeting_date: datetime
    participants: List[str] = Field(default_factory=list)
    metadata: Dict[str, str] = Field(default_factory=dict)


class RequirementScenario(BaseModel):
    """Structured requirement scenario extracted from transcript."""
    scenario_id: str
    source_transcript_id: str
    business_context: str
    pain_points: List[str] = Field(default_factory=list)
    stakeholders: List[str] = Field(default_factory=list)
    urgency_level: str = Field(..., pattern="^(low|medium|high|critical)$")
    industry_domain: Optional[str] = None
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    confidence_score: float = Field(ge=0.0, le=1.0)


class ScenarioGenerator:
    """Generates requirement scenarios from transcripts using Azure OpenAI."""
    
    def __init__(
        self,
        azure_openai_endpoint: str,
        deployment_name: str,
        api_version: str = "2024-02-15-preview",
        key_vault_url: Optional[str] = None
    ):
        """
        Initialize the scenario generator.
        
        Args:
            azure_openai_endpoint: Azure OpenAI service endpoint
            deployment_name: Deployment name for GPT-4.1+ model
            api_version: API version to use
            key_vault_url: Optional Key Vault URL for credential retrieval
        """
        self.endpoint = azure_openai_endpoint
        self.deployment_name = deployment_name
        self.api_version = api_version
        
        # Initialize Azure credentials
        credential = DefaultAzureCredential()
        
        # Initialize Azure OpenAI client
        if key_vault_url:
            kv_client = SecretClient(vault_url=key_vault_url, credential=credential)
            api_key = kv_client.get_secret("azure-openai-api-key").value
        else:
            # Fallback to environment variable or managed identity
            api_key = None
        
        self.client = AzureOpenAI(
            azure_endpoint=azure_openai_endpoint,
            api_key=api_key,
            api_version=api_version
        )
    
    def extract_scenarios(
        self,
        transcript: TranscriptInput,
        max_scenarios: int = 10
    ) -> List[RequirementScenario]:
        """
        Extract requirement scenarios from a meeting transcript.
        
        Args:
            transcript: The input transcript
            max_scenarios: Maximum number of scenarios to extract
            
        Returns:
            List of extracted requirement scenarios
        """
        prompt = self._build_extraction_prompt(transcript, max_scenarios)
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert business analyst extracting structured requirement scenarios from meeting transcripts. Output valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            scenarios = []
            
            for idx, scenario_data in enumerate(result.get("scenarios", [])):
                scenario = RequirementScenario(
                    scenario_id=f"{transcript.transcript_id}_scenario_{idx+1}",
                    source_transcript_id=transcript.transcript_id,
                    **scenario_data
                )
                scenarios.append(scenario)
            
            logger.info(f"Extracted {len(scenarios)} scenarios from transcript {transcript.transcript_id}")
            return scenarios
            
        except Exception as e:
            logger.error(f"Error extracting scenarios: {e}", exc_info=True)
            raise
    
    def _build_extraction_prompt(
        self,
        transcript: TranscriptInput,
        max_scenarios: int
    ) -> str:
        """Build the prompt for scenario extraction."""
        return f"""
Extract requirement scenarios from the following meeting transcript.

Transcript:
{transcript.transcript_text}

Participants: {', '.join(transcript.participants)}
Meeting Date: {transcript.meeting_date.isoformat()}

Instructions:
1. Identify distinct requirement scenarios discussed in the meeting
2. Extract business context, pain points, and stakeholders for each
3. Assess urgency level (low, medium, high, critical)
4. Determine industry domain if mentioned
5. Provide confidence score (0.0-1.0) for each extraction

Output a JSON object with this structure:
{{
    "scenarios": [
        {{
            "business_context": "Brief description of the business situation",
            "pain_points": ["pain point 1", "pain point 2"],
            "stakeholders": ["stakeholder 1", "stakeholder 2"],
            "urgency_level": "high",
            "industry_domain": "technology",
            "confidence_score": 0.85
        }}
    ]
}}

Extract up to {max_scenarios} scenarios. Focus on operational system design requirements.
"""
    
    def enhance_scenario(
        self,
        scenario: RequirementScenario,
        additional_context: Optional[Dict] = None
    ) -> RequirementScenario:
        """
        Enhance a scenario with additional detail using LLM.
        
        Args:
            scenario: Base scenario to enhance
            additional_context: Optional additional context
            
        Returns:
            Enhanced scenario
        """
        prompt = f"""
Enhance the following requirement scenario with more detail and specificity.

Current Scenario:
- Business Context: {scenario.business_context}
- Pain Points: {', '.join(scenario.pain_points)}
- Stakeholders: {', '.join(scenario.stakeholders)}
- Urgency: {scenario.urgency_level}
- Industry: {scenario.industry_domain}

Additional Context: {json.dumps(additional_context) if additional_context else "None"}

Provide an enhanced version with:
- More specific business context
- Detailed, actionable pain points
- Complete stakeholder list
- Refined urgency assessment
- Industry-specific terminology

Output JSON matching the scenario structure.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert business analyst enhancing requirement scenarios."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.4,
                response_format={"type": "json_object"}
            )
            
            enhanced_data = json.loads(response.choices[0].message.content)
            
            # Update scenario with enhanced data
            scenario.business_context = enhanced_data.get("business_context", scenario.business_context)
            scenario.pain_points = enhanced_data.get("pain_points", scenario.pain_points)
            scenario.stakeholders = enhanced_data.get("stakeholders", scenario.stakeholders)
            scenario.urgency_level = enhanced_data.get("urgency_level", scenario.urgency_level)
            scenario.industry_domain = enhanced_data.get("industry_domain", scenario.industry_domain)
            
            return scenario
            
        except Exception as e:
            logger.error(f"Error enhancing scenario: {e}", exc_info=True)
            return scenario  # Return original on error

