"""Validation rules and functions for benchmark configuration."""

import os
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

class ValidationError(Exception):
    """Custom exception for configuration validation errors."""
    pass

VALIDATION_RULES = {
    "system": {
        "debug": {"type": bool},
        "log_level": {
            "type": str,
            "allowed": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        },
        "timestamp_format": {
            "type": str,
            "validator": lambda x: bool(datetime.now().strftime(x))  # Test if format is valid
        },
        "max_retries": {
            "type": int,
            "min": 1,
            "max": 10
        },
        "retry_delay": {
            "type": int,
            "min": 1,
            "max": 60
        }
    },
    "directories": {
        "*": {  # Wildcard for all directory paths
            "type": str,
            "validator": lambda x: not os.path.isabs(x),  # Paths should be relative
            "required": True
        }
    },
    "metrics": {
        "*": {  # Wildcard for all metrics
            "enabled": {"type": bool},
            "weight": {
                "type": float,
                "min": 0.0,
                "max": 1.0
            },
            "threshold": {
                "type": float,
                "min": 0.0,
                "max": 1.0
            }
        }
    },
    "analysis": {
        "statistical_significance": {
            "type": float,
            "min": 0.01,
            "max": 0.1
        },
        "min_samples": {
            "type": int,
            "min": 1,
            "max": 100
        },
        "outlier_threshold": {
            "type": float,
            "min": 1.0,
            "max": 5.0
        },
        "trend_window": {
            "type": str,
            "validator": lambda x: x[-1] in ['s', 'm', 'h', 'd'] and x[:-1].isdigit()
        }
    },
    "visualization": {
        "theme": {
            "type": str,
            "allowed": ["plotly", "plotly_white", "plotly_dark", "seaborn"]
        },
        "color_scheme": {
            "type": str,
            "allowed": ["RdYlBu", "Viridis", "Plasma", "Inferno", "Magma"]
        },
        "interactive": {"type": bool},
        "plot_width": {
            "type": int,
            "min": 100,
            "max": 3000
        },
        "plot_height": {
            "type": int,
            "min": 100,
            "max": 2000
        }
    },
    "reporting": {
        "formats": {
            "type": list,
            "allowed_items": ["md", "html", "pdf", "json"]
        },
        "include_raw_data": {"type": bool},
        "auto_open": {"type": bool}
    }
}

def validate_value(value: Any, rules: Dict[str, Any], path: str = "") -> List[str]:
    """Validate a single value against its rules."""
    errors = []

    # Check type
    expected_type = rules.get("type")
    if expected_type and not isinstance(value, expected_type):
        errors.append(f"{path}: Expected type {expected_type.__name__}, got {type(value).__name__}")

    # Check allowed values
    allowed = rules.get("allowed")
    if allowed and value not in allowed:
        errors.append(f"{path}: Value must be one of {allowed}, got {value}")

    # Check allowed items for lists
    allowed_items = rules.get("allowed_items")
    if allowed_items and isinstance(value, list):
        invalid_items = [item for item in value if item not in allowed_items]
        if invalid_items:
            errors.append(f"{path}: Invalid items {invalid_items}, allowed values are {allowed_items}")

    # Check numeric ranges
    if isinstance(value, (int, float)):
        min_val = rules.get("min")
        max_val = rules.get("max")
        if min_val is not None and value < min_val:
            errors.append(f"{path}: Value {value} is below minimum {min_val}")
        if max_val is not None and value > max_val:
            errors.append(f"{path}: Value {value} is above maximum {max_val}")

    # Run custom validator
    validator = rules.get("validator")
    if validator:
        try:
            if not validator(value):
                errors.append(f"{path}: Failed custom validation")
        except Exception as e:
            errors.append(f"{path}: Validation error: {str(e)}")

    return errors

def validate_config(config: Dict[str, Any], rules: Dict[str, Any] = None, path: str = "") -> List[str]:
    """Recursively validate configuration against rules."""
    if rules is None:
        rules = VALIDATION_RULES

    errors = []
    
    # Check for required fields
    for key, rule in rules.items():
        if key == "*":  # Wildcard rules
            continue
        if rule.get("required", False) and key not in config:
            errors.append(f"{path}: Missing required field '{key}'")

    # Validate each field
    for key, value in config.items():
        current_path = f"{path}.{key}" if path else key
        
        # Get rules for this field
        field_rules = rules.get(key) or rules.get("*", {})
        
        if isinstance(value, dict):
            # Recursive validation for nested dictionaries
            if isinstance(field_rules, dict) and not field_rules.get("type"):
                errors.extend(validate_config(value, field_rules, current_path))
            else:
                # Validate as a value if it has explicit rules
                errors.extend(validate_value(value, field_rules, current_path))
        else:
            # Validate non-dict values
            errors.extend(validate_value(value, field_rules, current_path))

    return errors

def validate_directory_structure(config: Dict[str, Any]) -> List[str]:
    """Validate directory structure specified in config."""
    errors = []
    directories = config.get("directories", {})
    
    for dir_type, path in directories.items():
        try:
            # Check if path is absolute
            if os.path.isabs(path):
                errors.append(f"Directory '{dir_type}' path must be relative: {path}")
            
            # Check for path traversal attempts
            if ".." in path:
                errors.append(f"Directory '{dir_type}' path cannot contain '..': {path}")
            
            # Check path is within project directory
            full_path = os.path.abspath(path)
            if not full_path.startswith(os.getcwd()):
                errors.append(f"Directory '{dir_type}' must be within project directory: {path}")
            
        except Exception as e:
            errors.append(f"Error validating directory '{dir_type}': {str(e)}")
    
    return errors

def validate_and_update_config(config: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """Validate and update configuration, returning the validated config and any errors."""
    all_errors = []
    
    # Validate basic structure
    structure_errors = validate_config(config)
    all_errors.extend(structure_errors)
    
    # Validate directory structure
    directory_errors = validate_directory_structure(config)
    all_errors.extend(directory_errors)
    
    if all_errors:
        raise ValidationError("\n".join(all_errors))
    
    return config, all_errors

def main():
    """Test configuration validation."""
    from benchmark.config import DEFAULT_CONFIG, get_config
    
    print("Validating default configuration...")
    try:
        config, errors = validate_and_update_config(DEFAULT_CONFIG)
        if errors:
            print("Validation errors in default configuration:")
            for error in errors:
                print(f"- {error}")
        else:
            print("Default configuration is valid!")
    except ValidationError as e:
        print(f"Validation failed:\n{str(e)}")

if __name__ == "__main__":
    main()
