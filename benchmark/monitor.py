"""Resource monitoring for benchmark runs."""

import os
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import contextmanager

from benchmark.monitor_simple import create_monitor, SimpleMonitor
from utils.log import log

class BenchmarkMonitor:
    def __init__(self, output_dir: str = "benchmark/monitoring"):
        """Initialize benchmark monitor."""
        self.output_dir = output_dir
        self.monitor = create_monitor(notify_telegram=True)
        os.makedirs(output_dir, exist_ok=True)

    @contextmanager
    def monitor_run(self, name: str):
        """Context manager for monitoring a benchmark run."""
        start_time = datetime.now()
        log(f"Starting monitoring for: {name}")
        
        try:
            yield self.monitor
        finally:
            # Get monitoring summary
            summary = self.monitor.get_summary()
            duration = (datetime.now() - start_time).total_seconds()
            
            # Save monitoring results
            self.save_results(name, summary, duration)
            
            log(f"Monitoring completed for: {name}")
            if summary.get("alerts", 0) > 0:
                log(f"Alerts during run: {summary['alerts']}")

    def save_results(self, name: str, summary: Dict[str, Any], duration: float):
        """Save monitoring results."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.output_dir, f"{name}_{timestamp}.json")
        
        results = {
            "name": name,
            "timestamp": timestamp,
            "duration": duration,
            "summary": summary
        }
        
        with open(filename, "w") as f:
            json.dump(results, f, indent=2)

def create_benchmark_monitor(output_dir: Optional[str] = None) -> BenchmarkMonitor:
    """Create benchmark monitor."""
    return BenchmarkMonitor(output_dir or "benchmark/monitoring")
