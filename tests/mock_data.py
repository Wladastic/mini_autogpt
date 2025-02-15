"""Mock data generators for benchmark testing."""

import random
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

import numpy as np

# Test template variations
MOCK_TEMPLATES = {
    "fast": {
        "system": {
            "debug": True,
            "log_level": "DEBUG",
            "timestamp_format": "%Y%m%d_%H%M%S",
            "max_retries": 1,
            "retry_delay": 1
        },
        "metrics": {
            "response_quality": {
                "enabled": True,
                "weight": 1.0,
                "threshold": 0.6
            }
        },
        "analysis": {
            "statistical_significance": 0.1,
            "min_samples": 3,
            "outlier_threshold": 3.0
        }
    },
    "thorough": {
        "system": {
            "debug": True,
            "log_level": "DEBUG",
            "timestamp_format": "%Y%m%d_%H%M%S",
            "max_retries": 3,
            "retry_delay": 5
        },
        "metrics": {
            "response_quality": {
                "enabled": True,
                "weight": 1.0,
                "threshold": 0.8
            },
            "context_usage": {
                "enabled": True,
                "weight": 1.0,
                "threshold": 0.7
            }
        },
        "analysis": {
            "statistical_significance": 0.05,
            "min_samples": 5,
            "outlier_threshold": 2.0
        }
    }
}

class MockDataGenerator:
    def __init__(self, output_dir: str = "tests/mock_data"):
        """Initialize mock data generator."""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_performance_data(self, template_name: str, num_samples: int = 10) -> List[Dict[str, Any]]:
        """Generate mock performance data for a template."""
        template = MOCK_TEMPLATES.get(template_name, MOCK_TEMPLATES["fast"])
        data = []
        
        base_time = datetime.now()
        for i in range(num_samples):
            timestamp = base_time + timedelta(minutes=i*5)
            
            sample = {
                "timestamp": timestamp.isoformat(),
                "template": template_name,
                "duration": random.uniform(1.0, 10.0),
                "metrics": {}
            }
            
            # Generate metric values with some noise
            for metric, config in template["metrics"].items():
                if config["enabled"]:
                    baseline = config["threshold"]
                    noise = random.uniform(-0.1, 0.1)
                    value = max(0.0, min(1.0, baseline + noise))
                    sample["metrics"][metric] = value
            
            data.append(sample)
        
        return data

    def generate_debug_logs(self, template_name: str, num_logs: int = 20) -> List[Dict[str, Any]]:
        """Generate mock debug logs."""
        logs = []
        base_time = datetime.now()
        
        actions = ["think", "decide", "web_search", "ask_user", "send_message"]
        statuses = ["success", "error"]
        
        for i in range(num_logs):
            timestamp = base_time + timedelta(seconds=i*30)
            action = random.choice(actions)
            status = random.choice(statuses)
            
            log_entry = {
                "timestamp": timestamp.isoformat(),
                "template": template_name,
                "request_type": action,
                "status": status,
                "duration": random.uniform(0.1, 2.0),
                "details": {
                    "action": action,
                    "success": status == "success",
                    "error_message": f"Mock error in {action}" if status == "error" else None
                }
            }
            
            logs.append(log_entry)
        
        return logs

    def generate_optimization_history(self, template_name: str, num_iterations: int = 5) -> List[Dict[str, Any]]:
        """Generate mock optimization history."""
        history = []
        base_time = datetime.now()
        
        initial_metrics = {
            "response_quality": 0.6,
            "context_usage": 0.5
        }
        
        target_metrics = {
            "response_quality": 0.8,
            "context_usage": 0.7
        }
        
        for i in range(num_iterations):
            timestamp = base_time + timedelta(minutes=i*10)
            progress = i / (num_iterations - 1)  # 0 to 1
            
            # Simulate improvement over iterations
            current_metrics = {
                metric: initial + (target - initial) * progress + random.uniform(-0.05, 0.05)
                for (metric, initial), (_, target) in zip(
                    initial_metrics.items(), target_metrics.items()
                )
            }
            
            iteration = {
                "timestamp": timestamp.isoformat(),
                "template_name": template_name,
                "iteration": i,
                "metrics": current_metrics,
                "loss": 1.0 - progress + random.uniform(-0.1, 0.1)
            }
            
            history.append(iteration)
        
        return history

    def save_mock_data(self, template_name: str):
        """Generate and save all mock data for a template."""
        # Generate data
        performance_data = self.generate_performance_data(template_name)
        debug_logs = self.generate_debug_logs(template_name)
        optimization_history = self.generate_optimization_history(template_name)
        
        # Save performance data
        performance_file = os.path.join(
            self.output_dir, f"performance_{template_name}.json"
        )
        with open(performance_file, "w") as f:
            json.dump(performance_data, f, indent=2)
        
        # Save debug logs
        logs_file = os.path.join(self.output_dir, f"debug_logs_{template_name}.json")
        with open(logs_file, "w") as f:
            json.dump(debug_logs, f, indent=2)
        
        # Save optimization history
        history_file = os.path.join(
            self.output_dir, f"optimization_{template_name}.json"
        )
        with open(history_file, "w") as f:
            json.dump(optimization_history, f, indent=2)
        
        return {
            "performance": performance_file,
            "logs": logs_file,
            "optimization": history_file
        }

def generate_test_data():
    """Generate test data for all mock templates."""
    generator = MockDataGenerator()
    data_files = {}
    
    for template_name in MOCK_TEMPLATES:
        data_files[template_name] = generator.save_mock_data(template_name)
    
    return data_files

if __name__ == "__main__":
    files = generate_test_data()
    print("Generated mock data files:")
    for template, files in files.items():
        print(f"\n{template}:")
        for data_type, file_path in files.items():
            print(f"  {data_type}: {file_path}")
