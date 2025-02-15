"""Test runner with mock data for verifying benchmark system."""

import asyncio
import json
import os
from datetime import datetime, timedelta

from utils.log import log

MOCK_ACTIONS = [
    "think", "decide", "user_interaction", "web_search",
    "llm_request", "evaluate", "send_message"
]

MOCK_RESPONSES = {
    "think": {
        "success": "I have analyzed the situation and determined the next steps.",
        "error": "Error in thinking process: context overload"
    },
    "decide": {
        "success": "Based on analysis, we should proceed with web search.",
        "error": "Unable to make decision: insufficient context"
    },
    "web_search": {
        "success": "Found relevant information about the topic.",
        "error": "Search failed: network error"
    }
}

class MockDataGenerator:
    def __init__(self, output_dir="benchmark/mock_data"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_mock_log(self, request_type, success_rate=0.8):
        """Generate a mock debug log entry."""
        timestamp = datetime.now()
        success = True if random.random() < success_rate else False

        log_entry = {
            "timestamp": timestamp.isoformat(),
            "request_type": request_type,
            "request": {
                "type": request_type,
                "timestamp": timestamp.isoformat()
            },
            "response": {
                "status": "success" if success else "error",
                "message": MOCK_RESPONSES.get(request_type, {}).get(
                    "success" if success else "error",
                    "Standard response"
                )
            }
        }

        return log_entry

    def generate_mock_scenario_run(self, scenario_name, model_id, num_actions=10):
        """Generate a complete mock scenario run."""
        start_time = datetime.now()
        logs = []

        for _ in range(num_actions):
            action = random.choice(MOCK_ACTIONS)
            log_entry = self.generate_mock_log(action)
            logs.append(log_entry)

        duration = (datetime.now() - start_time).total_seconds()

        result = {
            "model": model_id,
            "scenario": scenario_name,
            "timestamp": start_time.isoformat(),
            "duration": duration,
            "iterations_completed": num_actions,
            "debug_logs": logs,
            "metrics": self.generate_mock_metrics(),
            "scenario_config": {
                "name": scenario_name,
                "iterations": num_actions
            }
        }

        return result

    def generate_mock_metrics(self):
        """Generate mock metrics for a scenario run."""
        return {
            "response_quality": random.uniform(0.6, 1.0),
            "context_usage": random.uniform(0.5, 1.0),
            "memory_retention": random.uniform(0.7, 1.0),
            "decision_quality": random.uniform(0.6, 1.0),
            "action_distribution": {
                action: random.uniform(0.1, 0.3)
                for action in MOCK_ACTIONS
            },
            "error_rate": random.uniform(0.0, 0.2),
            "completion_rate": random.uniform(0.7, 1.0)
        }

    def save_mock_data(self, result):
        """Save mock benchmark result."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/mock_result_{result['model']}_{result['scenario']}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)
        
        log(f"Mock data saved to {filename}")
        return filename

async def generate_test_dataset():
    """Generate a complete test dataset with multiple scenarios and models."""
    generator = MockDataGenerator()
    
    models = ["mock_model_1", "mock_model_2", "mock_model_3"]
    scenarios = ["basic_conversation", "web_research", "complex_task"]
    
    results = []
    
    for model in models:
        for scenario in scenarios:
            log(f"Generating mock data for {model} - {scenario}")
            result = generator.generate_mock_scenario_run(scenario, model)
            file = generator.save_mock_data(result)
            results.append({"model": model, "scenario": scenario, "file": file})
    
    return results

def verify_mock_data(results):
    """Verify the generated mock data for testing."""
    issues = []
    
    for result in results:
        try:
            with open(result["file"], 'r') as f:
                data = json.load(f)
                
            # Verify required fields
            required_fields = [
                "model", "scenario", "timestamp", "duration",
                "debug_logs", "metrics"
            ]
            
            for field in required_fields:
                if field not in data:
                    issues.append(f"Missing field {field} in {result['file']}")
            
            # Verify metrics
            if "metrics" in data:
                if not isinstance(data["metrics"], dict):
                    issues.append(f"Invalid metrics format in {result['file']}")
                    
            # Verify debug logs
            if "debug_logs" in data:
                if not isinstance(data["debug_logs"], list):
                    issues.append(f"Invalid debug_logs format in {result['file']}")
                
        except Exception as e:
            issues.append(f"Error verifying {result['file']}: {str(e)}")
    
    return issues

async def main():
    """Generate and verify test dataset."""
    import random
    random.seed(42)  # For reproducible results
    
    log("Generating test dataset...")
    results = await generate_test_dataset()
    
    log("Verifying mock data...")
    issues = verify_mock_data(results)
    
    if issues:
        log("Issues found in mock data:")
        for issue in issues:
            log(f"- {issue}")
    else:
        log("Mock data verification successful!")

if __name__ == "__main__":
    import random  # For generating mock data
    asyncio.run(main())
