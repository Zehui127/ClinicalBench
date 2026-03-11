"""
Clinical Gastroenterology Domain for Tau2
Specialized domain for digestive system and GI tract tasks
"""

from tau2.domains.clinical.gastroenterology.environment import (
    get_environment,
    get_tasks,
    get_tasks_split,
)

__all__ = ["get_environment", "get_tasks", "get_tasks_split"]
