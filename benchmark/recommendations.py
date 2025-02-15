"""Optimization suggestions and recommendations based on benchmark analysis."""

import json
from typing import Dict, List, Any, Tuple
from collections import defaultdict

import numpy as np
from scipy import stats

from utils.log import log
from benchmark.templates import TEMPLATES, get_template
from benchmark.template_analysis import TemplateAnalyzer

class TemplateOptimizer:
    def __init__(self, analyzer: TemplateAnalyzer = None):
        """Initialize template optimizer."""
        self.analyzer = analyzer or TemplateAnalyzer()

    def analyze_performance_patterns(self, comparison: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify performance patterns and potential improvements."""
        patterns = []
        
        for template_name, metrics in comparison.items():
            template_patterns = {
                "template": template_name,
                "strengths": [],
                "weaknesses": [],
                "suggestions": []
            }
            
            # Analyze metric patterns
            for metric, stats in metrics.items():
                mean = stats["mean"]
                std = stats["std"]
                
                # Check for high variability
                cv = std / mean if mean != 0 else float('inf')
                if cv > 0.25:  # High coefficient of variation
                    template_patterns["weaknesses"].append(
                        f"High variability in {metric} (CV: {cv:.2f})"
                    )
                    template_patterns["suggestions"].append(
                        f"Consider stabilizing {metric} performance"
                    )
                
                # Check for low performance
                if mean < 0.6:  # Below acceptable threshold
                    template_patterns["weaknesses"].append(
                        f"Low performance in {metric} (mean: {mean:.2f})"
                    )
                    template_patterns["suggestions"].append(
                        f"Optimize {metric} settings"
                    )
                elif mean > 0.8:  # Good performance
                    template_patterns["strengths"].append(
                        f"Strong performance in {metric} (mean: {mean:.2f})"
                    )
            
            patterns.append(template_patterns)
        
        return patterns

    def suggest_optimizations(self, template_name: str) -> Dict[str, Any]:
        """Generate optimization suggestions for a specific template."""
        template = get_template(template_name)
        comparison = self.analyzer.compare_templates([template_name])
        resource_usage = self.analyzer.analyze_resource_usage({template_name: []})
        
        suggestions = {
            "metrics": self._optimize_metrics(template, comparison.get(template_name, {})),
            "resources": self._optimize_resources(template, resource_usage.get(template_name, {})),
            "settings": self._optimize_settings(template)
        }
        
        return suggestions

    def _optimize_metrics(self, template: Dict[str, Any], metrics: Dict[str, Any]) -> List[str]:
        """Suggest metric optimizations."""
        suggestions = []
        
        for metric, config in template.get("metrics", {}).items():
            if not config.get("enabled", True):
                continue
            
            stats = metrics.get(metric, {})
            mean = stats.get("mean", 0)
            threshold = config.get("threshold", 0.7)
            
            if mean < threshold:
                suggestions.append(
                    f"Consider lowering {metric} threshold from {threshold:.2f} "
                    f"to {(mean + threshold)/2:.2f}"
                )
            elif mean > threshold + 0.2:
                suggestions.append(
                    f"Could increase {metric} threshold from {threshold:.2f} "
                    f"to {min(mean, 0.95):.2f}"
                )
        
        return suggestions

    def _optimize_resources(self, template: Dict[str, Any], usage: Dict[str, Any]) -> List[str]:
        """Suggest resource usage optimizations."""
        suggestions = []
        
        avg_duration = usage.get("avg_duration", 0)
        if avg_duration > 60:  # More than a minute
            suggestions.append(
                f"Long average duration ({avg_duration:.1f}s). Consider:"
                "\n- Reducing max_retries"
                "\n- Decreasing retry_delay"
                "\n- Disabling non-critical metrics"
            )
        
        action_dist = usage.get("action_distribution", {})
        total_actions = sum(action_dist.values())
        if total_actions > 0:
            for action, count in action_dist.items():
                ratio = count / total_actions
                if ratio > 0.4:  # Action dominates
                    suggestions.append(
                        f"High {action} usage ({ratio:.1%}). Consider balancing "
                        "action distribution"
                    )
        
        return suggestions

    def _optimize_settings(self, template: Dict[str, Any]) -> List[str]:
        """Suggest template setting optimizations."""
        suggestions = []
        
        system = template.get("system", {})
        if system.get("max_retries", 0) > 3:
            suggestions.append(
                "High max_retries setting might increase runtime unnecessarily"
            )
        
        analysis = template.get("analysis", {})
        if analysis.get("statistical_significance", 0.05) < 0.01:
            suggestions.append(
                "Very strict statistical significance might require more samples"
            )
        
        return suggestions

    def recommend_template(self, requirements: Dict[str, float]) -> Tuple[str, float]:
        """Recommend best template based on requirements."""
        scores = {}
        
        for template_name in TEMPLATES:
            template = get_template(template_name)
            score = self._calculate_match_score(template, requirements)
            scores[template_name] = score
        
        best_template = max(scores.items(), key=lambda x: x[1])
        return best_template

    def _calculate_match_score(self, template: Dict[str, Any], requirements: Dict[str, float]) -> float:
        """Calculate how well a template matches requirements."""
        score = 0.0
        total_weight = sum(requirements.values())
        
        for metric, weight in requirements.items():
            normalized_weight = weight / total_weight
            
            if metric in template.get("metrics", {}):
                metric_config = template["metrics"][metric]
                if metric_config.get("enabled", True):
                    score += normalized_weight * min(
                        1.0, 
                        metric_config.get("threshold", 0) / requirements.get(f"{metric}_threshold", 0.7)
                    )
        
        return score

    def generate_optimization_report(self, template_name: str) -> str:
        """Generate a detailed optimization report."""
        template = get_template(template_name)
        suggestions = self.suggest_optimizations(template_name)
        comparison = self.analyzer.compare_templates([template_name])
        patterns = self.analyze_performance_patterns(comparison)
        
        report = [
            f"# Template Optimization Report: {template_name}",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "## Performance Patterns",
        ]
        
        for pattern in patterns:
            if pattern["template"] == template_name:
                if pattern["strengths"]:
                    report.extend([
                        "\n### Strengths:",
                        *[f"- {s}" for s in pattern["strengths"]]
                    ])
                if pattern["weaknesses"]:
                    report.extend([
                        "\n### Weaknesses:",
                        *[f"- {s}" for s in pattern["weaknesses"]]
                    ])
        
        report.extend([
            "\n## Optimization Suggestions",
            "\n### Metric Optimizations:",
            *[f"- {s}" for s in suggestions["metrics"]],
            "\n### Resource Optimizations:",
            *[f"- {s}" for s in suggestions["resources"]],
            "\n### Setting Optimizations:",
            *[f"- {s}" for s in suggestions["settings"]],
        ])
        
        return "\n".join(report)

def main():
    """CLI for template optimization."""
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description="Template Optimization Tools")
    subparsers = parser.add_subparsers(dest="command")
    
    # Optimize command
    optimize_parser = subparsers.add_parser("optimize", help="Get optimization suggestions")
    optimize_parser.add_argument("template", help="Template name")
    
    # Recommend command
    recommend_parser = subparsers.add_parser("recommend", help="Get template recommendation")
    recommend_parser.add_argument("requirements", help="JSON string of requirements")
    
    # Report command
    report_parser = subparsers.add_parser("report", help="Generate optimization report")
    report_parser.add_argument("template", help="Template name")
    
    args = parser.parse_args()
    
    optimizer = TemplateOptimizer()
    
    try:
        if args.command == "optimize":
            suggestions = optimizer.suggest_optimizations(args.template)
            print(json.dumps(suggestions, indent=2))
        
        elif args.command == "recommend":
            requirements = json.loads(args.requirements)
            template, score = optimizer.recommend_template(requirements)
            print(f"Recommended template: {template} (score: {score:.2f})")
            print("\nOptimization suggestions for recommended template:")
            suggestions = optimizer.suggest_optimizations(template)
            print(json.dumps(suggestions, indent=2))
        
        elif args.command == "report":
            report = optimizer.generate_optimization_report(args.template)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"optimization_report_{args.template}_{timestamp}.md"
            
            with open(filename, 'w') as f:
                f.write(report)
            
            print(f"Report generated: {filename}")
        
        else:
            parser.print_help()
    
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
