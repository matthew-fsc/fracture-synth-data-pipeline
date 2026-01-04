"""
System requirement manifest builder.

Produces labeled requirement manifests that mirror real consulting engagements,
including dependency graphs, system components, and operational requirements.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, validator
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from openai import AzureOpenAI

from .company_profiler import CompanyProfile
from .synth_llm import RequirementScenario

logger = logging.getLogger(__name__)


class RequirementPriority(str, Enum):
    """Requirement priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SystemComponent(BaseModel):
    """System component definition."""
    component_id: str
    component_name: str
    component_type: str  # e.g., "workflow_engine", "data_ingestion", "notification_service"
    description: str
    dependencies: List[str] = Field(default_factory=list, description="Component IDs this depends on")
    required_capabilities: List[str] = Field(default_factory=list)


class Requirement(BaseModel):
    """Individual system requirement."""
    requirement_id: str
    requirement_type: str  # e.g., "functional", "non-functional", "compliance", "performance"
    title: str
    description: str
    priority: RequirementPriority
    source_pain_point: Optional[str] = None
    affected_components: List[str] = Field(default_factory=list, description="Component IDs")
    acceptance_criteria: List[str] = Field(default_factory=list)
    estimated_effort: Optional[str] = None  # e.g., "2 weeks", "1 month"


class DependencyGraph(BaseModel):
    """Dependency graph for system components."""
    nodes: List[Dict[str, str]] = Field(default_factory=list, description="Component nodes")
    edges: List[Dict[str, str]] = Field(default_factory=list, description="Dependency edges")
    cycles: List[List[str]] = Field(default_factory=list, description="Detected cycles")


class SystemManifest(BaseModel):
    """Complete system requirement manifest."""
    manifest_id: str
    manifest_version: str = "1.0.0"
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Source data
    company_profile: CompanyProfile
    source_scenarios: List[RequirementScenario]
    
    # Requirements
    requirements: List[Requirement] = Field(default_factory=list)
    components: List[SystemComponent] = Field(default_factory=list)
    dependency_graph: DependencyGraph = Field(default_factory=DependencyGraph)
    
    # Metadata
    total_requirements: int = 0
    total_components: int = 0
    estimated_timeline: Optional[str] = None
    complexity_score: float = Field(ge=0.0, le=10.0, description="Overall complexity score")
    
    @validator('total_requirements', always=True)
    def set_total_requirements(cls, v, values):
        if 'requirements' in values:
            return len(values['requirements'])
        return v
    
    @validator('total_components', always=True)
    def set_total_components(cls, v, values):
        if 'components' in values:
            return len(values['components'])
        return v


