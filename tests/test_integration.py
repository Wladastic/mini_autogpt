"""Integration tests for the benchmark system."""

import os
import json
import pytest
from datetime import datetime

from benchmark.config import BenchmarkConfig
from benchmark.profiles import ProfileManager
from benchmark.templates import get_template
from benchmark.learning import TemplateOptimizationLearner
from benchmark.auto_tuning import TemplateTuner
from benchmark.visualizer import BenchmarkVisualizer
from tests.mock_data import MockDataGenerator, MOCK_TEMPLATES

@pytest.fixture(scope="module")
def test_env():
    """Set up test environment with mock data."""
    # Create directories
    dirs = ["tests/integration/results", "tests/integration/profiles"]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    
    # Generate mock data
    generator = MockDataGenerator("tests/integration/mock_data")
    data = {}
    for template_name in MOCK_TEMPLATES:
        data[template_name] = generator.save_mock_data(template_name)
    
    yield {
        "data": data,
        "config": BenchmarkConfig("tests/integration/config.json"),
        "profile_manager": ProfileManager("tests/integration/profiles"),
        "learner": TemplateOptimizationLearner("tests/integration/learning"),
        "tuner": TemplateTuner("tests/integration/tuning"),
        "visualizer": BenchmarkVisualizer("tests/integration/visualizations")
    }
    
    # Cleanup
    for d in dirs:
        if os.path.exists(d):
            import shutil
            shutil.rmtree(d)

@pytest.mark.integration
def test_full_optimization_workflow(test_env):
    """Test complete workflow from template creation to optimization."""
    # 1. Create and save profile
    profile_name = "integration_test"
    template = MOCK_TEMPLATES["thorough"]
    profile_path = test_env["profile_manager"].create_profile(profile_name, template)
    assert os.path.exists(profile_path)
    
    # 2. Load and validate profile
    loaded_profile = test_env["profile_manager"].load_profile(profile_name)
    assert loaded_profile["metrics"]["response_quality"]["threshold"] == \
           template["metrics"]["response_quality"]["threshold"]
    
    # 3. Train learning model
    for template_name, files in test_env["data"].items():
        # Load performance data
        with open(files["performance"], 'r') as f:
            performance_data = json.load(f)
        
        # Add training data
        for entry in performance_data:
            test_env["learner"].add_training_data(template_name, entry["metrics"])
    
    # 4. Run optimization
    target_metrics = {
        "response_quality": 0.9,
        "context_usage": 0.8
    }
    optimized = test_env["tuner"].tune_template(profile_name, target_metrics, max_iterations=5)
    assert optimized is not None
    assert "metrics" in optimized
    
    # 5. Generate visualization
    test_env["visualizer"].generate_visualization_report()
    assert os.path.exists(test_env["visualizer"].output_dir)

@pytest.mark.integration
def test_performance_analysis_workflow(test_env):
    """Test performance analysis workflow."""
    # 1. Load mock performance data
    template_name = "thorough"
    with open(test_env["data"][template_name]["performance"], 'r') as f:
        performance_data = json.load(f)
    
    # 2. Train model and make predictions
    for entry in performance_data:
        test_env["learner"].add_training_data(template_name, entry["metrics"])
    
    template = get_template(template_name)
    predictions = test_env["learner"].predict_performance(template)
    
    assert "response_quality" in predictions
    assert 0 <= predictions["response_quality"] <= 1

@pytest.mark.integration
def test_optimization_stability(test_env):
    """Test stability of optimization process."""
    template_name = "fast"
    target_metrics = {"response_quality": 0.8}
    
    # Run multiple optimizations
    results = []
    for _ in range(3):
        optimized = test_env["tuner"].tune_template(
            template_name,
            target_metrics,
            max_iterations=5
        )
        results.append(
            optimized["metrics"]["response_quality"]["threshold"]
        )
    
    # Check consistency
    mean = sum(results) / len(results)
    variance = sum((x - mean) ** 2 for x in results) / len(results)
    assert variance < 0.1, "Optimization results show high variance"

@pytest.mark.integration
def test_error_handling(test_env):
    """Test error handling in integrated workflow."""
    # 1. Test invalid profile creation
    with pytest.raises(Exception):
        test_env["profile_manager"].create_profile("invalid", {})
    
    # 2. Test invalid optimization targets
    with pytest.raises(Exception):
        test_env["tuner"].tune_template("fast", {"invalid_metric": 1.0})
    
    # 3. Test missing data handling
    profile_name = "missing_data_test"
    test_env["profile_manager"].create_profile(profile_name, MOCK_TEMPLATES["fast"])
    
    # Should handle gracefully with empty training data
    predictions = test_env["learner"].predict_performance(MOCK_TEMPLATES["fast"])
    assert isinstance(predictions, dict)

def test_data_consistency(test_env):
    """Test data consistency across components."""
    template_name = "thorough"
    
    # 1. Create profile
    profile = test_env["profile_manager"].create_profile(
        "consistency_test",
        MOCK_TEMPLATES[template_name]
    )
    
    # 2. Load performance data
    with open(test_env["data"][template_name]["performance"], 'r') as f:
        performance_data = json.load(f)
    
    # 3. Process through components
    for entry in performance_data:
        test_env["learner"].add_training_data(template_name, entry["metrics"])
    
    # 4. Verify predictions match template configuration
    predictions = test_env["learner"].predict_performance(MOCK_TEMPLATES[template_name])
    template_threshold = MOCK_TEMPLATES[template_name]["metrics"]["response_quality"]["threshold"]
    
    assert abs(predictions["response_quality"] - template_threshold) < 0.3

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--runslow"])
