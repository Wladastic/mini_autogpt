#!/usr/bin/env python3
"""Complete benchmark runner with profiling and analysis."""

import os
import sys
import json
import argparse
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional

from benchmark.config import BenchmarkConfig
from benchmark.profiles import ProfileManager
from benchmark.templates import TEMPLATES
from benchmark.auto_tuning import TemplateTuner
from benchmark.learning import TemplateOptimizationLearner
from benchmark.visualizer import BenchmarkVisualizer
from benchmark.progress import create_progress_tracker
from benchmark.monitor import MonitoredBenchmark
from tests.profiling import BenchmarkProfiler
from tests.profile_visualizer import ProfileVisualizer
from utils.log import log

class BenchmarkRunner:
    def __init__(self, config_file: Optional[str] = None):
        """Initialize benchmark runner."""
        self.config = BenchmarkConfig(config_file)
        self.profile_manager = ProfileManager()
        self.tuner = TemplateTuner()
        self.learner = TemplateOptimizationLearner()
        self.visualizer = BenchmarkVisualizer()
        self.profiler = BenchmarkProfiler()

    async def run_benchmark(self, templates: List[str] = None, iterations: int = 1,
                          max_workers: int = 3, show_progress: bool = True,
                          monitor_resources: bool = True):
        """Run complete benchmark suite with parallel execution and progress tracking."""
        templates = templates or list(TEMPLATES.keys())
        
        # Initialize progress tracker
        progress = create_progress_tracker(
            total_templates=len(templates),
            iterations=iterations,
            output_dir=self.config.get_path("results"),
        ) if show_progress else None
        
        log("Starting benchmark run...")
        
        try:
            if progress:
                # Run benchmarks in parallel with progress tracking
                template_results = await progress.run_with_progress(
                    runner_func=self.run_single_benchmark,
                    templates=templates,
                    iterations=iterations,
                    max_workers=max_workers
                )
            else:
                # Run without progress tracking
                template_results = await self._run_parallel(
                    templates, iterations, max_workers
                )
            
            # Convert results to dictionary format
            results = {}
            for template_name, template_data in template_results:
                results[template_name] = template_data
            
            if progress:
                progress.print_summary()
            
            return results
            
        except Exception as e:
            log(f"Error in benchmark run: {e}")
            if progress:
                progress.print_summary()
            raise

    async def _run_parallel(self, templates: List[str], iterations: int, max_workers: int):
        """Run benchmarks in parallel without progress tracking."""
        async def run_template(template_name: str):
            results = []
            template = self.profile_manager.load_profile(template_name)
            for _ in range(iterations):
                result = await self.run_single_benchmark(template_name, template)
                results.append(result)
            return template_name, results

        tasks = [asyncio.create_task(run_template(t)) for t in templates]
        return await asyncio.gather(*tasks)

    async def run_single_benchmark(self, template_name: str, template: Dict[str, Any]):
        """Run benchmark for a single template."""
        result = {
            "template": template_name,
            "timestamp": datetime.now().isoformat(),
            "metrics": {},
            "profiling": {},
            "optimization": None
        }

        try:
            with self.profiler.profile_operation("benchmark"):
                # Run optimization
                target_metrics = {
                    "response_quality": 0.9,
                    "context_usage": 0.8,
                    "memory_retention": 0.8
                }
                optimized = self.tuner.tune_template(
                    template_name,
                    target_metrics,
                    max_iterations=5
                )
                result["optimization"] = {
                    "initial": template,
                    "optimized": optimized,
                    "target_metrics": target_metrics
                }

                # Run learning pipeline
                predictions = self.learner.predict_performance(optimized)
                result["metrics"] = predictions

        except Exception as e:
            log(f"Error in benchmark run: {e}")
            result["error"] = str(e)

        return result

    def analyze_results(self, results: Dict[str, Any], monitoring_data: Optional[Dict] = None):
        """Analyze benchmark results."""
        log("Analyzing results...")
        
        # Generate visualizations
        viz_report = self.visualizer.generate_visualization_report()
        log(f"Visualization report generated: {viz_report}")
        
        # Generate profiling visualizations
        profile_viz = ProfileVisualizer()
        profile_report = profile_viz.generate_visualization_report()
        log(f"Profile visualization report generated: {profile_report}")
        
        return {
            "visualization_report": viz_report,
            "profile_report": profile_report,
            "results": results,
            "monitoring": monitoring_data
        }

def main():
    """Main benchmark runner."""
    parser = argparse.ArgumentParser(description="Benchmark Runner")
    
    parser.add_argument(
        "--templates",
        nargs="+",
        help="Templates to benchmark (default: all)"
    )
    
    parser.add_argument(
        "--iterations",
        type=int,
        default=1,
        help="Number of iterations per template"
    )
    
    parser.add_argument(
        "--config",
        help="Path to config file"
    )
    
    parser.add_argument(
        "--output",
        default="benchmark_results",
        help="Output directory for results"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=3,
        help="Number of parallel workers (default: 3)"
    )
    
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress bars"
    )
    
    parser.add_argument(
        "--no-monitoring",
        action="store_true",
        help="Disable resource monitoring"
    )
    
    parser.add_argument(
        "--monitor-interval",
        type=float,
        default=1.0,
        help="Resource monitoring interval in seconds (default: 1.0)"
    )

    args = parser.parse_args()

    # Create output directory
    os.makedirs(args.output, exist_ok=True)

    monitoring_data = None
    try:
        # Run benchmark with parallel execution and monitoring
        runner = BenchmarkRunner(args.config)
        
        if not args.no_monitoring:
            with MonitoredBenchmark(
                os.path.join(args.output, "monitoring")
            ) as monitor:
                results = asyncio.run(
                    runner.run_benchmark(
                        templates=args.templates,
                        iterations=args.iterations,
                        max_workers=args.workers,
                        show_progress=not args.no_progress
                    )
                )
                monitoring_data = monitor.get_summary()
        else:
            results = asyncio.run(
                runner.run_benchmark(
                    templates=args.templates,
                    iterations=args.iterations,
                    max_workers=args.workers,
                    show_progress=not args.no_progress
                )
            )
        
        # Analyze results
        analysis = runner.analyze_results(results, monitoring_data)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = os.path.join(args.output, f"results_{timestamp}.json")
        
        with open(results_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        # Print summary
        summary = [
            "\nBenchmark completed successfully!",
            f"\nResults saved to: {results_file}",
            f"Visualization report: {analysis['visualization_report']}",
            f"Profile report: {analysis['profile_report']}",
            "\nSummary:",
            f"- Templates tested: {len(results)}",
            f"- Total iterations: {args.iterations * len(results)}",
            f"- Output directory: {args.output}",
            f"- Workers used: {args.workers}"
        ]
        
        if monitoring_data:
            summary.extend([
                "\nResource Usage:",
                f"- CPU (avg): {monitoring_data['cpu']['avg']:.1f}%",
                f"- Memory (avg): {monitoring_data['memory']['avg']:.1f}%",
                f"- Disk I/O: {monitoring_data['disk_read_mbs']['avg']:.1f} MB/s read, "
                f"{monitoring_data['disk_write_mbs']['avg']:.1f} MB/s write",
                f"- Peak threads: {monitoring_data['max_threads']}"
            ])
        
        log("\n".join(summary))

    except Exception as e:
        log(f"Error running benchmark: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
