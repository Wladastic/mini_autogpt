"""Assessment engine for analyzing benchmark results."""

import json
import os
from datetime import datetime
from typing import Dict, List, Any

import utils.llm as llm
from utils.log import log

ASSESSMENT_PROMPT = """You are an AI system assessor. Analyze the provided benchmark results and generate a detailed assessment.
Focus on:
1. Performance metrics and their meaning
2. Pattern recognition in behavior
3. Strengths and weaknesses
4. Areas for improvement
5. Comparative analysis with other results

Provide specific examples and evidence for your conclusions. Be analytical and thorough."""

class AssessmentEngine:
    def __init__(self, results_dir="benchmark/results", reports_dir="benchmark/reports"):
        """Initialize the assessment engine."""
        self.results_dir = results_dir
        self.reports_dir = reports_dir
        os.makedirs(reports_dir, exist_ok=True)

    def load_results(self, filter_model=None, filter_scenario=None) -> List[Dict]:
        """Load benchmark results, optionally filtered by model or scenario."""
        results = []
        try:
            for filename in os.listdir(self.results_dir):
                if not filename.endswith('.json'):
                    continue
                
                if filter_model and filter_model not in filename:
                    continue
                    
                if filter_scenario and filter_scenario not in filename:
                    continue

                with open(os.path.join(self.results_dir, filename), 'r') as f:
                    result = json.load(f)
                    results.append(result)
        except Exception as e:
            log(f"Error loading results: {e}")
        
        return results

    def analyze_metrics(self, results: List[Dict]) -> Dict[str, Any]:
        """Analyze metrics across results."""
        if not results:
            return {}

        analysis = {
            "total_runs": len(results),
            "models_tested": set(),
            "scenarios_tested": set(),
            "average_metrics": {},
            "best_performing": {},
            "worst_performing": {},
            "error_patterns": {},
            "action_patterns": {}
        }

        # Collect unique models and scenarios
        for result in results:
            analysis["models_tested"].add(result["model"])
            analysis["scenarios_tested"].add(result["scenario"])

        # Convert sets to lists for JSON serialization
        analysis["models_tested"] = list(analysis["models_tested"])
        analysis["scenarios_tested"] = list(analysis["scenarios_tested"])

        # Calculate averages and find extremes
        metrics_sum = {}
        for result in results:
            metrics = result["metrics"]
            for metric, value in metrics.items():
                if isinstance(value, (int, float)):
                    metrics_sum[metric] = metrics_sum.get(metric, 0) + value

                    # Track best and worst
                    if metric not in analysis["best_performing"]:
                        analysis["best_performing"][metric] = {
                            "value": value,
                            "model": result["model"],
                            "scenario": result["scenario"]
                        }
                        analysis["worst_performing"][metric] = {
                            "value": value,
                            "model": result["model"],
                            "scenario": result["scenario"]
                        }
                    else:
                        if value > analysis["best_performing"][metric]["value"]:
                            analysis["best_performing"][metric] = {
                                "value": value,
                                "model": result["model"],
                                "scenario": result["scenario"]
                            }
                        if value < analysis["worst_performing"][metric]["value"]:
                            analysis["worst_performing"][metric] = {
                                "value": value,
                                "model": result["model"],
                                "scenario": result["scenario"]
                            }

        # Calculate averages
        for metric, total in metrics_sum.items():
            analysis["average_metrics"][metric] = total / len(results)

        # Analyze action patterns
        action_counts = {}
        for result in results:
            for entry in result.get("debug_logs", []):
                if "request_type" in entry:
                    action_type = entry["request_type"]
                    action_counts[action_type] = action_counts.get(action_type, 0) + 1

        analysis["action_patterns"] = action_counts

        return analysis

    async def generate_assessment(self, results: List[Dict]) -> str:
        """Generate a natural language assessment using LLM."""
        if not results:
            return "No results to assess."

        # Prepare data for LLM
        analysis = self.analyze_metrics(results)
        assessment_data = {
            "metrics_analysis": analysis,
            "raw_results": results
        }

        # Create prompt for LLM
        history = [
            {"role": "system", "content": ASSESSMENT_PROMPT},
            {"role": "user", "content": f"Please analyze these benchmark results: {json.dumps(assessment_data, indent=2)}"}
        ]

        try:
            response = llm.one_shot_request(
                prompt=json.dumps(assessment_data, indent=2),
                system_context=ASSESSMENT_PROMPT
            )
            
            if response:
                return response
            else:
                return "Error generating assessment."
        except Exception as e:
            log(f"Error generating assessment: {e}")
            return f"Error generating assessment: {str(e)}"

    async def create_report(self, results: List[Dict] = None) -> str:
        """Create a comprehensive report of benchmark results."""
        if results is None:
            results = self.load_results()

        if not results:
            return "No results to report."

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"{self.reports_dir}/report_{timestamp}.md"

        analysis = self.analyze_metrics(results)
        assessment = await self.generate_assessment(results)

        # Create markdown report
        report = [
            "# Benchmark Assessment Report",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "## Overview",
            f"- Total Runs: {analysis['total_runs']}",
            f"- Models Tested: {', '.join(analysis['models_tested'])}",
            f"- Scenarios Tested: {', '.join(analysis['scenarios_tested'])}",
            "",
            "## Metrics Summary",
            "### Average Metrics",
        ]

        # Add metrics details
        for metric, value in analysis["average_metrics"].items():
            report.append(f"- {metric}: {value:.3f}")

        report.extend([
            "",
            "## Best Performing Cases",
        ])

        for metric, data in analysis["best_performing"].items():
            report.append(f"### {metric}")
            report.append(f"- Value: {data['value']:.3f}")
            report.append(f"- Model: {data['model']}")
            report.append(f"- Scenario: {data['scenario']}")

        report.extend([
            "",
            "## Action Patterns",
        ])

        for action, count in analysis["action_patterns"].items():
            report.append(f"- {action}: {count} occurrences")

        report.extend([
            "",
            "## LLM Assessment",
            assessment
        ])

        # Write report to file
        with open(report_file, 'w') as f:
            f.write("\n".join(report))

        log(f"Report generated: {report_file}")
        return report_file

async def main():
    """Run a complete assessment."""
    engine = AssessmentEngine()
    await engine.create_report()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
