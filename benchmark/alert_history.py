"""Alert history tracking and pattern detection."""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
import numpy as np
from dataclasses import dataclass

from utils.log import log
from benchmark.alert_notifications import AlertSeverity

@dataclass
class AlertPattern:
    """Pattern detected in alert history."""
    resource: str
    frequency: float  # Alerts per hour
    avg_value: float
    peak_value: float
    severity_distribution: Dict[str, int]
    first_seen: datetime
    last_seen: datetime
    total_occurrences: int
    description: str

class AlertHistory:
    """Track and analyze alert history."""
    def __init__(self, history_dir: str = "benchmark/alert_history"):
        """Initialize alert history tracker."""
        self.history_dir = history_dir
        self.current_file = None
        self.current_alerts = []
        
        os.makedirs(history_dir, exist_ok=True)
        self._init_current_file()

    def _init_current_file(self):
        """Initialize current history file."""
        timestamp = datetime.now().strftime("%Y%m")
        self.current_file = os.path.join(
            self.history_dir,
            f"alert_history_{timestamp}.json"
        )
        
        if os.path.exists(self.current_file):
            with open(self.current_file, 'r') as f:
                self.current_alerts = json.load(f)
        else:
            self.current_alerts = []

    def add_alert(self, alert: Dict[str, Any]):
        """Add new alert to history."""
        self.current_alerts.append({
            **alert,
            "_added": datetime.now().isoformat()
        })
        
        # Save updated history
        with open(self.current_file, 'w') as f:
            json.dump(self.current_alerts, f, indent=2)

    def get_alerts(self, 
                  start_time: Optional[datetime] = None,
                  end_time: Optional[datetime] = None,
                  resource: Optional[str] = None,
                  severity: Optional[AlertSeverity] = None) -> List[Dict[str, Any]]:
        """Get filtered alerts from history."""
        alerts = []
        
        # Load all history files
        for filename in os.listdir(self.history_dir):
            if filename.startswith("alert_history_") and filename.endswith(".json"):
                with open(os.path.join(self.history_dir, filename), 'r') as f:
                    alerts.extend(json.load(f))
        
        # Apply filters
        filtered = alerts
        
        if start_time:
            filtered = [
                a for a in filtered 
                if datetime.fromisoformat(a["timestamp"]) >= start_time
            ]
        
        if end_time:
            filtered = [
                a for a in filtered 
                if datetime.fromisoformat(a["timestamp"]) <= end_time
            ]
        
        if resource:
            filtered = [a for a in filtered if a["resource"] == resource]
        
        if severity:
            filtered = [
                a for a in filtered 
                if AlertSeverity[a.get("severity", "WARNING")] == severity
            ]
        
        return filtered

    def detect_patterns(self, 
                       window_hours: int = 24,
                       min_frequency: float = 1.0) -> List[AlertPattern]:
        """Detect patterns in alert history."""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=window_hours)
        
        # Get recent alerts
        alerts = self.get_alerts(start_time=start_time, end_time=end_time)
        if not alerts:
            return []
        
        # Group by resource
        resource_alerts = defaultdict(list)
        for alert in alerts:
            resource_alerts[alert["resource"]].append(alert)
        
        patterns = []
        for resource, resource_alerts_list in resource_alerts.items():
            # Calculate frequency
            duration = (end_time - start_time).total_seconds() / 3600  # hours
            frequency = len(resource_alerts_list) / duration
            
            if frequency >= min_frequency:
                # Analyze values
                values = [a["value"] for a in resource_alerts_list]
                avg_value = np.mean(values)
                peak_value = max(values)
                
                # Analyze severity distribution
                severity_dist = defaultdict(int)
                for alert in resource_alerts_list:
                    severity_dist[alert.get("severity", "WARNING")] += 1
                
                # Get timespan
                timestamps = [
                    datetime.fromisoformat(a["timestamp"]) 
                    for a in resource_alerts_list
                ]
                first_seen = min(timestamps)
                last_seen = max(timestamps)
                
                # Generate description
                description = (
                    f"Resource {resource} triggered {len(resource_alerts_list)} alerts "
                    f"({frequency:.1f}/hour). "
                    f"Values: avg={avg_value:.1f}, peak={peak_value:.1f}. "
                    f"Severities: {dict(severity_dist)}"
                )
                
                pattern = AlertPattern(
                    resource=resource,
                    frequency=frequency,
                    avg_value=avg_value,
                    peak_value=peak_value,
                    severity_distribution=dict(severity_dist),
                    first_seen=first_seen,
                    last_seen=last_seen,
                    total_occurrences=len(resource_alerts_list),
                    description=description
                )
                patterns.append(pattern)
        
        return patterns

    def generate_history_report(self, days: int = 7) -> str:
        """Generate report of alert history."""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        alerts = self.get_alerts(start_time=start_time, end_time=end_time)
        patterns = self.detect_patterns(window_hours=days * 24)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(self.history_dir, f"history_report_{timestamp}.html")
        
        html_content = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<title>Alert History Report</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 20px; }",
            "table { border-collapse: collapse; width: 100%; margin: 10px 0; }",
            "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
            "th { background-color: #f2f2f2; }",
            ".pattern { background-color: #fff3e0; padding: 10px; margin: 10px 0; }",
            ".high-frequency { color: #d32f2f; }",
            "</style>",
            "</head>",
            "<body>",
            "<h1>Alert History Report</h1>",
            f"<p>Period: {start_time.strftime('%Y-%m-%d')} to {end_time.strftime('%Y-%m-%d')}</p>"
        ]
        
        # Add patterns section
        if patterns:
            html_content.extend([
                "<h2>Detected Patterns</h2>"
            ])
            for pattern in patterns:
                frequency_class = "high-frequency" if pattern.frequency > 5 else ""
                html_content.append(
                    f'<div class="pattern {frequency_class}">'
                    f"<h3>{pattern.resource}</h3>"
                    f"<p>{pattern.description}</p>"
                    f"<p>Time span: {pattern.first_seen.strftime('%Y-%m-%d %H:%M')} to "
                    f"{pattern.last_seen.strftime('%Y-%m-%d %H:%M')}</p>"
                    "</div>"
                )
        
        # Add alerts table
        html_content.extend([
            "<h2>Alert History</h2>",
            "<table>",
            "<tr><th>Time</th><th>Resource</th><th>Severity</th><th>Value</th>"
            "<th>Threshold</th><th>Message</th></tr>"
        ])
        
        for alert in sorted(alerts, key=lambda x: x["timestamp"], reverse=True):
            time_str = datetime.fromisoformat(alert["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
            html_content.append(
                "<tr>"
                f"<td>{time_str}</td>"
                f"<td>{alert['resource']}</td>"
                f"<td>{alert.get('severity', 'WARNING')}</td>"
                f"<td>{alert['value']:.1f}</td>"
                f"<td>{alert['threshold']:.1f}</td>"
                f"<td>{alert['message']}</td>"
                "</tr>"
            )
        
        html_content.extend([
            "</table>",
            "<h2>Summary Statistics</h2>",
            "<ul>"
        ])
        
        # Add summary statistics
        resource_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        for alert in alerts:
            resource_counts[alert["resource"]] += 1
            severity_counts[alert.get("severity", "WARNING")] += 1
        
        html_content.extend([
            f"<li>Total alerts: {len(alerts)}</li>",
            f"<li>Unique resources affected: {len(resource_counts)}</li>",
            "<li>Resource distribution:</li>",
            "<ul>"
        ])
        
        for resource, count in sorted(resource_counts.items(), key=lambda x: x[1], reverse=True):
            html_content.append(f"<li>{resource}: {count} alerts</li>")
        
        html_content.extend([
            "</ul>",
            "<li>Severity distribution:</li>",
            "<ul>"
        ])
        
        for severity, count in sorted(severity_counts.items()):
            html_content.append(f"<li>{severity}: {count} alerts</li>")
        
        html_content.extend([
            "</ul>",
            "</ul>",
            "</body>",
            "</html>"
        ])
        
        with open(report_file, 'w') as f:
            f.write("\n".join(html_content))
        
        return report_file

def create_alert_history() -> AlertHistory:
    """Create alert history tracker."""
    return AlertHistory()
