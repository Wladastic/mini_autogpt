"""System resource monitoring for benchmark runs."""

import os
import time
import psutil
import threading
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json

from utils.log import log

@dataclass
class ResourceStats:
    """Resource usage statistics."""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used: float  # In MB
    swap_used: float    # In MB
    disk_io_read: float # In MB/s
    disk_io_write: float # In MB/s
    network_sent: float # In MB/s
    network_recv: float # In MB/s
    num_threads: int
    num_processes: int

class ResourceMonitor:
    def __init__(self, output_dir: str = "benchmark/monitoring",
                 interval: float = 1.0):
        """Initialize resource monitor."""
        self.output_dir = output_dir
        self.interval = interval
        self.monitoring = False
        self.stats: List[ResourceStats] = []
        self._monitor_thread: Optional[threading.Thread] = None
        self._last_disk_io: Optional[Tuple[float, float]] = None
        self._last_network_io: Optional[Tuple[float, float]] = None
        self._last_time: Optional[float] = None

        os.makedirs(output_dir, exist_ok=True)

    def start(self):
        """Start monitoring resources."""
        if self.monitoring:
            return

        self.monitoring = True
        self.stats = []
        self._monitor_thread = threading.Thread(target=self._monitor_loop)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
        log("Resource monitoring started")

    def stop(self) -> Dict[str, Any]:
        """Stop monitoring and return statistics."""
        if not self.monitoring:
            return self.get_summary()

        self.monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join()
            self._monitor_thread = None

        log("Resource monitoring stopped")
        return self.get_summary()

    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                stats = self._collect_stats()
                self.stats.append(stats)
                time.sleep(self.interval)
            except Exception as e:
                log(f"Error in resource monitoring: {e}")

    def _collect_stats(self) -> ResourceStats:
        """Collect current resource statistics."""
        current_time = time.time()

        # Get CPU and memory stats
        cpu_percent = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()

        # Get disk I/O stats
        disk_io = psutil.disk_io_counters()
        if self._last_disk_io and self._last_time:
            time_diff = current_time - self._last_time
            read_speed = (disk_io.read_bytes - self._last_disk_io[0]) / time_diff / 1024 / 1024
            write_speed = (disk_io.write_bytes - self._last_disk_io[1]) / time_diff / 1024 / 1024
        else:
            read_speed = write_speed = 0.0
        self._last_disk_io = (disk_io.read_bytes, disk_io.write_bytes)

        # Get network I/O stats
        net_io = psutil.net_io_counters()
        if self._last_network_io and self._last_time:
            time_diff = current_time - self._last_time
            sent_speed = (net_io.bytes_sent - self._last_network_io[0]) / time_diff / 1024 / 1024
            recv_speed = (net_io.bytes_recv - self._last_network_io[1]) / time_diff / 1024 / 1024
        else:
            sent_speed = recv_speed = 0.0
        self._last_network_io = (net_io.bytes_sent, net_io.bytes_recv)

        self._last_time = current_time

        return ResourceStats(
            timestamp=current_time,
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used=memory.used / 1024 / 1024,  # Convert to MB
            swap_used=swap.used / 1024 / 1024,      # Convert to MB
            disk_io_read=read_speed,
            disk_io_write=write_speed,
            network_sent=sent_speed,
            network_recv=recv_speed,
            num_threads=threading.active_count(),
            num_processes=len(psutil.Process().children())
        )

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of resource usage."""
        if not self.stats:
            return {}

        # Calculate statistics
        cpu_percentages = [s.cpu_percent for s in self.stats]
        memory_percentages = [s.memory_percent for s in self.stats]
        memory_used = [s.memory_used for s in self.stats]
        swap_used = [s.swap_used for s in self.stats]
        disk_read = [s.disk_io_read for s in self.stats]
        disk_write = [s.disk_io_write for s in self.stats]
        net_sent = [s.network_sent for s in self.stats]
        net_recv = [s.network_recv for s in self.stats]

        def calc_stats(values: List[float]) -> Dict[str, float]:
            if not values:
                return {"min": 0, "max": 0, "avg": 0}
            return {
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values)
            }

        summary = {
            "duration": self.stats[-1].timestamp - self.stats[0].timestamp,
            "samples": len(self.stats),
            "cpu": calc_stats(cpu_percentages),
            "memory": calc_stats(memory_percentages),
            "memory_used_mb": calc_stats(memory_used),
            "swap_used_mb": calc_stats(swap_used),
            "disk_read_mbs": calc_stats(disk_read),
            "disk_write_mbs": calc_stats(disk_write),
            "network_sent_mbs": calc_stats(net_sent),
            "network_recv_mbs": calc_stats(net_recv),
            "max_threads": max(s.num_threads for s in self.stats),
            "max_processes": max(s.num_processes for s in self.stats)
        }

        self.save_stats(summary)
        return summary

    def save_stats(self, summary: Dict[str, Any]):
        """Save monitoring statistics."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save summary
        summary_file = os.path.join(self.output_dir, f"monitor_summary_{timestamp}.json")
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Save detailed stats
        details_file = os.path.join(self.output_dir, f"monitor_details_{timestamp}.json")
        with open(details_file, 'w') as f:
            json.dump([{
                "timestamp": s.timestamp,
                "cpu_percent": s.cpu_percent,
                "memory_percent": s.memory_percent,
                "memory_used_mb": s.memory_used,
                "swap_used_mb": s.swap_used,
                "disk_read_mbs": s.disk_io_read,
                "disk_write_mbs": s.disk_io_write,
                "network_sent_mbs": s.network_sent,
                "network_recv_mbs": s.network_recv,
                "num_threads": s.num_threads,
                "num_processes": s.num_processes
            } for s in self.stats], f, indent=2)
        
        log(f"Monitoring data saved to {summary_file} and {details_file}")

class MonitoredBenchmark:
    """Context manager for monitoring benchmark runs."""
    def __init__(self, output_dir: str = "benchmark/monitoring"):
        self.monitor = ResourceMonitor(output_dir)

    def __enter__(self):
        self.monitor.start()
        return self.monitor

    def __exit__(self, exc_type, exc_val, exc_tb):
        summary = self.monitor.stop()
        if exc_type is not None:
            log(f"Benchmark failed with error: {exc_val}")
        return False  # Don't suppress exceptions
