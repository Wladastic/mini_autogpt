"""Predefined configuration templates for common benchmark scenarios."""

from typing import Dict, Any

# Fast testing profile with minimal iterations
FAST_TEST = {
    "system": {
        "debug": True,
        "log_level": "DEBUG",
        "timestamp_format": "%Y%m%d_%H%M%S",
        "max_retries": 1,
        "retry_delay": 1
    },
    "metrics": {
        "response_quality": {
            "enabled": True,
            "weight": 1.0,
            "threshold": 0.5  # Lower threshold for quick tests
        },
        "context_usage": {
            "enabled": False,  # Disable some metrics for speed
            "weight": 0.0,
            "threshold": 0.0
        },
        "memory_retention": {
            "enabled": False,
            "weight": 0.0,
            "threshold": 0.0
        },
        "decision_quality": {
            "enabled": True,
            "weight": 1.0,
            "threshold": 0.5
        }
    },
    "analysis": {
        "statistical_significance": 0.1,  # Less strict for quick tests
        "min_samples": 3,
        "outlier_threshold": 3.0,
        "trend_window": "5m"
    }
}

# Thorough testing profile
THOROUGH = {
    "system": {
        "debug": True,
        "log_level": "DEBUG",
        "timestamp_format": "%Y%m%d_%H%M%S",
        "max_retries": 5,
        "retry_delay": 10
    },
    "metrics": {
        "response_quality": {
            "enabled": True,
            "weight": 1.0,
            "threshold": 0.8  # Higher standards
        },
        "context_usage": {
            "enabled": True,
            "weight": 1.0,
            "threshold": 0.7
        },
        "memory_retention": {
            "enabled": True,
            "weight": 1.0,
            "threshold": 0.9
        },
        "decision_quality": {
            "enabled": True,
            "weight": 1.0,
            "threshold": 0.8
        }
    },
    "analysis": {
        "statistical_significance": 0.01,  # More strict
        "min_samples": 10,
        "outlier_threshold": 2.0,
        "trend_window": "1h"
    }
}

# Memory-focused testing
MEMORY_TEST = {
    "system": {
        "debug": True,
        "log_level": "DEBUG",
        "timestamp_format": "%Y%m%d_%H%M%S",
        "max_retries": 3,
        "retry_delay": 5
    },
    "metrics": {
        "response_quality": {
            "enabled": True,
            "weight": 0.5,
            "threshold": 0.6
        },
        "context_usage": {
            "enabled": True,
            "weight": 1.5,  # Higher weight for memory-related metrics
            "threshold": 0.8
        },
        "memory_retention": {
            "enabled": True,
            "weight": 2.0,  # Highest weight for memory tests
            "threshold": 0.9
        },
        "decision_quality": {
            "enabled": True,
            "weight": 0.5,
            "threshold": 0.6
        }
    },
    "analysis": {
        "statistical_significance": 0.05,
        "min_samples": 7,
        "outlier_threshold": 2.5,
        "trend_window": "30m"
    }
}

# Performance testing
PERFORMANCE = {
    "system": {
        "debug": True,
        "log_level": "DEBUG",
        "timestamp_format": "%Y%m%d_%H%M%S",
        "max_retries": 0,  # No retries for timing accuracy
        "retry_delay": 0
    },
    "metrics": {
        "response_quality": {
            "enabled": True,
            "weight": 0.5,
            "threshold": 0.6
        },
        "context_usage": {
            "enabled": False,  # Focus on speed
            "weight": 0.0,
            "threshold": 0.0
        },
        "memory_retention": {
            "enabled": False,
            "weight": 0.0,
            "threshold": 0.0
        },
        "decision_quality": {
            "enabled": True,
            "weight": 2.0,  # Higher weight for decision speed
            "threshold": 0.7
        }
    },
    "analysis": {
        "statistical_significance": 0.05,
        "min_samples": 20,  # More samples for timing
        "outlier_threshold": 3.0,
        "trend_window": "15m"
    }
}

# Template registry
TEMPLATES = {
    "fast": FAST_TEST,
    "thorough": THOROUGH,
    "memory": MEMORY_TEST,
    "performance": PERFORMANCE
}

def list_templates() -> Dict[str, str]:
    """List available templates with descriptions."""
    return {
        "fast": "Quick testing with minimal metrics",
        "thorough": "Comprehensive testing with high standards",
        "memory": "Focus on memory retention and context usage",
        "performance": "Focus on response speed and decision quality"
    }

def get_template(name: str) -> Dict[str, Any]:
    """Get a template by name."""
    if name not in TEMPLATES:
        raise ValueError(f"Template '{name}' not found. Available templates: {list(TEMPLATES.keys())}")
    return TEMPLATES[name].copy()

def main():
    """CLI for template management."""
    import argparse
    import json
    from benchmark.profiles import ProfileManager
    
    parser = argparse.ArgumentParser(description="Benchmark Template Manager")
    subparsers = parser.add_subparsers(dest="command")
    
    # List command
    subparsers.add_parser("list", help="List available templates")
    
    # Show command
    show_parser = subparsers.add_parser("show", help="Show template contents")
    show_parser.add_argument("name", help="Template name")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create profile from template")
    create_parser.add_argument("template", help="Template name")
    create_parser.add_argument("profile", help="Profile name to create")
    
    args = parser.parse_args()
    
    try:
        if args.command == "list":
            templates = list_templates()
            print("\nAvailable templates:")
            for name, desc in templates.items():
                print(f"- {name}: {desc}")
        
        elif args.command == "show":
            template = get_template(args.name)
            print(f"\nTemplate: {args.name}")
            print(json.dumps(template, indent=2))
        
        elif args.command == "create":
            template = get_template(args.template)
            manager = ProfileManager()
            path = manager.create_profile(args.profile, template)
            print(f"Created profile '{args.profile}' from template '{args.template}'")
            print(f"Profile saved to: {path}")
        
        else:
            parser.print_help()
    
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