class ManifestBuilder:
    """Builds system requirement manifests from scenarios and company profiles."""
    
    def __init__(
        self,
        azure_openai_endpoint: str,
        deployment_name: str,
        api_version: str = "2024-02-15-preview",
        key_vault_url: Optional[str] = None
    ):
        """
        Initialize the manifest builder.
        
        Args:
            azure_openai_endpoint: Azure OpenAI service endpoint
            deployment_name: Deployment name
            api_version: API version
            key_vault_url: Optional Key Vault URL
        """
        self.endpoint = azure_openai_endpoint
        self.deployment_name = deployment_name
        self.api_version = api_version
        
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
    
    def build_manifest(
        self,
        company_profile: CompanyProfile,
        scenarios: List[RequirementScenario],
        manifest_id: Optional[str] = None
    ) -> SystemManifest:
        """
        Build a system requirement manifest from company profile and scenarios.
        
        Args:
            company_profile: The company profile
            scenarios: List of requirement scenarios
            manifest_id: Optional manifest ID
            
        Returns:
            Complete system manifest
        """
        if not manifest_id:
            manifest_id = f"manifest_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Generate requirements from scenarios and pain points
        requirements = self._generate_requirements(company_profile, scenarios)
        
        # Generate system components
        components = self._generate_components(requirements, company_profile)
        
        # Build dependency graph
        dependency_graph = self._build_dependency_graph(components)
        
        # Calculate complexity
        complexity_score = self._calculate_complexity(requirements, components, dependency_graph)
        
        manifest = SystemManifest(
            manifest_id=manifest_id,
            company_profile=company_profile,
            source_scenarios=scenarios,
            requirements=requirements,
            components=components,
            dependency_graph=dependency_graph,
            complexity_score=complexity_score
        )
        
        return manifest
    
    def _generate_requirements(
        self,
        company_profile: CompanyProfile,
        scenarios: List[RequirementScenario]
    ) -> List[Requirement]:
        """Generate requirements from scenarios and pain points."""
        prompt = f"""
Generate system requirements for an enterprise operational system based on:

Company Profile:
- Industry: {company_profile.industry}
- Employees: {company_profile.employee_count}
- Departments: {', '.join(company_profile.departments)}
- Operational Metrics:
  * Daily Tickets: {company_profile.operational_metrics.ticket_volume_daily}
  * Handoff Delay: {company_profile.operational_metrics.handoff_delay_avg_hours} hours
  * Handoff Failures: {company_profile.operational_metrics.handoff_failure_rate * 100:.1f}%
  * Advisors: {company_profile.operational_metrics.advisor_count}
  * Realtime Ingestion: {company_profile.operational_metrics.realtime_ingestion_volume_daily}/day

Pain Points:
{chr(10).join(f"- {pp}" for pp in company_profile.pain_points)}

Scenarios:
{chr(10).join(f"- {s.business_context}: {', '.join(s.pain_points)}" for s in scenarios)}

Generate comprehensive system requirements including:
1. Functional requirements (workflow management, handoff tracking, ticket routing)
2. Non-functional requirements (performance, scalability, reliability)
3. Compliance requirements (based on industry)
4. Integration requirements (departments, advisors, external systems)
5. Real-time processing requirements
6. Data quality and validation requirements

For each requirement, provide:
- requirement_type: functional, non-functional, compliance, performance, integration
- title: Clear requirement title
- description: Detailed description
- priority: low, medium, high, critical (based on urgency and impact)
- source_pain_point: Which pain point this addresses
- acceptance_criteria: List of measurable acceptance criteria
- estimated_effort: Rough estimate (e.g., "2 weeks", "1 month")

Output JSON with a "requirements" array.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert system architect generating enterprise operational system requirements."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.4,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            requirements = []
            
            for idx, req_data in enumerate(result.get("requirements", [])):
                requirement = Requirement(
                    requirement_id=f"req_{idx+1:03d}",
                    priority=RequirementPriority(req_data.get("priority", "medium")),
                    **{k: v for k, v in req_data.items() if k != "priority"}
                )
                requirements.append(requirement)
            
            logger.info(f"Generated {len(requirements)} requirements")
            return requirements
            
        except Exception as e:
            logger.error(f"Error generating requirements: {e}", exc_info=True)
            raise
    
    def _generate_components(
        self,
        requirements: List[Requirement],
        company_profile: CompanyProfile
    ) -> List[SystemComponent]:
        """Generate system components from requirements."""
        prompt = f"""
Based on these system requirements, identify the core system components needed:

Requirements:
{chr(10).join(f"- [{r.requirement_type}] {r.title}: {r.description[:100]}..." for r in requirements[:20])}

Company Context:
- Departments: {', '.join(company_profile.departments)}
- Daily Ticket Volume: {company_profile.operational_metrics.ticket_volume_daily}
- Realtime Ingestion: {company_profile.operational_metrics.realtime_ingestion_volume_daily}/day
- Advisors: {company_profile.operational_metrics.advisor_count}

Identify system components such as:
- Workflow orchestration engine
- Ticket/work item management system
- Handoff tracking service
- Real-time data ingestion pipeline
- Notification service
- Department routing service
- Advisor assignment service
- Compliance monitoring service
- KPI/metrics dashboard
- Data validation service
- etc.

For each component, provide:
- component_name: Clear component name
- component_type: Type/category
- description: What it does
- required_capabilities: List of key capabilities
- dependencies: Other component names this depends on

