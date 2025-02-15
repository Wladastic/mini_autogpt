"""Utility functions for template manipulation and customization."""

import copy
from typing import Dict, Any, List, Optional, Union
from benchmark.validation import validate_and_update_config, ValidationError
from benchmark.templates import TEMPLATES, get_template
from utils.log import log

def customize_template(template_name: str, overrides: Dict[str, Any]) -> Dict[str, Any]:
    """Create a customized version of a template with overrides."""
    base = get_template(template_name)
    
    def deep_update(target: Dict, source: Dict) -> Dict:
        """Recursively update nested dictionaries."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                deep_update(target[key], value)
            else:
                target[key] = copy.deepcopy(value)
        return target
    
    customized = deep_update(base, overrides)
    
    # Validate the customized template
    try:
        validated, errors = validate_and_update_config(customized)
        if errors:
            log("Validation warnings for customized template:")
            for error in errors:
                log(f"- {error}")
        return validated
    except ValidationError as e:
        log(f"Error validating customized template: {e}")
        raise

def combine_templates(templates: List[str], weights: Optional[List[float]] = None) -> Dict[str, Any]:
    """Combine multiple templates with optional weights."""
    if not templates:
        raise ValueError("No templates specified")
    
    if weights is None:
        weights = [1.0] * len(templates)
    
    if len(templates) != len(weights):
        raise ValueError("Number of templates must match number of weights")
    
    if not all(w >= 0 for w in weights) or sum(weights) == 0:
        raise ValueError("Weights must be non-negative and sum to a positive value")
    
    # Normalize weights
    total = sum(weights)
    weights = [w/total for w in weights]
    
    combined: Dict[str, Any] = {}
    
    for template_name, weight in zip(templates, weights):
        template = get_template(template_name)
        
        # Combine metrics with weighted values
        if "metrics" not in combined:
            combined["metrics"] = {}
        
        for metric, config in template["metrics"].items():
            if metric not in combined["metrics"]:
                combined["metrics"][metric] = copy.deepcopy(config)
            else:
                # Weight the numeric values
                for key, value in config.items():
                    if isinstance(value, (int, float)):
                        current = combined["metrics"][metric].get(key, 0)
                        combined["metrics"][metric][key] = current + (value * weight)
        
        # Combine analysis settings
        if "analysis" not in combined:
            combined["analysis"] = {}
        
        for key, value in template["analysis"].items():
            if isinstance(value, (int, float)):
                current = combined["analysis"].get(key, 0)
                combined["analysis"][key] = current + (value * weight)
    
    # Use most aggressive system settings from any template
    system_settings = {}
    for template_name in templates:
        template = get_template(template_name)
        for key, value in template["system"].items():
            if key not in system_settings or (
                isinstance(value, (int, float)) and value > system_settings[key]
            ):
                system_settings[key] = value
    
    combined["system"] = system_settings
    
    # Validate the combined template
    try:
        validated, errors = validate_and_update_config(combined)
        if errors:
            log("Validation warnings for combined template:")
            for error in errors:
                log(f"- {error}")
        return validated
    except ValidationError as e:
        log(f"Error validating combined template: {e}")
        raise

def preview_combination(templates: List[str], weights: Optional[List[float]] = None) -> Dict[str, Any]:
    """Preview how templates would be combined without creating a profile."""
    combined = combine_templates(templates, weights)
    
    # Calculate template contributions
    contributions = {name: 0.0 for name in templates}
    norm_weights = weights or [1.0] * len(templates)
    total = sum(norm_weights)
    norm_weights = [w/total for w in norm_weights]
    
    for template_name, weight in zip(templates, norm_weights):
        template = get_template(template_name)
        for metric in template["metrics"]:
            if template["metrics"][metric]["enabled"]:
                contributions[template_name] += weight
    
    return {
        "combined_template": combined,
        "template_contributions": contributions,
        "effective_weights": dict(zip(templates, norm_weights))
    }

def main():
    """CLI for template utilities."""
    import argparse
    import json
    from benchmark.profiles import ProfileManager
    
    parser = argparse.ArgumentParser(description="Template Utilities")
    subparsers = parser.add_subparsers(dest="command")
    
    # Customize command
    customize_parser = subparsers.add_parser("customize", help="Customize a template")
    customize_parser.add_argument("template", help="Base template name")
    customize_parser.add_argument("overrides", help="JSON string of overrides")
    customize_parser.add_argument("--save", help="Save as new profile")
    
    # Combine command
    combine_parser = subparsers.add_parser("combine", help="Combine multiple templates")
    combine_parser.add_argument("templates", nargs="+", help="Template names")
    combine_parser.add_argument("--weights", nargs="+", type=float, help="Template weights")
    combine_parser.add_argument("--save", help="Save as new profile")
    
    # Preview command
    preview_parser = subparsers.add_parser("preview", help="Preview template combination")
    preview_parser.add_argument("templates", nargs="+", help="Template names")
    preview_parser.add_argument("--weights", nargs="+", type=float, help="Template weights")
    
    args = parser.parse_args()
    
    try:
        if args.command == "customize":
            overrides = json.loads(args.overrides)
            result = customize_template(args.template, overrides)
            
            if args.save:
                manager = ProfileManager()
                manager.create_profile(args.save, result)
                print(f"Saved customized template as profile: {args.save}")
            else:
                print(json.dumps(result, indent=2))
        
        elif args.command == "combine":
            result = combine_templates(args.templates, args.weights)
            
            if args.save:
                manager = ProfileManager()
                manager.create_profile(args.save, result)
                print(f"Saved combined template as profile: {args.save}")
            else:
                print(json.dumps(result, indent=2))
        
        elif args.command == "preview":
            preview = preview_combination(args.templates, args.weights)
            print("\nTemplate Combination Preview:")
            print("\nContributions:")
            for template, contribution in preview["template_contributions"].items():
                print(f"- {template}: {contribution:.2%}")
            print("\nEffective Weights:")
            for template, weight in preview["effective_weights"].items():
                print(f"- {template}: {weight:.2f}")
            print("\nCombined Template:")
            print(json.dumps(preview["combined_template"], indent=2))
        
        else:
            parser.print_help()
    
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
