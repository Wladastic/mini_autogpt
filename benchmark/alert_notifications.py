"""Alert notifications and severity management."""

import os
import smtplib
from enum import Enum
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import telegram
from utils.log import log
from utils.simple_telegram import send_message

class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4

@dataclass
class AlertThresholds:
    """Thresholds for different severity levels."""
    info: float
    warning: float
    error: float
    critical: float

    def get_severity(self, value: float) -> AlertSeverity:
        """Get severity level for a value."""
        if value >= self.critical:
            return AlertSeverity.CRITICAL
        elif value >= self.error:
            return AlertSeverity.ERROR
        elif value >= self.warning:
            return AlertSeverity.WARNING
        elif value >= self.info:
            return AlertSeverity.INFO
        return None

@dataclass
class NotificationConfig:
    """Notification configuration."""
    email_enabled: bool = False
    email_from: str = ""
    email_to: List[str] = None
    email_server: str = "smtp.gmail.com"
    email_port: int = 587
    email_username: str = ""
    email_password: str = ""
    
    telegram_enabled: bool = False
    telegram_token: str = ""
    telegram_chat_id: str = ""
    
    min_severity: AlertSeverity = AlertSeverity.WARNING

class AlertNotifier:
    def __init__(self, config: NotificationConfig):
        """Initialize alert notifier."""
        self.config = config
        self._setup_notifiers()

    def _setup_notifiers(self):
        """Set up notification handlers."""
        self.notifiers: Dict[str, Callable] = {}
        
        if self.config.email_enabled:
            self.notifiers["email"] = self._send_email
        
        if self.config.telegram_enabled:
            self.notifiers["telegram"] = self._send_telegram

    def _format_alert_message(self, alert: Dict[str, Any]) -> str:
        """Format alert for notification."""
        severity = alert.get("severity", AlertSeverity.INFO)
        time_str = datetime.fromtimestamp(alert["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        
        return (
            f"🚨 {severity.name} Alert\n"
            f"Time: {time_str}\n"
            f"Resource: {alert['resource']}\n"
            f"Value: {alert['value']:.1f}\n"
            f"Threshold: {alert['threshold']:.1f}\n"
            f"Message: {alert['message']}"
        )

    def _send_email(self, alert: Dict[str, Any]):
        """Send email notification."""
        try:
            msg = MIMEMultipart()
            msg["From"] = self.config.email_from
            msg["To"] = ", ".join(self.config.email_to)
            msg["Subject"] = f"Resource Alert: {alert['resource']} [{alert.get('severity', 'INFO')}]"
            
            body = self._format_alert_message(alert)
            msg.attach(MIMEText(body, "plain"))
            
            with smtplib.SMTP(self.config.email_server, self.config.email_port) as server:
                server.starttls()
                server.login(self.config.email_username, self.config.email_password)
                server.send_message(msg)
            
            log(f"Email notification sent: {alert['resource']}")
            
        except Exception as e:
            log(f"Error sending email notification: {e}")

    def _send_telegram(self, alert: Dict[str, Any]):
        """Send Telegram notification."""
        try:
            message = self._format_alert_message(alert)
            send_message(
                message,
                token=self.config.telegram_token,
                chat_id=self.config.telegram_chat_id
            )
            log(f"Telegram notification sent: {alert['resource']}")
            
        except Exception as e:
            log(f"Error sending Telegram notification: {e}")

    def notify(self, alert: Dict[str, Any]):
        """Send notifications for an alert."""
        severity = alert.get("severity", AlertSeverity.INFO)
        
        if severity.value >= self.config.min_severity.value:
            for notifier in self.notifiers.values():
                notifier(alert)

class ResourceThresholdManager:
    """Manage resource thresholds with severity levels."""
    def __init__(self):
        self.thresholds = {
            "cpu_percent": AlertThresholds(
                info=50.0,
                warning=70.0,
                error=85.0,
                critical=95.0
            ),
            "memory_percent": AlertThresholds(
                info=60.0,
                warning=75.0,
                error=85.0,
                critical=95.0
            ),
            "disk_read_mbs": AlertThresholds(
                info=50.0,
                warning=80.0,
                error=120.0,
                critical=200.0
            ),
            "disk_write_mbs": AlertThresholds(
                info=50.0,
                warning=80.0,
                error=120.0,
                critical=200.0
            ),
            "network_sent_mbs": AlertThresholds(
                info=25.0,
                warning=40.0,
                error=60.0,
                critical=100.0
            ),
            "network_recv_mbs": AlertThresholds(
                info=25.0,
                warning=40.0,
                error=60.0,
                critical=100.0
            )
        }

    def get_severity(self, metric: str, value: float) -> Optional[AlertSeverity]:
        """Get severity level for a metric value."""
        if metric in self.thresholds:
            return self.thresholds[metric].get_severity(value)
        return None

    def check_metrics(self, metrics: Dict[str, float]) -> List[Dict[str, Any]]:
        """Check metrics and return alerts with severity levels."""
        alerts = []
        timestamp = datetime.now().timestamp()
        
        for metric, value in metrics.items():
            severity = self.get_severity(metric, value)
            if severity:
                alerts.append({
                    "timestamp": timestamp,
                    "resource": metric,
                    "value": value,
                    "severity": severity,
                    "threshold": getattr(self.thresholds[metric], severity.name.lower()),
                    "message": f"{metric} at {severity.name} level: {value:.1f}"
                })
        
        return alerts

def create_default_notifier() -> AlertNotifier:
    """Create notifier with default configuration."""
    config = NotificationConfig(
        email_enabled=bool(os.getenv("ALERT_EMAIL_ENABLED")),
        email_from=os.getenv("ALERT_EMAIL_FROM", ""),
        email_to=os.getenv("ALERT_EMAIL_TO", "").split(","),
        email_username=os.getenv("ALERT_EMAIL_USERNAME", ""),
        email_password=os.getenv("ALERT_EMAIL_PASSWORD", ""),
        telegram_enabled=bool(os.getenv("ALERT_TELEGRAM_ENABLED")),
        telegram_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
        min_severity=AlertSeverity[os.getenv("ALERT_MIN_SEVERITY", "WARNING")]
    )
    return AlertNotifier(config)
