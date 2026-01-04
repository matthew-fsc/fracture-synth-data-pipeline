"""
Azure OpenAI Service Manager

Provides centralized management for Azure OpenAI API calls with:
- Token usage tracking
- Cost monitoring and reporting
- Model version management
- Integration with Azure Key Vault
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
from pathlib import Path
import json

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from openai import AzureOpenAI
from openai.types.chat import ChatCompletion

logger = logging.getLogger(__name__)


@dataclass
class TokenUsage:
    """Token usage statistics for a single API call."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    model: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    cost_usd: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "model": self.model,
            "timestamp": self.timestamp.isoformat(),
            "cost_usd": self.cost_usd
        }


@dataclass
class CostTracker:
    """Track costs over time periods."""
    daily_costs: Dict[str, float] = field(default_factory=dict)  # date -> cost
    monthly_costs: Dict[str, float] = field(default_factory=dict)  # YYYY-MM -> cost
    model_costs: Dict[str, float] = field(default_factory=dict)  # model -> total cost
    total_cost: float = 0.0
    
    def add_cost(self, cost: float, model: str, timestamp: Optional[datetime] = None):
        """Add cost to tracker."""
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        date_str = timestamp.strftime("%Y-%m-%d")
        month_str = timestamp.strftime("%Y-%m")
        
        self.daily_costs[date_str] = self.daily_costs.get(date_str, 0.0) + cost
        self.monthly_costs[month_str] = self.monthly_costs.get(month_str, 0.0) + cost
        self.model_costs[model] = self.model_costs.get(model, 0.0) + cost
        self.total_cost += cost
    
    def get_daily_cost(self, date: Optional[str] = None) -> float:
        """Get cost for a specific date (default: today)."""
        if date is None:
            date = datetime.utcnow().strftime("%Y-%m-%d")
        return self.daily_costs.get(date, 0.0)
    
    def get_monthly_cost(self, month: Optional[str] = None) -> float:
        """Get cost for a specific month (default: current month)."""
        if month is None:
            month = datetime.utcnow().strftime("%Y-%m")
        return self.monthly_costs.get(month, 0.0)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "daily_costs": self.daily_costs,
            "monthly_costs": self.monthly_costs,
            "model_costs": self.model_costs,
            "total_cost": self.total_cost
        }


# Pricing per 1M tokens (as of 2024, adjust as needed)
MODEL_PRICING = {
    "gpt-4-turbo": {"input": 10.0, "output": 30.0},  # $10/$30 per 1M tokens
    "gpt-4": {"input": 30.0, "output": 60.0},
    "gpt-35-turbo": {"input": 0.5, "output": 1.5},
    "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
    "gpt-4o": {"input": 5.0, "output": 15.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.6},
}


