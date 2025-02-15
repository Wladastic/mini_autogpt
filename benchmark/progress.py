"""Progress tracking and reporting for benchmark runs."""

import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import asyncio
from tqdm import tqdm

from utils.log import log

@dataclass
class ProgressStats:
    """Statistics for benchmark progress."""
    total_templates: int
    total_iterations: int
    completed_templates: int = 0
    completed_iterations: int = 0
    current_template: Optional[str] = None
    start_time: float = 0.0
    errors: int = 0
    
    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        return time.time() - self.start_time if self.start_time else 0
    
    @property
    def total_progress(self) -> float:
        """Get total progress percentage."""
        total_runs = self.total_templates * self.total_iterations
        completed_runs = (self.completed_templates * self.total_iterations) + self.completed_iterations
        return (completed_runs / total_runs * 100) if total_runs > 0 else 0
    
    @property
    def estimated_remaining(self) -> float:
        """Estimate remaining time in seconds."""
        if self.total_progress > 0:
            time_per_percent = self.elapsed_time / self.total_progress
            return time_per_percent * (100 - self.total_progress)
        return 0

class BenchmarkProgress:
    def __init__(self, total_templates: int, iterations: int, 
                 console_output: bool = True, log_file: Optional[str] = None):
        """Initialize progress tracker."""
        self.stats = ProgressStats(total_templates, iterations)
        self.stats.start_time = time.time()
        
        self.console_output = console_output
        self.log_file = log_file
        self.progress_bars = {}
        
        if console_output:
            # Initialize main progress bar
            self.main_bar = tqdm(
                total=100,
                desc="Overall Progress",
                unit="%",
                position=0
            )
            
            # Initialize template progress bar
            self.template_bar = tqdm(
                total=iterations,
                desc="Current Template",
                unit="it",
                position=1,
                leave=False
            )

    def update_progress(self, template: str, iteration: int, success: bool = True):
        """Update progress for a template iteration."""
        if not success:
            self.stats.errors += 1
        
        if template != self.stats.current_template:
            if self.stats.current_template:
                self.stats.completed_templates += 1
                self.stats.completed_iterations = 0
            self.stats.current_template = template
            if self.console_output:
                self.template_bar.reset()
                self.template_bar.set_description(f"Template: {template}")
        
        self.stats.completed_iterations = iteration
        
        if self.console_output:
            self.main_bar.n = self.stats.total_progress
            self.main_bar.refresh()
            self.template_bar.n = iteration
            self.template_bar.refresh()
        
        self._log_progress()

    def _log_progress(self):
        """Log progress to file if enabled."""
        if self.log_file:
            with open(self.log_file, 'a') as f:
                f.write(
                    f"{datetime.now().isoformat()}: "
                    f"Progress: {self.stats.total_progress:.1f}% - "
                    f"Template: {self.stats.current_template} "
                    f"({self.stats.completed_iterations}/{self.stats.total_iterations})\n"
                )

    def get_summary(self) -> Dict[str, Any]:
        """Get progress summary."""
        return {
            "total_templates": self.stats.total_templates,
            "completed_templates": self.stats.completed_templates,
            "total_iterations": self.stats.total_iterations,
            "completed_iterations": self.stats.completed_iterations,
            "elapsed_time": self.stats.elapsed_time,
            "estimated_remaining": self.stats.estimated_remaining,
            "errors": self.stats.errors,
            "total_progress": self.stats.total_progress
        }

    def print_summary(self):
        """Print progress summary."""
        summary = self.get_summary()
        
        if self.console_output:
            self.main_bar.close()
            self.template_bar.close()
        
        print("\nBenchmark Progress Summary:")
        print(f"Templates: {summary['completed_templates']}/{summary['total_templates']}")
        print(f"Iterations: {summary['completed_iterations']}/{summary['total_iterations']}")
        print(f"Progress: {summary['total_progress']:.1f}%")
        print(f"Elapsed Time: {summary['elapsed_time']:.1f}s")
        print(f"Remaining Time: {summary['estimated_remaining']:.1f}s")
        print(f"Errors: {summary['errors']}")

    async def run_with_progress(self, runner_func, templates: list, iterations: int,
                              max_workers: int = 3):
        """Run benchmark with progress tracking and parallel execution."""
        async def run_template(template: str):
            for i in range(iterations):
                try:
                    result = await runner_func(template)
                    success = "error" not in result
                    self.update_progress(template, i + 1, success)
                    yield result
                except Exception as e:
                    log(f"Error running template {template}: {e}")
                    self.update_progress(template, i + 1, False)
                    yield {"error": str(e)}

        # Create task groups for parallel execution
        tasks = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for template in templates:
                task = asyncio.create_task(
                    self._run_template_async(executor, run_template, template)
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
        
        return results

    async def _run_template_async(self, executor, run_template, template: str):
        """Run template asynchronously."""
        results = []
        async for result in run_template(template):
            results.append(result)
        return template, results

def create_progress_tracker(total_templates: int, iterations: int, 
                          output_dir: str) -> BenchmarkProgress:
    """Create a progress tracker with logging."""
    log_file = f"{output_dir}/benchmark_progress.log"
    return BenchmarkProgress(
        total_templates=total_templates,
        iterations=iterations,
        console_output=True,
        log_file=log_file
    )
