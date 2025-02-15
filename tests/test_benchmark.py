"""Test suite for the benchmark system."""

import os
import json
from datetime import datetime
import pytest
import numpy as np

from benchmark.config import BenchmarkConfig, DEFAULT_CONFIG
from benchmark.templates import get_template, TEMPLATES
from benchmark.validation import validate_and_update_config
from benchmark.profiles import ProfileManager
from benchmark.learning import TemplateOptimizationLearner
from benchmark.auto_tuning import TemplateTuner

# Test data
TEST_TEMPLATE = {
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
            "threshold": 0.7
        }
    },
    "analysis": {
        "statistical_significance": 0.05,
        "min_samples": 5,
        "outlier_threshold": 2.0
    }
}

@pytest.fixture
def config():
    """Create a test configuration."""
    return BenchmarkConfig("tests/test_config.json")

@pytest.fixture
def profile_manager():
    """Create a test profile manager."""
    return ProfileManager("tests/profiles")

@pytest.fixture
def template_learner():
    """Create a test template learner."""
    return TemplateOptimizationLearner("tests/learning_data")

@pytest.fixture
def template_tuner():
    """Create a test template tuner."""
    return TemplateTuner("tests/tuning")

def test_config_validation():
    """Test configuration validation."""
    # Test valid configuration
    validated, errors = validate_and_update_config(DEFAULT_CONFIG)
    assert errors == [], "Default config should be valid"
    
    # Test invalid configuration
    invalid_config = DEFAULT_CONFIG.copy()
    invalid_config["system"]["max_retries"] = -1
    with pytest.raises(Exception):
        validate_and_update_config(invalid_config)

def test_config_loading(config):
    """Test configuration loading and saving."""
    # Test loading default config
    assert config.config is not None
    assert "system" in config.config
    
    # Test saving and loading config
    config.save_config(TEST_TEMPLATE)
    loaded = config.load_config()
    assert loaded["system"]["max_retries"] == TEST_TEMPLATE["system"]["max_retries"]

def test_profile_management(profile_manager):
    """Test profile management functionality."""
    # Test creating profile
    profile_name = "test_profile"
    path = profile_manager.create_profile(profile_name, TEST_TEMPLATE)
    assert os.path.exists(path)
    
    # Test loading profile
    loaded = profile_manager.load_profile(profile_name)
    assert loaded["system"]["max_retries"] == TEST_TEMPLATE["system"]["max_retries"]
    
    # Test deleting profile
    profile_manager.delete_profile(profile_name)
    with pytest.raises(FileNotFoundError):
        profile_manager.load_profile(profile_name)

def test_template_features(template_learner):
    """Test template feature extraction."""
    features = template_learner._extract_features(TEST_TEMPLATE)
    assert "max_retries" in features
    assert features["max_retries"] == TEST_TEMPLATE["system"]["max_retries"]

def test_template_learning(template_learner):
    """Test template learning functionality."""
    # Add test data
    template_learner.add_training_data("test", {
        "response_quality": 0.8,
        "context_usage": 0.7
    })
    
    # Test prediction
    predictions = template_learner.predict_performance(TEST_TEMPLATE)
    assert "response_quality" in predictions
    assert 0 <= predictions["response_quality"] <= 1

def test_template_tuning(template_tuner):
    """Test template tuning functionality."""
    # Test tuning with target metrics
    targets = {"response_quality": 0.9}
    optimized = template_tuner.tune_template("test", targets, max_iterations=10)
    
    assert optimized is not None
    assert "metrics" in optimized
    assert "response_quality" in optimized["metrics"]

def test_parameter_bounds(template_tuner):
    """Test parameter bounds validation."""
    bounds = template_tuner.parameter_bounds
    
    for param, bound in bounds.items():
        assert bound.min_value <= bound.max_value
        assert bound.step > 0

def test_optimization_history(template_tuner):
    """Test optimization history tracking."""
    template_name = "test"
    targets = {"response_quality": 0.9}
    
    # Run tuning
    template_tuner.tune_template(template_name, targets, max_iterations=10)
    
    # Check history
    assert len(template_tuner.optimization_history) > 0
    last_entry = template_tuner.optimization_history[-1]
    assert last_entry["template_name"] == template_name
    assert "target_metrics" in last_entry
    assert "initial_performance" in last_entry
    assert "final_performance" in last_entry

def test_report_generation(template_tuner):
    """Test report generation functionality."""
    template_name = "test"
    report = template_tuner.generate_tuning_report(
        template_name,
        TEST_TEMPLATE,
        TEST_TEMPLATE  # Use same template for simplicity
    )
    
    assert os.path.exists(report)
    with open(report, "r") as f:
        content = f.read()
        assert template_name in content
        assert "Performance Comparison" in content

def test_edge_cases():
    """Test edge cases and error handling."""
    # Test empty template
    empty_template = {}
    with pytest.raises(Exception):
        validate_and_update_config(empty_template)
    
    # Test missing required fields
    invalid_template = {"system": {}}
    with pytest.raises(Exception):
        validate_and_update_config(invalid_template)
    
    # Test invalid metric values
    invalid_metrics = TEST_TEMPLATE.copy()
    invalid_metrics["metrics"]["response_quality"]["threshold"] = 2.0
    with pytest.raises(Exception):
        validate_and_update_config(invalid_metrics)

@pytest.mark.parametrize("template_name", TEMPLATES.keys())
def test_default_templates(template_name):
    """Test all default templates."""
    template = get_template(template_name)
    validated, errors = validate_and_update_config(template)
    assert errors == [], f"Template {template_name} should be valid"

if __name__ == "__main__":
    pytest.main([__file__])