class OpenAIManager:
    """
    Centralized Azure OpenAI service manager.
    
    Provides token tracking, cost monitoring, and model management.
    """
    
    def __init__(
        self,
        azure_openai_endpoint: str,
        deployment_name: str,
        key_vault_url: Optional[str] = None,
        api_version: str = "2024-02-15-preview",
        usage_log_path: Optional[Path] = None
    ):
        """
        Initialize OpenAI manager.
        
        Args:
            azure_openai_endpoint: Azure OpenAI endpoint URL
            deployment_name: Deployment name (model)
            key_vault_url: Optional Key Vault URL for credentials
            api_version: API version to use
            usage_log_path: Optional path to log usage statistics
        """
        self.endpoint = azure_openai_endpoint
        self.deployment_name = deployment_name
        self.api_version = api_version
        self.usage_log_path = usage_log_path or Path("data/logs/usage.json")
        self.usage_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize client
        self._init_client(key_vault_url)
        
        # Tracking
        self.token_usage_history: List[TokenUsage] = []
        self.cost_tracker = CostTracker()
        
        # Load historical usage if exists
        self._load_usage_history()
    
    def _init_client(self, key_vault_url: Optional[str]):
        """Initialize Azure OpenAI client."""
        credential = DefaultAzureCredential()
        api_key = None
        
        if key_vault_url:
            try:
                kv_client = SecretClient(vault_url=key_vault_url, credential=credential)
                api_key = kv_client.get_secret("azure-openai-api-key").value
            except Exception as e:
                logger.warning(f"Could not load API key from Key Vault: {e}")
        
        if not api_key:
            # Try environment variable
            import os
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("Azure OpenAI API key not found in Key Vault or environment")
        
        self.client = AzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=api_key,
            api_version=self.api_version
        )
    
    def _load_usage_history(self):
        """Load usage history from file."""
        if self.usage_log_path.exists():
            try:
                with open(self.usage_log_path, 'r') as f:
                    data = json.load(f)
                    self.token_usage_history = [
                        TokenUsage(**item) if isinstance(item, dict) else item
                        for item in data.get("usage_history", [])
                    ]
                    cost_data = data.get("cost_tracker", {})
                    if cost_data:
                        self.cost_tracker = CostTracker(**cost_data)
            except Exception as e:
                logger.warning(f"Could not load usage history: {e}")
    
    def _save_usage_history(self):
        """Save usage history to file."""
        try:
            data = {
                "usage_history": [usage.to_dict() for usage in self.token_usage_history[-1000:]],  # Keep last 1000
                "cost_tracker": self.cost_tracker.to_dict()
            }
            with open(self.usage_log_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Could not save usage history: {e}")
    
    def _calculate_cost(self, usage: TokenUsage) -> float:
        """Calculate cost based on token usage and model pricing."""
        model_key = self.deployment_name.lower()
        
        # Find matching pricing
        pricing = None
        for key, price in MODEL_PRICING.items():
            if key in model_key or model_key in key:
                pricing = price
                break
        
        if not pricing:
            logger.warning(f"No pricing found for model {self.deployment_name}, using default")
            pricing = MODEL_PRICING.get("gpt-35-turbo", {"input": 0.5, "output": 1.5})
        
        # Calculate cost (pricing is per 1M tokens)
        input_cost = (usage.prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (usage.completion_tokens / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost
        
        return total_cost
    
    def _track_usage(self, response: ChatCompletion, timestamp: Optional[datetime] = None):
        """Track token usage from API response."""
        if not response.usage:
            return
        
        usage = TokenUsage(
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
            model=response.model or self.deployment_name,
            timestamp=timestamp or datetime.utcnow()
        )
        
        usage.cost_usd = self._calculate_cost(usage)
        
        self.token_usage_history.append(usage)
        self.cost_tracker.add_cost(usage.cost_usd, usage.model, usage.timestamp)
        
        # Save periodically (every 10 calls)
        if len(self.token_usage_history) % 10 == 0:
            self._save_usage_history()
        
        logger.debug(
            f"Token usage: {usage.total_tokens} tokens "
            f"(${usage.cost_usd:.4f})"
        )
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatCompletion:
        """
        Create chat completion with usage tracking.
        
        Args:
            messages: List of message dictionaries
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional arguments for API call
            
        Returns:
            ChatCompletion response
        """
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            self._track_usage(response)
            
            return response
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise
    
    def get_usage_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get usage statistics for a date range.
        
        Args:
            start_date: Start date (default: 30 days ago)
            end_date: End date (default: now)
            
        Returns:
            Dictionary with usage statistics
        """
        if start_date is None:
            start_date = datetime.utcnow() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.utcnow()
        
        filtered_usage = [
            u for u in self.token_usage_history
            if start_date <= u.timestamp <= end_date
        ]
        
        if not filtered_usage:
            return {
                "total_tokens": 0,
                "total_cost": 0.0,
                "call_count": 0,
                "avg_tokens_per_call": 0.0
            }
        
        total_tokens = sum(u.total_tokens for u in filtered_usage)
        total_cost = sum(u.cost_usd for u in filtered_usage)
        
        return {
            "total_tokens": total_tokens,
            "total_prompt_tokens": sum(u.prompt_tokens for u in filtered_usage),
            "total_completion_tokens": sum(u.completion_tokens for u in filtered_usage),
            "total_cost": total_cost,
            "call_count": len(filtered_usage),
            "avg_tokens_per_call": total_tokens / len(filtered_usage),
            "avg_cost_per_call": total_cost / len(filtered_usage),
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost summary."""
        return {
            "total_cost": self.cost_tracker.total_cost,
            "daily_cost": self.cost_tracker.get_daily_cost(),
            "monthly_cost": self.cost_tracker.get_monthly_cost(),
            "by_model": self.cost_tracker.model_costs,
            "daily_breakdown": self.cost_tracker.daily_costs,
            "monthly_breakdown": self.cost_tracker.monthly_costs
        }
    
    def save_usage_report(self, output_path: Optional[Path] = None):
        """Save comprehensive usage report."""
        if output_path is None:
            output_path = Path("data/logs/usage_report.json")
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "cost_summary": self.get_cost_summary(),
            "usage_stats_30d": self.get_usage_stats(),
            "recent_usage": [u.to_dict() for u in self.token_usage_history[-100:]]
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Usage report saved to {output_path}")

