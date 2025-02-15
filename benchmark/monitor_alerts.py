"""Resource monitoring alerts and thresholds."""

import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from utils.log import log
from benchmark.alert_notifications import (
    AlertSeverity,
    ResourceThresholdManager,
    create_default_notifier,
    AlertNotifier
)

@dataclass
class ResourceThresholds:
    """Resource threshold configuration."""
    cpu_percent: float = 80.0
    memory_percent: float = 80.0
    memory_mb: float = 1024.0  # 1GB
    swap_mb: float = 512.0     # 512MB
    disk_read_mbs: float = 100.0
    disk_write_mbs: float = 100.0
    network_sent_mbs: float = 50.0
    network_recv_mbs: float = 50.0
    max_threads: int = 100
    max_processes: int = 20

@dataclass
class ResourceAlert:
    """Resource alert information."""
    timestamp: float
    resource: str
    value: float
    threshold: float
    message: str
    severity: AlertSeverity = AlertSeverity.WARNING

class ResourceAlertManager:
    def __init__(self, alert_dir: str = "benchmark/alerts",
                 thresholds: Optional[ResourceThresholds] = None,
                 notifier: Optional[AlertNotifier] = None):
        """Initialize alert manager."""
        self.alert_dir = alert_dir
        self.base_thresholds = thresholds or ResourceThresholds()
        self.threshold_manager = ResourceThresholdManager()
        self.notifier = notifier or create_default_notifier()
        self.alerts: List[ResourceAlert] = []
        
        os.makedirs(alert_dir, exist_ok=True)

    def check_metrics(self, metrics: Dict[str, Any]) -> List[ResourceAlert]:
        """Check metrics against thresholds with severity levels."""
        # Get alerts from threshold manager
        severity_alerts = self.threshold_manager.check_metrics(metrics)
        
        # Create ResourceAlert objects
        alerts = []
        for alert_data in severity_alerts:
            alert = ResourceAlert(
                timestamp=alert_data["timestamp"],
                resource=alert_data["resource"],
                value=alert_data["value"],
                threshold=alert_data["threshold"],
                message=alert_data["message"],
                severity=alert_data["severity"]
            )
            alerts.append(alert)
            
            # Send notification if configured
            if self.notifier:
                self.notifier.notify(alert_data)
        
        # Store alerts
        self.alerts.extend(alerts)

        # Log high severity alerts
        for alert in alerts:
            if alert.severity in [AlertSeverity.ERROR, AlertSeverity.CRITICAL]:
                log(f"HIGH SEVERITY ALERT: {alert.message}")
            else:
                log(f"Alert: {alert.message}")

        return alerts

    def generate_alert_report(self) -> str:
        """Generate alert report with severity levels."""
        if not self.alerts:
            return "No alerts generated during monitoring."

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(self.alert_dir, f"alerts_{timestamp}.html")

        # Define severity colors
        severity_colors = {
            AlertSeverity.INFO: "#3498db",     # Blue
            AlertSeverity.WARNING: "#f1c40f",  # Yellow
            AlertSeverity.ERROR: "#e67e22",    # Orange
            AlertSeverity.CRITICAL: "#e74c3c"  # Red
        }

        html_content = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<title>Resource Monitoring Alerts</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 20px; }",
            "table { border-collapse: collapse; width: 100%; }",
            "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
            "th { background-color: #f2f2f2; }",
            *[f".{sev.name.lower()} {{ background-color: {color}33; }}"
              for sev, color in severity_colors.items()],
            "</style>",
            "</head>",
            "<body>",
            "<h1>Resource Monitoring Alerts</h1>",
            f"<p>Generated: {datetime.now().isoformat()}</p>",
            "<table>",
            "<tr><th>Time</th><th>Severity</th><th>Resource</th><th>Value</th>"
            "<th>Threshold</th><th>Message</th></tr>"
        ]

        for alert in sorted(self.alerts, key=lambda x: x.timestamp):
            time_str = datetime.fromtimestamp(alert.timestamp).strftime("%H:%M:%S")
            html_content.append(
                f"<tr class='{alert.severity.name.lower()}'>"
                f"<td>{time_str}</td>"
                f"<td>{alert.severity.name}</td>"
                f"<td>{alert.resource}</td>"
                f"<td>{alert.value:.1f}</td>"
                f"<td>{alert.threshold:.1f}</td>"
                f"<td>{alert.message}</td>"
                f"</tr>"
            )

        html_content.extend([
            "</table>",
            "<h2>Summary</h2>",
            "<ul>"
        ])

        # Add summary statistics by severity
        for severity in AlertSeverity:
            severity_alerts = [a for a in self.alerts if a.severity == severity]
            if severity_alerts:
                html_content.append(
                    f"<li><strong>{severity.name}:</strong> "
                    f"{len(severity_alerts)} alerts"
                    f"</li>"
                )

        # Add summary by resource
        resources = set(alert.resource for alert in self.alerts)
        html_content.append("<h3>By Resource:</h3>")
        for resource in sorted(resources):
            resource_alerts = [a for a in self.alerts if a.resource == resource]
            max_alert = max(resource_alerts, key=lambda x: x.value)
            html_content.append(
                f"<li><strong>{resource}:</strong> "
                f"{len(resource_alerts)} alerts, "
                f"Max value: {max_alert.value:.1f} "
                f"({max_alert.severity.name})"
                f"</li>"
            )

        html_content.extend([
            "</ul>",
            "</body>",
            "</html>"
        ])

        with open(report_file, 'w') as f:
            f.write("\n".join(html_content))

        return report_file

    def export_alerts(self) -> Dict[str, Any]:
        """Export alerts data with severity information."""
        severity_counts = {sev: 0 for sev in AlertSeverity}
        for alert in self.alerts:
            severity_counts[alert.severity] += 1

        return {
            "alerts": [
                {
                    "timestamp": alert.timestamp,
                    "resource": alert.resource,
                    "value": alert.value,
                    "threshold": alert.threshold,
                    "message": alert.message,
                    "severity": alert.severity.name
                }
                for alert in self.alerts
            ],
            "summary": {
                "total_alerts": len(self.alerts),
                "resources_affected": len(set(alert.resource for alert in self.alerts)),
                "severity_distribution": {
                    sev.name: count for sev, count in severity_counts.items()
                },
                "first_alert": min(alert.timestamp for alert in self.alerts) if self.alerts else None,
                "last_alert": max(alert.timestamp for alert in self.alerts) if self.alerts else None,
                "critical_alerts": len([a for a in self.alerts if a.severity == AlertSeverity.CRITICAL])
            }
        }

def create_alert_manager(config: Optional[Dict[str, Any]] = None) -> ResourceAlertManager:
    """Create alert manager with optional configuration."""
    thresholds = None
    if config:
        thresholds = ResourceThresholds(
            cpu_percent=config.get("cpu_threshold", 80.0),
            memory_percent=config.get("memory_threshold", 80.0),
            memory_mb=config.get("memory_mb_threshold", 1024.0),
            swap_mb=config.get("swap_threshold", 512.0),
            disk_read_mbs=config.get("disk_read_threshold", 100.0),
            disk_write_mbs=config.get("disk_write_threshold", 100.0),
            network_sent_mbs=config.get("network_send_threshold", 50.0),
            network_recv_mbs=config.get("network_recv_threshold", 50.0),
            max_threads=config.get("thread_threshold", 100),
            max_processes=config.get("process_threshold", 20)
        )
    
    notifier = create_default_notifier()
    return ResourceAlertManager(thresholds=thresholds, notifier=notifier)
