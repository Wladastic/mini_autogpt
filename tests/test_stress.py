"""Stress testing for the benchmark system."""

import os
import time
import asyncio
import multiprocessing
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import pytest

from benchmark.config import BenchmarkConfig
from benchmark.profiles import ProfileManager
from benchmark.learning import TemplateOptimizationLearner
from benchmark.auto_tuning import TemplateTuner
from tests.mock_data import MockDataGenerator, MOCK_TEMPLATES

class StressTestMetrics:
    def __init__(self):
        self.start_time = time.time()
        self.operation_times = []
        self.error_count = 0
        self.success_count = 0
        self.memory_usage = []

    def record_operation(self, duration: float, success: bool):
        """Record an operation's metrics."""
        self.operation_times.append(duration)
        if success:
            self.success_count += 1
        else:
            self.error_count += 1

    def record_memory(self, usage: float):
        """Record memory usage."""
        self.memory_usage.append(usage)

    def get_summary(self) -> dict:
        """Get summary statistics."""
        total_time = time.time() - self.start_time
        total_ops = self.success_count + self.error_count
        
        return {
            "total_time": total_time,
            "total_operations": total_ops,
            "operations_per_second": total_ops / total_time if total_time > 0 else 0,
            "success_rate": self.success_count / total_ops if total_ops > 0 else 0,
            "average_operation_time": sum(self.operation_times) / len(self.operation_times) if self.operation_times else 0,
            "max_operation_time": max(self.operation_times) if self.operation_times else 0,
            "average_memory_mb": sum(self.memory_usage) / len(self.memory_usage) if self.memory_usage else 0,
            "peak_memory_mb": max(self.memory_usage) if self.memory_usage else 0
        }

def get_process_memory() -> float:
    """Get current process memory usage in MB."""
    import psutil
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

async def concurrent_optimization(template_name: str, metrics: StressTestMetrics):
    """Run optimization concurrently."""
    start_time = time.time()
    success = True
    
    try:
        tuner = TemplateTuner("tests/stress/tuning")
        target_metrics = {"response_quality": 0.9}
        await asyncio.sleep(0.1)  # Simulate network delay
        optimized = tuner.tune_template(template_name, target_metrics, max_iterations=3)
        metrics.record_memory(get_process_memory())
        
    except Exception as e:
        success = False
        print(f"Error in optimization: {e}")
    
    metrics.record_operation(time.time() - start_time, success)

async def concurrent_learning(template_name: str, metrics: StressTestMetrics):
    """Run learning operations concurrently."""
    start_time = time.time()
    success = True
    
    try:
        learner = TemplateOptimizationLearner("tests/stress/learning")
        generator = MockDataGenerator()
        data = generator.generate_performance_data(template_name, num_samples=5)
        
        for entry in data:
            await asyncio.sleep(0.05)  # Simulate processing time
            learner.add_training_data(template_name, entry["metrics"])
        
        metrics.record_memory(get_process_memory())
        
    except Exception as e:
        success = False
        print(f"Error in learning: {e}")
    
    metrics.record_operation(time.time() - start_time, success)

class StressTest:
    def __init__(self, concurrency: int = 5, duration: int = 30):
        self.concurrency = concurrency
        self.duration = duration
        self.metrics = StressTestMetrics()
        
        # Create test directories
        os.makedirs("tests/stress/tuning", exist_ok=True)
        os.makedirs("tests/stress/learning", exist_ok=True)

    async def run_concurrent_operations(self):
        """Run concurrent operations for stress testing."""
        start_time = time.time()
        template_names = list(MOCK_TEMPLATES.keys())
        
        while time.time() - start_time < self.duration:
            tasks = []
            for _ in range(self.concurrency):
                for template in template_names:
                    tasks.append(concurrent_optimization(template, self.metrics))
                    tasks.append(concurrent_learning(template, self.metrics))
            
            await asyncio.gather(*tasks)
    
    def cleanup(self):
        """Clean up test directories."""
        import shutil
        shutil.rmtree("tests/stress", ignore_errors=True)

@pytest.mark.stress
def test_concurrent_operations():
    """Test system under concurrent load."""
    stress_test = StressTest(concurrency=5, duration=30)
    
    try:
        asyncio.run(stress_test.run_concurrent_operations())
        summary = stress_test.metrics.get_summary()
        
        # Assert performance metrics
        assert summary["success_rate"] > 0.95, "Success rate below 95%"
        assert summary["operations_per_second"] > 1.0, "Performance below 1 op/sec"
        assert summary["average_operation_time"] < 5.0, "Operations too slow"
        assert summary["peak_memory_mb"] < 1000, "Memory usage too high"
        
    finally:
        stress_test.cleanup()

@pytest.mark.stress
def test_memory_stability():
    """Test memory stability under load."""
    initial_memory = get_process_memory()
    stress_test = StressTest(concurrency=3, duration=20)
    
    try:
        asyncio.run(stress_test.run_concurrent_operations())
        final_memory = get_process_memory()
        
        # Check for memory leaks
        memory_increase = final_memory - initial_memory
        assert memory_increase < 100, f"Potential memory leak: {memory_increase:.2f}MB increase"
        
    finally:
        stress_test.cleanup()

@pytest.mark.stress
def test_error_recovery():
    """Test system recovery from errors under stress."""
    stress_test = StressTest(concurrency=5, duration=20)
    
    try:
        # Inject some invalid data
        invalid_template = {"invalid": "data"}
        ProfileManager("tests/stress/profiles").create_profile("invalid", invalid_template)
        
        asyncio.run(stress_test.run_concurrent_operations())
        summary = stress_test.metrics.get_summary()
        
        # System should continue operating despite errors
        assert summary["success_rate"] > 0.8, "Poor error recovery"
        assert summary["operations_per_second"] > 0.5, "Poor performance after errors"
        
    finally:
        stress_test.cleanup()

@pytest.mark.stress
def test_long_running_stability():
    """Test system stability over longer period."""
    stress_test = StressTest(concurrency=2, duration=60)
    performance_samples = []
    
    try:
        async def monitor_performance():
            start_time = time.time()
            while time.time() - start_time < stress_test.duration:
                await asyncio.sleep(5)
                metrics = stress_test.metrics.get_summary()
                performance_samples.append(metrics["operations_per_second"])
        
        async def run_test():
            await asyncio.gather(
                stress_test.run_concurrent_operations(),
                monitor_performance()
            )
        
        asyncio.run(run_test())
        
        # Check performance stability
        if len(performance_samples) >= 2:
            variance = sum((x - sum(performance_samples)/len(performance_samples))**2 
                         for x in performance_samples) / len(performance_samples)
            assert variance < 1.0, "High performance variance over time"
        
    finally:
        stress_test.cleanup()

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--runslow"])
