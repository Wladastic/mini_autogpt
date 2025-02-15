"""Performance profiling tools for benchmark system."""

import os
import time
import cProfile
import pstats
import io
import functools
from typing import Dict, Any, Callable, Optional
from datetime import datetime
from contextlib import contextmanager

import line_profiler
import memory_profiler
from pyinstrument import Profiler

from utils.log import log

class PerformanceProfile:
    def __init__(self, output_dir: str = "tests/profiling"):
        """Initialize performance profiler."""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.stats = {}

    def profile_function(self, func: Callable) -> Callable:
        """Decorator to profile a function."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            profiler = cProfile.Profile()
            try:
                return profiler.runcall(func, *args, **kwargs)
            finally:
                stats = pstats.Stats(profiler)
                self._save_profile_stats(func.__name__, stats)
        return wrapper

    def profile_memory(self, func: Callable) -> Callable:
        """Decorator to profile memory usage."""
        @functools.wraps(func)
        @memory_profiler.profile(precision=4)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper

    def profile_line_by_line(self, func: Callable) -> Callable:
        """Decorator for line-by-line profiling."""
        profiler = line_profiler.LineProfiler()
        wrapped = profiler(func)
        wrapped.profile = profiler
        return wrapped

    @contextmanager
    def profile_block(self, name: str):
        """Context manager for profiling a block of code."""
        profiler = Profiler()
        profiler.start()
        try:
            yield
        finally:
            profiler.stop()
            self._save_block_profile(name, profiler)

    def _save_profile_stats(self, name: str, stats: pstats.Stats):
        """Save profiling statistics."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/profile_{name}_{timestamp}"
        
        # Save stats file
        stats.dump_stats(f"{filename}.prof")
        
        # Save readable report
        with open(f"{filename}.txt", 'w') as f:
            stats = pstats.Stats(f"{filename}.prof", stream=f)
            stats.sort_stats('cumulative')
            stats.print_stats()

    def _save_block_profile(self, name: str, profiler: Profiler):
        """Save block profiling results."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/block_{name}_{timestamp}"
        
        # Save HTML report
        profiler.write_html(f"{filename}.html")
        
        # Save text report
        with open(f"{filename}.txt", 'w') as f:
            f.write(profiler.output_text())

class BenchmarkProfiler:
    def __init__(self):
        """Initialize benchmark profiler."""
        self.profiler = PerformanceProfile()
        self.results = {}

    def profile_template_optimization(self, template: Dict[str, Any], target_metrics: Dict[str, float]):
        """Profile template optimization process."""
        from benchmark.auto_tuning import TemplateTuner
        
        @self.profiler.profile_function
        def run_optimization():
            tuner = TemplateTuner()
            return tuner.tune_template(
                template_name="profile_test",
                target_metrics=target_metrics
            )
        
        with self.profiler.profile_block("template_optimization"):
            result = run_optimization()
            
        return result

    def profile_learning_pipeline(self, template_name: str, num_samples: int = 10):
        """Profile the learning pipeline."""
        from benchmark.learning import TemplateOptimizationLearner
        from tests.mock_data import MockDataGenerator
        
        @self.profiler.profile_memory
        def run_learning():
            learner = TemplateOptimizationLearner()
            generator = MockDataGenerator()
            data = generator.generate_performance_data(template_name, num_samples)
            
            for entry in data:
                learner.add_training_data(template_name, entry["metrics"])
            
            return learner.predict_performance(generator.MOCK_TEMPLATES[template_name])
        
        with self.profiler.profile_block("learning_pipeline"):
            result = run_learning()
            
        return result

    @contextmanager
    def profile_operation(self, name: str):
        """Context manager for profiling operations."""
        start_time = time.time()
        start_memory = memory_profiler.memory_usage()[0]
        
        try:
            yield
        finally:
            end_time = time.time()
            end_memory = memory_profiler.memory_usage()[0]
            
            self.results[name] = {
                "duration": end_time - start_time,
                "memory_delta": end_memory - start_memory
            }

def profile_benchmark_system():
    """Run complete system profiling."""
    profiler = BenchmarkProfiler()
    
    # Profile template optimization
    with profiler.profile_operation("optimization"):
        result = profiler.profile_template_optimization(
            template={"metrics": {"response_quality": {"threshold": 0.8}}},
            target_metrics={"response_quality": 0.9}
        )
    
    # Profile learning pipeline
    with profiler.profile_operation("learning"):
        result = profiler.profile_learning_pipeline("thorough", num_samples=10)
    
    return profiler.results

def generate_profile_report():
    """Generate a comprehensive profiling report."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"tests/profiling/report_{timestamp}.md"
    
    results = profile_benchmark_system()
    
    report = [
        "# Benchmark System Profiling Report",
        f"Generated: {datetime.now().isoformat()}",
        "",
        "## Operation Timings",
        "| Operation | Duration (s) | Memory Delta (MB) |",
        "|-----------|--------------|-------------------|"
    ]
    
    for operation, metrics in results.items():
        report.append(
            f"| {operation} | {metrics['duration']:.3f} | "
            f"{metrics['memory_delta']:.2f} |"
        )
    
    # Add profiling data locations
    report.extend([
        "",
        "## Detailed Profiling Data",
        "Detailed profiling data is available in the following files:",
        "",
        "* Profile stats: `tests/profiling/*.prof`",
        "* Text reports: `tests/profiling/*.txt`",
        "* HTML visualizations: `tests/profiling/*.html`"
    ])
    
    with open(report_file, 'w') as f:
        f.write("\n".join(report))
    
    return report_file

def main():
    """Run profiling and generate report."""
    try:
        report_file = generate_profile_report()
        print(f"Profiling report generated: {report_file}")
    except Exception as e:
        print(f"Error running profiling: {e}")

if __name__ == "__main__":
    main()