Output JSON with a "components" array.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert system architect designing enterprise system components."
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
            components = []
            component_name_to_id = {}
            
            for idx, comp_data in enumerate(result.get("components", [])):
                component_id = f"comp_{idx+1:03d}"
                component_name_to_id[comp_data["component_name"]] = component_id
                
                component = SystemComponent(
                    component_id=component_id,
                    **comp_data
                )
                components.append(component)
            
            # Resolve dependency references
            for component in components:
                resolved_deps = []
                for dep_name in component.dependencies:
                    if dep_name in component_name_to_id:
                        resolved_deps.append(component_name_to_id[dep_name])
                component.dependencies = resolved_deps
            
            # Link requirements to components
            self._link_requirements_to_components(requirements, components)
            
            logger.info(f"Generated {len(components)} components")
            return components
            
        except Exception as e:
            logger.error(f"Error generating components: {e}", exc_info=True)
            raise
    
    def _link_requirements_to_components(
        self,
        requirements: List[Requirement],
        components: List[SystemComponent]
    ):
        """Link requirements to components based on content matching."""
        # Simple keyword-based linking (could be enhanced with LLM)
        for requirement in requirements:
            requirement_lower = requirement.title.lower() + " " + requirement.description.lower()
            
            for component in components:
                component_lower = component.component_name.lower() + " " + component.description.lower()
                
                # Check for keyword matches
                keywords = component.component_type.split("_") + component.component_name.split()
                if any(keyword.lower() in requirement_lower for keyword in keywords if len(keyword) > 3):
                    if component.component_id not in requirement.affected_components:
                        requirement.affected_components.append(component.component_id)
    
    def _build_dependency_graph(self, components: List[SystemComponent]) -> DependencyGraph:
        """Build dependency graph from components."""
        nodes = [
            {
                "id": comp.component_id,
                "name": comp.component_name,
                "type": comp.component_type
            }
            for comp in components
        ]
        
        edges = []
        for component in components:
            for dep_id in component.dependencies:
                edges.append({
                    "from": dep_id,
                    "to": component.component_id,
                    "type": "depends_on"
                })
        
        # Detect cycles (simple DFS)
        cycles = self._detect_cycles(components)
        
        return DependencyGraph(nodes=nodes, edges=edges, cycles=cycles)
    
    def _detect_cycles(self, components: List[SystemComponent]) -> List[List[str]]:
        """Detect cycles in dependency graph."""
        component_map = {comp.component_id: comp for comp in components}
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(comp_id: str, path: List[str]):
            if comp_id in rec_stack:
                # Found cycle
                cycle_start = path.index(comp_id)
                cycles.append(path[cycle_start:] + [comp_id])
                return
            
            if comp_id in visited:
                return
            
            visited.add(comp_id)
            rec_stack.add(comp_id)
            
            if comp_id in component_map:
                for dep_id in component_map[comp_id].dependencies:
                    dfs(dep_id, path + [comp_id])
            
            rec_stack.remove(comp_id)
        
        for comp in components:
            if comp.component_id not in visited:
                dfs(comp.component_id, [])
        
        return cycles
    
    def _calculate_complexity(
        self,
        requirements: List[Requirement],
        components: List[SystemComponent],
        dependency_graph: DependencyGraph
    ) -> float:
        """Calculate overall system complexity score (0-10)."""
        base_complexity = len(requirements) * 0.1 + len(components) * 0.2
        
        # Add complexity for dependencies
        dependency_complexity = len(dependency_graph.edges) * 0.05
        
        # Add complexity for cycles
        cycle_complexity = len(dependency_graph.cycles) * 0.5
        
        # Add complexity for critical requirements
        critical_count = sum(1 for r in requirements if r.priority == RequirementPriority.CRITICAL)
        critical_complexity = critical_count * 0.3
        
        total = base_complexity + dependency_complexity + cycle_complexity + critical_complexity
        
        return min(10.0, total)

