"""Configuration for resource monitoring."""

from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class MonitorConfig:
    """Resource monitoring configuration."""
    # Resource thresholds
    cpu_threshold: float = 80.0      # Percent
    memory_threshold: float = 80.0   # Percent
    disk_threshold: float = 85.0     # Percent
    
    # Monitoring settings
    check_interval: float = 1.0      # Seconds between checks
    notify_telegram: bool = False    # Send Telegram alerts
    min_alert_interval: float = 60.0 # Minimum seconds between repeat alerts

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'MonitorConfig':
        """Create config from dictionary."""
        return cls(
            cpu_threshold=float(config.get("cpu_threshold", 80.0)),
            memory_threshold=float(config.get("memory_threshold", 80.0)),
            disk_threshold=float(config.get("disk_threshold", 85.0)),
            check_interval=float(config.get("check_interval", 1.0)),
            notify_telegram=bool(config.get("notify_telegram", False)),
            min_alert_interval=float(config.get("min_alert_interval", 60.0))
        )

def load_monitor_config(config_path: Optional[str] = None) -> MonitorConfig:
    """Load monitor configuration."""
    if config_path:
        try:
            with open(config_path) as f:
                config = json.load(f)
            return MonitorConfig.from_dict(config)
        except Exception as e:
            print(f"Error loading monitor config: {e}")
    
    return MonitorConfig()
