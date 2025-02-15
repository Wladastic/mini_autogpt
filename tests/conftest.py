"""Pytest configuration for benchmark tests."""

import os
import shutil
import pytest
from typing import List
from _pytest.nodes import Item

# Test directories
TEST_DIRS = [
    "tests/profiles",
    "tests/learning_data",
    "tests/tuning",
    "tests/results",
    "tests/reports"
]

def pytest_sessionstart(session):
    """Set up test environment."""
    # Create test directories
    for directory in TEST_DIRS:
        os.makedirs(directory, exist_ok=True)
        
    # Create empty __init__.py files
    for directory in TEST_DIRS:
        init_file = os.path.join(directory, "__init__.py")
        if not os.path.exists(init_file):
            open(init_file, "w").close()

def pytest_sessionfinish(session, exitstatus):
    """Clean up test environment."""
    # Clean up test directories
    for directory in TEST_DIRS:
        if os.path.exists(directory):
            shutil.rmtree(directory)

def pytest_collection_modifyitems(session: pytest.Session, config: pytest.Config, items: List[Item]):
    """Modify test collection."""
    # Mark slow tests
    for item in items:
        if "template_tuning" in item.nodeid or "template_learning" in item.nodeid:
            item.add_marker(pytest.mark.slow)

def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--runslow",
        action="store_true",
        default=False,
        help="run slow tests"
    )

def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow to run"
    )

def pytest_runtest_setup(item):
    """Set up individual test."""
    if "slow" in item.keywords and not item.config.getoption("--runslow"):
        pytest.skip("need --runslow option to run")
