"""
Monitoring and Observability Module

Provides:
- Application Insights integration
- Pipeline execution logging
- Error tracking and alerting
- Performance metrics
- Cost tracking
"""

from .pipeline_monitor import PipelineMonitor, ExecutionMetrics
from .app_insights_client import AppInsightsClient

__all__ = [
    "PipelineMonitor",
    "ExecutionMetrics",
    "AppInsightsClient",
]

