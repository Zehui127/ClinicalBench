"""
Environment Setup for PrimeKG Domain
Medical consultation tasks generated from Harvard Medical School PrimeKG knowledge graph
"""

from pathlib import Path
from typing import Optional

from tau2.data_model.tasks import Task
from tau2.domains.clinical.user_simulator import ClinicalUserDB, ClinicalUserTools
from tau2.environment.environment import Environment
from tau2.environment.toolkit import ToolKitBase
from tau2.utils import DATA_DIR, load_file


# === PATHS ===
DOMAIN_DIR = DATA_DIR / "tau2" / "domains" / "clinical" / "primekg"
TASKS_PATH = DOMAIN_DIR / "tasks.json"
SPLIT_PATH = DOMAIN_DIR / "split_tasks.json"
POLICY_PATH = DOMAIN_DIR / "policy.md"


class PrimeKGTools(ToolKitBase):
    """ToolKit for PrimeKG domain - no specific tools needed for medical consultation"""

    pass


def get_default_policy() -> str:
    """Get default policy for PrimeKG domain"""
    return """# PrimeKG Medical Consultation Policy

You are a medical consultation AI assistant. Your role is to:

1. **Gather Information**: Ask relevant questions about the patient's symptoms, duration, and severity
2. **Provide Medical Advice**: Based on the symptoms, provide accurate medical guidance
3. **Consider PrimeKG Knowledge**: Use your knowledge of medical conditions, diseases, and treatments
4. **Safety First**: Always consider patient safety and recommend appropriate follow-up care
5. **Clear Communication**: Explain medical concepts in an accessible way

## Guidelines:
- Be empathetic and professional
- Ask clarifying questions when needed
- Provide evidence-based medical information
- Recommend appropriate diagnostic steps when relevant
- Consider drug contraindications and interactions
- Refer to specialists when appropriate

## Important Notes:
- These tasks are generated from the PrimeKG knowledge graph (Harvard Medical School)
- All medical knowledge is based on real clinical data
- Tasks cover various medical specialties and conditions
"""


def get_environment(solo_mode: bool = False) -> Environment:
    """
    Create and configure the PrimeKG domain environment.

    Args:
        solo_mode: Whether to run in solo mode (agent handles user interactions)

    Returns:
        Configured Environment instance
    """
    # Create user tools for patient information
    user_db = ClinicalUserDB()
    user_tools = ClinicalUserTools(user_db)

    # Create tools (empty toolkit for PrimeKG - no specific tools needed)
    tools = PrimeKGTools()

    # Load policy
    try:
        with open(POLICY_PATH, "r") as fp:
            policy = fp.read()
    except Exception:
        policy = get_default_policy()

    # Create environment
    env = Environment(
        domain_name="primekg",
        policy=policy,
        tools=tools,
        user_tools=user_tools,
        solo_mode=solo_mode,
    )

    return env


def get_tasks(task_split_name: Optional[str] = None) -> list[Task]:
    """
    Load PrimeKG domain tasks.

    Args:
        task_split_name: Optional task split name (e.g., "train", "test")

    Returns:
        List of Task objects
    """
    import json

    # Load all tasks with explicit UTF-8 encoding
    with open(TASKS_PATH, 'r', encoding='utf-8') as f:
        tasks_data = json.load(f)

    all_tasks = [Task(**task) for task in tasks_data]

    # If no split specified, return all tasks
    if task_split_name is None:
        return all_tasks

    # Load split and filter
    with open(SPLIT_PATH, 'r', encoding='utf-8') as f:
        split_data = json.load(f)

    if task_split_name not in ["train", "test"]:
        raise ValueError(f"Invalid split name: {task_split_name}. Must be 'train' or 'test'")

    task_ids = split_data[task_split_name]
    filtered_tasks = [t for t in all_tasks if t.id in task_ids]

    return filtered_tasks


def get_tasks_split() -> dict[str, list[str]]:
    """
    Get the train/test split for PrimeKG tasks.

    Returns:
        Dictionary with 'train' and 'test' keys containing lists of task IDs
    """
    import json

    with open(SPLIT_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)
