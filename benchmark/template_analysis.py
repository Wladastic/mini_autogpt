"""Analysis tools for comparing and evaluating template performance."""

import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.log import log
from benchmark.templates import TEMPLATES, get_template
from benchmark.validation import validate_and_update_config

class TemplateAnalyzer:
    def __init__(self, results_dir="benchmark/results", output_dir="benchmark/analysis"):
        """Initialize template analyzer."""
        self.results_dir = results_dir
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def load_results_by_template(self) -> Dict[str, List[Dict]]:
        """Load benchmark results grouped by template."""
        template_results = defaultdict(list)
        
        for filename in os.listdir(self.results_dir):
            if not filename.endswith('.json'):
                continue
            
            with open(os.path.join(self.results_dir, filename), 'r') as f:
                result = json.load(f)
                template_name = result.get("template", "unknown")
                template_results[template_name].append(result)
        
        return dict(template_results)

    def calculate_template_metrics(self, results: List[Dict]) -> Dict[str, Any]:
        """Calculate performance metrics for a template's results."""
        if not results:
            return {}

        metrics = defaultdict(list)
        for result in results:
            for metric, value in result.get("metrics", {}).items():
                if isinstance(value, (int, float)):
                    metrics[metric].append(value)

        summary = {}
        for metric, values in metrics.items():
            summary[metric] = {
                "mean": np.mean(values),
                "std": np.std(values),
                "min": np.min(values),
                "max": np.max(values),
                "median": np.median(values),
                "count": len(values)
            }

        return summary

    def compare_templates(self, templates: Optional[List[str]] = None) -> Dict[str, Any]:
        """Compare performance metrics across templates."""
        results = self.load_results_by_template()
        
        if templates:
            results = {k: v for k, v in results.items() if k in templates}
        
        comparison = {}
        for template_name, template_results in results.items():
            comparison[template_name] = self.calculate_template_metrics(template_results)
        
        return comparison

    def create_comparison_plots(self, comparison: Dict[str, Any]) -> None:
        """Create visualization plots for template comparison."""
        metrics = set()
        for template_data in comparison.values():
            metrics.update(template_data.keys())
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{self.output_dir}/template_comparison_{timestamp}.html"
        
        # Create subplots for each metric
        fig = make_subplots(
            rows=len(metrics),
            cols=1,
            subplot_titles=list(metrics),
            vertical_spacing=0.1
        )
        
        for idx, metric in enumerate(metrics, 1):
            means = []
            stds = []
            templates = []
            
            for template, data in comparison.items():
                if metric in data:
                    means.append(data[metric]["mean"])
                    stds.append(data[metric]["std"])
                    templates.append(template)
            
            # Add bar chart
            fig.add_trace(
                go.Bar(
                    name=metric,
                    x=templates,
                    y=means,
                    error_y=dict(type='data', array=stds),
                    showlegend=False
                ),
                row=idx,
                col=1
            )
        
        fig.update_layout(
            height=300 * len(metrics),
            title="Template Performance Comparison",
            showlegend=True
        )
        
        fig.write_html(output_file)
        log(f"Comparison plots saved to {output_file}")

    def analyze_resource_usage(self, results: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Analyze resource usage patterns across templates."""
        usage = {}
        
        for template_name, template_results in results.items():
            template_usage = defaultdict(list)
            
            for result in template_results:
                # Collect time statistics
                template_usage["duration"].append(result.get("duration", 0))
                
                # Count action types
                for log in result.get("debug_logs", []):
                    action_type = log.get("request_type", "unknown")
                    template_usage["actions"][action_type] = \
                        template_usage["actions"].get(action_type, 0) + 1
            
            usage[template_name] = {
                "avg_duration": np.mean(template_usage["duration"]),
                "total_actions": sum(template_usage["actions"].values()),
                "action_distribution": dict(template_usage["actions"])
            }
        
        return usage

    def generate_report(self, templates: Optional[List[str]] = None) -> str:
        """Generate a comprehensive analysis report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"{self.output_dir}/template_analysis_{timestamp}.md"
        
        results = self.load_results_by_template()
        if templates:
            results = {k: v for k, v in results.items() if k in templates}
        
        comparison = self.compare_templates(templates)
        resource_usage = self.analyze_resource_usage(results)
        
        # Create report content
        report = [
            "# Template Analysis Report",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "## Performance Metrics",
        ]
        
        # Add metric comparisons
        for template, metrics in comparison.items():
            report.extend([
                f"\n### {template}",
                "| Metric | Mean | Std | Min | Max | Median | Count |",
                "|--------|------|-----|-----|-----|---------|-------|",
            ])
            
            for metric, stats in metrics.items():
                report.append(
                    f"| {metric} | {stats['mean']:.3f} | {stats['std']:.3f} | "
                    f"{stats['min']:.3f} | {stats['max']:.3f} | {stats['median']:.3f} | "
                    f"{stats['count']} |"
                )
        
        # Add resource usage
        report.extend([
            "",
            "## Resource Usage",
        ])
        
        for template, usage in resource_usage.items():
            report.extend([
                f"\n### {template}",
                f"- Average Duration: {usage['avg_duration']:.2f}s",
                f"- Total Actions: {usage['total_actions']}",
                "\nAction Distribution:",
            ])
            
            for action, count in usage["action_distribution"].items():
                report.append(f"- {action}: {count}")
        
        # Write report
        with open(report_file, 'w') as f:
            f.write("\n".join(report))
        
        # Generate plots
        self.create_comparison_plots(comparison)
        
        log(f"Analysis report generated: {report_file}")
        return report_file

def main():
    """CLI for template analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Template Analysis Tools")
    subparsers = parser.add_subparsers(dest="command")
    
    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Compare template performance")
    compare_parser.add_argument("--templates", nargs="+", help="Templates to compare")
    
    # Report command
    report_parser = subparsers.add_parser("report", help="Generate analysis report")
    report_parser.add_argument("--templates", nargs="+", help="Templates to analyze")
    
    args = parser.parse_args()
    
    analyzer = TemplateAnalyzer()
    
    try:
        if args.command == "compare":
            comparison = analyzer.compare_templates(args.templates)
            analyzer.create_comparison_plots(comparison)
            print(json.dumps(comparison, indent=2))
        
        elif args.command == "report":
            report_file = analyzer.generate_report(args.templates)
            print(f"Report generated: {report_file}")
        
        else:
            parser.print_help()
    
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
