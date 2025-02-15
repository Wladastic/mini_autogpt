"""Benchmark runner for testing different models and scenarios."""

import asyncio
import json
import os
import time
from datetime import datetime
import requests

from dotenv import load_dotenv
import think.memory as memory
from utils.log import log, save_debug
from benchmark.scenarios import get_scenario, list_scenarios
import utils.llm as llm
import main as mini_autogpt

class BenchmarkRunner:
    def __init__(self, output_dir="benchmark/results"):
        """Initialize the benchmark runner."""
        self.output_dir = output_dir
        self.models = []
        self.results = {}
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs("benchmark/logs", exist_ok=True)
        load_dotenv()
    
    async def load_models(self):
        """Get available models from LMStudio."""
        try:
            api_url = os.getenv("API_URL", "").strip()
            base_url = llm.get_base_url(api_url, "lmstudio")
            models_url = f"{base_url}/models"
            log(f"Fetching models from {models_url}")
            
            response = requests.get(models_url)
            if response.status_code == 200:
                self.models = response.json().get("data", [])
                log(f"Found {len(self.models)} models")
                return self.models
            else:
                log(f"Error fetching models: {response.status_code}")
                return []
        except Exception as e:
            log(f"Error loading models: {e}")
            return []

    async def run_scenario(self, model, scenario_name):
        """Run a single test scenario for a model."""
        scenario = get_scenario(scenario_name)
        if not scenario:
            log(f"Scenario {scenario_name} not found")
            return None

        log(f"\n=== Running scenario '{scenario_name}' with model '{model}' ===")
        
        # Configure environment for this run
        os.environ["LMSTUDIO_MODEL"] = model
        os.environ["BENCHMARK_MODE"] = "true"
        os.environ["BENCHMARK_SCENARIO"] = scenario_name
        os.environ["BENCHMARK_ITERATIONS"] = str(scenario["iterations"])
        
        start_time = time.time()
        debug_logs = []
        
        try:
            # Clear memory for fresh start
            memory.forget_everything()
            
            # Create scenario-specific log directory
            log_dir = f"benchmark/logs/{model}/{scenario_name}"
            os.makedirs(log_dir, exist_ok=True)
            os.environ["DEBUG_LOG_DIR"] = log_dir
            
            # Run the mini-autogpt main loop for specified iterations
            for i in range(scenario["iterations"]):
                log(f"\nIteration {i+1}/{scenario['iterations']}")
                mini_autogpt.run_think()
                
                # Collect logs from this iteration
                debug_logs.extend(self.collect_iteration_logs(log_dir))
                
                # Brief pause between iterations
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            log("\nBenchmark interrupted by user")
            return None
        except Exception as e:
            log(f"Error running scenario: {e}")
            return None
        finally:
            # Reset environment
            os.environ.pop("BENCHMARK_MODE", None)
            os.environ.pop("BENCHMARK_SCENARIO", None)
            os.environ.pop("BENCHMARK_ITERATIONS", None)
            os.environ.pop("DEBUG_LOG_DIR", None)
        
        duration = time.time() - start_time
        
        # Create result entry
        result = {
            "model": model,
            "scenario": scenario_name,
            "timestamp": datetime.now().isoformat(),
            "duration": duration,
            "iterations_completed": len(debug_logs),
            "debug_logs": debug_logs,
            "metrics": await self.calculate_metrics(debug_logs, scenario),
            "scenario_config": scenario
        }

        # Save result
        self.save_result(result)
        return result

    def collect_iteration_logs(self, log_dir):
        """Collect debug logs from an iteration."""
        logs = []
        try:
            for file in os.listdir(log_dir):
                if file.endswith(".json"):
                    with open(os.path.join(log_dir, file), 'r') as f:
                        logs.append(json.load(f))
        except Exception as e:
            log(f"Error collecting logs: {e}")
        return logs

    async def calculate_metrics(self, debug_logs, scenario):
        """Calculate performance metrics from debug logs."""
        metrics = {
            "response_quality": 0.0,
            "context_usage": 0.0,
            "memory_retention": 0.0,
            "decision_quality": 0.0,
            "action_distribution": {},
            "error_rate": 0.0,
            "completion_rate": 0.0
        }

        if not debug_logs:
            return metrics

        # Count actions
        total_actions = 0
        action_counts = {}
        errors = 0

        for entry in debug_logs:
            if "request_type" in entry:
                total_actions += 1
                action_counts[entry["request_type"]] = action_counts.get(entry["request_type"], 0) + 1
                
                if "error" in entry.get("response", {}):
                    errors += 1

        # Calculate basic metrics
        if total_actions > 0:
            metrics["error_rate"] = errors / total_actions
            metrics["action_distribution"] = {
                action: count/total_actions 
                for action, count in action_counts.items()
            }
            
            # Check if expected actions were used
            expected_action_usage = sum(
                1 for action in scenario["expected_actions"]
                if action in action_counts
            ) / len(scenario["expected_actions"])
            
            metrics["completion_rate"] = expected_action_usage

        # TODO: Implement more sophisticated metrics based on scenario criteria
        
        return metrics

    def save_result(self, result):
        """Save benchmark result to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/result_{result['model']}_{result['scenario']}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)
        
        log(f"Results saved to {filename}")

    async def run_all(self):
        """Run all scenarios with all available models."""
        models = await self.load_models()
        if not models:
            log("No models available")
            return

        scenarios = list_scenarios()
        results = []

        for model in models:
            model_id = model["id"]
            log(f"\n=== Testing model: {model_id} ===")
            
            for scenario in scenarios:
                result = await self.run_scenario(model_id, scenario["name"])
                if result:
                    results.append(result)

        return results

async def main():
    """Run the benchmark system."""
    log("\n=== Starting Benchmark System ===")
    runner = BenchmarkRunner()
    results = await runner.run_all()
    log("\n=== Benchmark Complete ===")
    return results

if __name__ == "__main__":
    asyncio.run(main())
