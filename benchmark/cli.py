"""Command line interface for benchmark system."""

import argparse
import asyncio
import os
from datetime import datetime

from utils.log import log
from benchmark.runner import BenchmarkRunner
from benchmark.test_scenarios import generate_test_dataset, verify_mock_data
from benchmark.visualizer import BenchmarkVisualizer
from benchmark.assessment import AssessmentEngine
from benchmark.statistics import BenchmarkStatistics

def setup_directories():
    """Create required benchmark directories."""
    dirs = [
        "benchmark/results",
        "benchmark/visualizations",
        "benchmark/reports",
        "benchmark/logs",
        "benchmark/statistics",
        "benchmark/mock_data"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

async def run_benchmark(args):
    """Run benchmark with specified options."""
    runner = BenchmarkRunner()
    log("Starting benchmark run...")
    
    if args.model:
        log(f"Filtering for model: {args.model}")
    if args.scenario:
        log(f"Filtering for scenario: {args.scenario}")
    
    results = await runner.run_all()
    log("Benchmark complete!")
    
    if args.analyze:
        log("Generating analysis...")
        analyzer = AssessmentEngine()
        report = await analyzer.create_report(results)
        log(f"Analysis report generated: {report}")
    
    if args.visualize:
        log("Creating visualizations...")
        visualizer = BenchmarkVisualizer()
        viz_report = visualizer.generate_visualization_report()
        log(f"Visualization report generated: {viz_report}")
    
    if args.stats:
        log("Performing statistical analysis...")
        stats = BenchmarkStatistics()
        stats_report = stats.generate_report()
        log(f"Statistical report generated: {stats_report}")

async def generate_mock_data(args):
    """Generate and verify mock test data."""
    log("Generating mock dataset...")
    results = await generate_test_dataset()
    
    if args.verify:
        log("Verifying mock data...")
        issues = verify_mock_data(results)
        if issues:
            log("Issues found in mock data:")
            for issue in issues:
                log(f"- {issue}")
        else:
            log("Mock data verification successful!")

def generate_reports(args):
    """Generate reports from existing benchmark data."""
    if args.assessment or args.all:
        log("Generating assessment report...")
        analyzer = AssessmentEngine()
        asyncio.run(analyzer.create_report())
    
    if args.visualization or args.all:
        log("Generating visualization report...")
        visualizer = BenchmarkVisualizer()
        visualizer.generate_visualization_report()
    
    if args.statistics or args.all:
        log("Generating statistical report...")
        stats = BenchmarkStatistics()
        stats.generate_report()

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Benchmark System CLI")
    subparsers = parser.add_subparsers(dest='command')

    # Run benchmark command
    run_parser = subparsers.add_parser('run', help='Run benchmarks')
    run_parser.add_argument('--model', help='Filter specific model')
    run_parser.add_argument('--scenario', help='Filter specific scenario')
    run_parser.add_argument('--analyze', action='store_true', help='Generate analysis report')
    run_parser.add_argument('--visualize', action='store_true', help='Generate visualizations')
    run_parser.add_argument('--stats', action='store_true', help='Generate statistical analysis')

    # Generate mock data command
    mock_parser = subparsers.add_parser('mock', help='Generate mock test data')
    mock_parser.add_argument('--verify', action='store_true', help='Verify generated mock data')

    # Generate reports command
    report_parser = subparsers.add_parser('report', help='Generate reports')
    report_parser.add_argument('--all', action='store_true', help='Generate all reports')
    report_parser.add_argument('--assessment', action='store_true', help='Generate assessment report')
    report_parser.add_argument('--visualization', action='store_true', help='Generate visualization report')
    report_parser.add_argument('--statistics', action='store_true', help='Generate statistical report')

    args = parser.parse_args()

    try:
        setup_directories()

        if args.command == 'run':
            asyncio.run(run_benchmark(args))
        elif args.command == 'mock':
            asyncio.run(generate_mock_data(args))
        elif args.command == 'report':
            generate_reports(args)
        else:
            parser.print_help()

    except KeyboardInterrupt:
        log("\nOperation interrupted by user")
    except Exception as e:
        log(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    main()
