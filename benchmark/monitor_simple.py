"""Simple resource monitoring and alerting for benchmarks."""

import os
import psutil
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass

from utils.log import log
from utils.simple_telegram import send_message

@dataclass
class ResourceMetrics:
    """Basic resource metrics."""
    cpu_percent: float
    memory_percent: float 
    memory_used_mb: float
    disk_used_percent: float

class SimpleMonitor:
    def __init__(self, notify_telegram: bool = False):
        """Initialize simple monitor."""
        self.notify_telegram = notify_telegram
        self.metrics_history = []
        self.alert_count = 0

    def check_resources(self) -> ResourceMetrics:
        """Get current resource metrics."""
        metrics = ResourceMetrics(
            cpu_percent=psutil.cpu_percent(),
            memory_percent=psutil.virtual_memory().percent,
            memory_used_mb=psutil.virtual_memory().used / 1024 / 1024,
            disk_used_percent=psutil.disk_usage('/').percent
        )
        
        self.metrics_history.append({
            "timestamp": datetime.now().isoformat(),
            **metrics.__dict__
        })
        
        return metrics

    def check_alerts(self, metrics: ResourceMetrics):
        """Check for resource alerts."""
        alerts = []
        
        if metrics.cpu_percent > 80:
            alerts.append(f"High CPU usage: {metrics.cpu_percent:.1f}%")
            
        if metrics.memory_percent > 80:
            alerts.append(f"High memory usage: {metrics.memory_percent:.1f}%")
            
        if metrics.disk_used_percent > 85:
            alerts.append(f"High disk usage: {metrics.disk_used_percent:.1f}%")
        
        # Log alerts
        for alert in alerts:
            log(f"ALERT: {alert}")
            self.alert_count += 1
            
            # Send Telegram notification if enabled
            if self.notify_telegram:
                try:
                    send_message(f"🚨 Resource Alert: {alert}")
                except Exception as e:
                    log(f"Failed to send Telegram notification: {e}")
        
        return alerts

    def get_summary(self) -> Dict[str, Any]:
        """Get monitoring summary."""
        if not self.metrics_history:
            return {}
            
        # Calculate basic stats
        cpu_values = [m["cpu_percent"] for m in self.metrics_history]
        memory_values = [m["memory_percent"] for m in self.metrics_history]
        
        return {
            "duration": len(self.metrics_history),
            "alerts": self.alert_count,
            "cpu": {
                "min": min(cpu_values),
                "max": max(cpu_values),
                "avg": sum(cpu_values) / len(cpu_values)
            },
            "memory": {
                "min": min(memory_values),
                "max": max(memory_values),
                "avg": sum(memory_values) / len(memory_values)
            },
            "latest": self.metrics_history[-1]
        }

def create_monitor(notify_telegram: bool = False) -> SimpleMonitor:
    """Create simple resource monitor."""
    return SimpleMonitor(notify_telegram)
