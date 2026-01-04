"""
Pipeline Monitoring and Observability

Tracks pipeline execution metrics, errors, and performance.
"""

import logging
import time
from datetime import datetime
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import json

logger = logging.getLogger(__name__)


@dataclass
class ExecutionMetrics:
    """Pipeline execution metrics."""
    execution_id: str
    pipeline_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    status: str = "running"  # running, completed, failed
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    cost_usd: float = 0.0
    tokens_used: int = 0
    samples_generated: int = 0
    validation_passed: bool = False


class PipelineMonitor:
    """
    Monitor pipeline execution with metrics tracking and logging.
    """
    
    def __init__(
        self,
        execution_id: str,
        pipeline_name: str,
        metrics_dir: Optional[Path] = None,
        app_insights_client: Optional[Any] = None
    ):
        """
        Initialize pipeline monitor.
        
        Args:
            execution_id: Unique execution identifier
            pipeline_name: Name of the pipeline
            metrics_dir: Directory to save metrics
            app_insights_client: Optional Application Insights client
        """
        self.execution_id = execution_id
        self.pipeline_name = pipeline_name
        self.metrics_dir = metrics_dir or Path("data/metrics")
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self.app_insights_client = app_insights_client
        
        self.metrics = ExecutionMetrics(
            execution_id=execution_id,
            pipeline_name=pipeline_name,
            start_time=datetime.utcnow()
        )
        
        self.start_time = time.time()
    
    def record_metric(self, key: str, value: Any):
        """Record a custom metric."""
        self.metrics.metrics[key] = value
        
        # Also log to Application Insights if available
        if self.app_insights_client:
            try:
                self.app_insights_client.track_metric(
                    name=f"{self.pipeline_name}.{key}",
                    value=value,
                    properties={"execution_id": self.execution_id}
                )
            except Exception as e:
                logger.warning(f"Failed to track metric in Application Insights: {e}")
    
    def record_cost(self, cost: float):
        """Record cost for this execution."""
        self.metrics.cost_usd += cost
        self.record_metric("cost_usd", self.metrics.cost_usd)
    
    def record_tokens(self, tokens: int):
        """Record token usage."""
        self.metrics.tokens_used += tokens
        self.record_metric("tokens_used", self.metrics.tokens_used)
    
    def record_samples_generated(self, count: int):
        """Record number of samples generated."""
        self.metrics.samples_generated = count
        self.record_metric("samples_generated", count)
    
    def record_validation_result(self, passed: bool):
        """Record validation result."""
        self.metrics.validation_passed = passed
        self.record_metric("validation_passed", passed)
    
    def complete(self, success: bool = True, error_message: Optional[str] = None):
        """
        Mark execution as complete.
        
        Args:
            success: Whether execution was successful
            error_message: Error message if failed
        """
        self.metrics.end_time = datetime.utcnow()
        self.metrics.duration_seconds = time.time() - self.start_time
        self.metrics.status = "completed" if success else "failed"
        self.metrics.error_message = error_message
        
        # Save metrics
        self._save_metrics()
        
        # Log to Application Insights
        if self.app_insights_client:
            try:
                if success:
                    self.app_insights_client.track_event(
                        name=f"{self.pipeline_name}.completed",
                        properties={
                            "execution_id": self.execution_id,
                            "duration_seconds": self.metrics.duration_seconds,
                            "cost_usd": self.metrics.cost_usd,
                            "tokens_used": self.metrics.tokens_used,
                            "samples_generated": self.metrics.samples_generated
                        }
                    )
                else:
                    self.app_insights_client.track_exception(
                        exception=Exception(error_message or "Pipeline failed"),
                        properties={
                            "execution_id": self.execution_id,
                            "pipeline_name": self.pipeline_name
                        }
                    )
            except Exception as e:
                logger.warning(f"Failed to log to Application Insights: {e}")
    
    def _save_metrics(self):
        """Save metrics to file."""
        metrics_file = self.metrics_dir / f"{self.execution_id}.json"
        try:
            metrics_dict = {
                "execution_id": self.metrics.execution_id,
                "pipeline_name": self.metrics.pipeline_name,
                "start_time": self.metrics.start_time.isoformat(),
                "end_time": self.metrics.end_time.isoformat() if self.metrics.end_time else None,
                "duration_seconds": self.metrics.duration_seconds,
                "status": self.metrics.status,
                "error_message": self.metrics.error_message,
                "metrics": self.metrics.metrics,
                "cost_usd": self.metrics.cost_usd,
                "tokens_used": self.metrics.tokens_used,
                "samples_generated": self.metrics.samples_generated,
                "validation_passed": self.metrics.validation_passed
            }
            
            with open(metrics_file, 'w') as f:
                json.dump(metrics_dict, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")
    
    def get_metrics(self) -> ExecutionMetrics:
        """Get current metrics."""
        return self.metrics

