"""Configuration management for benchmark system."""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional

from utils.log import log

DEFAULT_CONFIG = {
    "system": {
        "debug": True,
        "log_level": "DEBUG",
        "timestamp_format": "%Y%m%d_%H%M%S",
        "max_retries": 3,
        "retry_delay": 5
    },
    "directories": {
        "results": "benchmark/results",
        "logs": "benchmark/logs",
        "reports": "benchmark/reports",
        "visualizations": "benchmark/visualizations",
        "statistics": "benchmark/statistics",
        "mock_data": "benchmark/mock_data"
    },
    "metrics": {
        "response_quality": {
            "enabled": True,
            "weight": 1.0,
            "threshold": 0.7
        },
        "context_usage": {
            "enabled": True,
            "weight": 1.0,
            "threshold": 0.6
        },
        "memory_retention": {
            "enabled": True,
            "weight": 1.0,
            "threshold": 0.8
        },
        "decision_quality": {
            "enabled": True,
            "weight": 1.0,
            "threshold": 0.7
        }
    },
    "analysis": {
        "statistical_significance": 0.05,
        "min_samples": 5,
        "outlier_threshold": 2.0,
        "trend_window": "1h"
    },
    "visualization": {
        "theme": "plotly_white",
        "color_scheme": "RdYlBu",
        "interactive": True,
        "plot_width": 1000,
        "plot_height": 600
    },
    "reporting": {
        "formats": ["md", "html"],
        "include_raw_data": False,
        "auto_open": True
    }
}

class BenchmarkConfig:
    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration manager."""
        self.config_file = config_file or "benchmark/config.json"
        self.config = self.load_config()
        self._ensure_directories()

    def load_config(self) -> Dict[str, Any]:
        """Load and validate configuration from file or create default."""
        from benchmark.validation import validate_and_update_config, ValidationError
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                log(f"Configuration loaded from {self.config_file}")
                
                # Merge with defaults before validation
                config = self._merge_with_default(config)
                
                # Validate merged configuration
                validated_config, errors = validate_and_update_config(config)
                if errors:
                    log("Configuration validation warnings:")
                    for error in errors:
                        log(f"- {error}")
                
                return validated_config
                
            except ValidationError as e:
                log(f"Configuration validation failed: {e}")
                log("Using default configuration")
                # Validate default config as fallback
                validated_default, _ = validate_and_update_config(DEFAULT_CONFIG.copy())
                return validated_default
                
            except Exception as e:
                log(f"Error loading config: {e}")
                log("Using default configuration")
                # Validate default config as fallback
                validated_default, _ = validate_and_update_config(DEFAULT_CONFIG.copy())
                return validated_default
        else:
            log("No configuration file found, creating default")
            validated_default, _ = validate_and_update_config(DEFAULT_CONFIG.copy())
            self.save_config(validated_default)
            return validated_default

    def _merge_with_default(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge loaded config with default, ensuring all required fields exist."""
        merged = DEFAULT_CONFIG.copy()
        
        def merge_dicts(base: Dict, update: Dict) -> Dict:
            for key, value in update.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    merge_dicts(base[key], value)
                else:
                    base[key] = value
            return base
        
        return merge_dicts(merged, config)

    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file after validation."""
        from benchmark.validation import validate_and_update_config, ValidationError
        try:
            validated_config, errors = validate_and_update_config(config)
            if errors:
                log("Configuration warnings:")
                for error in errors:
                    log(f"- {error}")
            
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(validated_config, f, indent=2)
            log(f"Configuration saved to {self.config_file}")
            self.config = validated_config
        except ValidationError as e:
            log(f"Configuration validation failed: {e}")
            raise
        except Exception as e:
            log(f"Error saving configuration: {e}")
            raise

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key path (e.g., 'system.debug')."""
        keys = key.split('.')
        value = self.config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """Set configuration value by key path."""
        keys = key.split('.')
        target = self.config
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value
        self.save_config(self.config)

    def _ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        for dir_path in self.config["directories"].values():
            os.makedirs(dir_path, exist_ok=True)

    def get_path(self, dir_type: str) -> str:
        """Get full path for a directory type."""
        base_path = self.get(f"directories.{dir_type}")
        if not base_path:
            raise ValueError(f"Unknown directory type: {dir_type}")
        return os.path.abspath(base_path)

    def get_timestamped_path(self, dir_type: str, prefix: str = "", suffix: str = "") -> str:
        """Get a timestamped path in the specified directory."""
        base_path = self.get_path(dir_type)
        timestamp = datetime.now().strftime(self.get("system.timestamp_format"))
        filename = f"{prefix}_{timestamp}{suffix}" if prefix else f"{timestamp}{suffix}"
        return os.path.join(base_path, filename)

    def update_from_env(self) -> None:
        """Update configuration from environment variables."""
        env_prefix = "BENCHMARK_"
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                config_key = key[len(env_prefix):].lower().replace("_", ".")
                try:
                    # Try to parse as JSON for complex values
                    parsed_value = json.loads(value)
                except json.JSONDecodeError:
                    parsed_value = value
                self.set(config_key, parsed_value)

def get_config(config_file: Optional[str] = None) -> BenchmarkConfig:
    """Get or create configuration instance."""
    return BenchmarkConfig(config_file)

# Global configuration instance
config = get_config()

def main():
    """CLI for configuration management."""
    import argparse
    parser = argparse.ArgumentParser(description="Benchmark Configuration Manager")
    
    subparsers = parser.add_subparsers(dest="command")
    
    # Get command
    get_parser = subparsers.add_parser("get", help="Get configuration value")
    get_parser.add_argument("key", help="Configuration key (e.g., system.debug)")
    
    # Set command
    set_parser = subparsers.add_parser("set", help="Set configuration value")
    set_parser.add_argument("key", help="Configuration key")
    set_parser.add_argument("value", help="Value to set (will be parsed as JSON)")
    
    # Reset command
    subparsers.add_parser("reset", help="Reset to default configuration")
    
    # Show command
    subparsers.add_parser("show", help="Show current configuration")
    
    args = parser.parse_args()
    
    if args.command == "get":
        value = config.get(args.key)
        print(f"{args.key} = {json.dumps(value, indent=2)}")
    
    elif args.command == "set":
        try:
            value = json.loads(args.value)
            config.set(args.key, value)
            print(f"Set {args.key} = {json.dumps(value, indent=2)}")
        except json.JSONDecodeError:
            config.set(args.key, args.value)
            print(f"Set {args.key} = {args.value}")
    
    elif args.command == "reset":
        config.save_config(DEFAULT_CONFIG)
        print("Configuration reset to defaults")
    
    elif args.command == "show":
        print(json.dumps(config.config, indent=2))
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
