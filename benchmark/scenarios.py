"""Test scenarios for benchmarking the AI system."""

SCENARIOS = [
    {
        "name": "basic_conversation",
        "description": "Test basic conversation abilities and memory retention",
        "iterations": 5,
        "expected_actions": ["ask_user", "send_message"],
        "success_criteria": {
            "min_context_usage": 0.7,  # Should use context in 70% of responses
            "max_repetition_rate": 0.2,  # Should not repeat more than 20% of questions
            "min_memory_recall": 0.8,  # Should recall 80% of important information
        }
    },
    {
        "name": "web_research",
        "description": "Test web search and information synthesis",
        "iterations": 3,
        "expected_actions": ["web_search", "send_message"],
        "success_criteria": {
            "min_search_quality": 0.7,  # Search queries should be 70% relevant
            "min_synthesis_quality": 0.8,  # Should synthesize information well
            "max_redundant_searches": 0.3,  # No more than 30% redundant searches
        }
    },
    {
        "name": "complex_task",
        "description": "Test multi-step task handling and decision making",
        "iterations": 4,
        "expected_actions": ["web_search", "ask_user", "send_message"],
        "success_criteria": {
            "min_task_completion": 0.8,  # Should complete 80% of tasks
            "min_decision_quality": 0.7,  # Decisions should be 70% optimal
            "max_unnecessary_actions": 0.2,  # No more than 20% unnecessary actions
        }
    }
]

def get_scenario(name):
    """Get a specific scenario by name."""
    for scenario in SCENARIOS:
        if scenario["name"] == name:
            return scenario
    return None

def list_scenarios():
    """List all available scenarios."""
    return [{"name": s["name"], "description": s["description"]} for s in SCENARIOS]
