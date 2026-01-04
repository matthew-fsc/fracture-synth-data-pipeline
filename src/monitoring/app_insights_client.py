"""
Application Insights Client

Provides integration with Azure Application Insights for monitoring.
"""

import logging
import os
from typing import Dict, Optional, Any
from datetime import datetime

try:
    from applicationinsights import TelemetryClient
    from applicationinsights.channel import (
        SynchronousQueue,
        SynchronousSender,
        TelemetryChannel
    )
    APP_INSIGHTS_AVAILABLE = True
except ImportError:
    APP_INSIGHTS_AVAILABLE = False
    logging.warning("Application Insights SDK not available. Install with: pip install applicationinsights")

logger = logging.getLogger(__name__)


class AppInsightsClient:
    """
    Application Insights client for telemetry.
    
    Supports:
    - Event tracking
    - Metric tracking
    - Exception tracking
    - Custom properties
    """
    
    def __init__(
        self,
        instrumentation_key: Optional[str] = None,
        connection_string: Optional[str] = None
    ):
        """
        Initialize Application Insights client.
        
        Args:
            instrumentation_key: Application Insights instrumentation key (legacy)
            connection_string: Application Insights connection string (preferred)
        """
        if not APP_INSIGHTS_AVAILABLE:
            logger.warning("Application Insights SDK not available")
            self.client = None
            return
        
        # Get credentials from parameters or environment
        if connection_string:
            self.connection_string = connection_string
        else:
            self.connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
        
        if instrumentation_key and not self.connection_string:
            # Legacy: use instrumentation key
            self.instrumentation_key = instrumentation_key
            self.connection_string = f"InstrumentationKey={instrumentation_key}"
        else:
            self.instrumentation_key = None
        
        if not self.connection_string:
            logger.warning("Application Insights connection string not provided")
            self.client = None
            return
        
        try:
            # Initialize telemetry channel
            channel = TelemetryChannel(
                queue=SynchronousQueue(),
                sender=SynchronousSender(self.connection_string)
            )
            
            # Initialize client
            if self.instrumentation_key:
                self.client = TelemetryClient(self.instrumentation_key, channel)
            else:
                # Extract instrumentation key from connection string
                key_part = [part for part in self.connection_string.split(";") if part.startswith("InstrumentationKey=")]
                if key_part:
                    key = key_part[0].split("=")[1]
                    self.client = TelemetryClient(key, channel)
                else:
                    logger.error("Could not extract instrumentation key from connection string")
                    self.client = None
        except Exception as e:
            logger.error(f"Failed to initialize Application Insights client: {e}")
            self.client = None
    
    def track_event(
        self,
        name: str,
        properties: Optional[Dict[str, str]] = None,
        measurements: Optional[Dict[str, float]] = None
    ):
        """
        Track a custom event.
        
        Args:
            name: Event name
            properties: Custom properties
            measurements: Custom measurements
        """
        if not self.client:
            return
        
        try:
            self.client.track_event(name, properties, measurements)
            self.client.flush()
        except Exception as e:
            logger.warning(f"Failed to track event: {e}")
    
    def track_metric(
        self,
        name: str,
        value: float,
        properties: Optional[Dict[str, str]] = None
    ):
        """
        Track a custom metric.
        
        Args:
            name: Metric name
            value: Metric value
            properties: Custom properties
        """
        if not self.client:
            return
        
        try:
            self.client.track_metric(name, value, properties=properties)
            self.client.flush()
        except Exception as e:
            logger.warning(f"Failed to track metric: {e}")
    
    def track_exception(
        self,
        exception: Exception,
        properties: Optional[Dict[str, str]] = None
    ):
        """
        Track an exception.
        
        Args:
            exception: Exception to track
            properties: Custom properties
        """
        if not self.client:
            return
        
        try:
            self.client.track_exception(exception, properties)
            self.client.flush()
        except Exception as e:
            logger.warning(f"Failed to track exception: {e}")
    
    def track_trace(
        self,
        message: str,
        severity_level: str = "Information",
        properties: Optional[Dict[str, str]] = None
    ):
        """
        Track a trace message.
        
        Args:
            message: Trace message
            severity_level: Severity level (Verbose, Information, Warning, Error, Critical)
            properties: Custom properties
        """
        if not self.client:
            return
        
        try:
            self.client.track_trace(message, severity_level, properties)
            self.client.flush()
        except Exception as e:
            logger.warning(f"Failed to track trace: {e}")

