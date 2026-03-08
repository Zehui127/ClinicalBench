"""
Environment Setup for Clinical Gastroenterology Domain
"""

from pathlib import Path
from typing import Optional

from tau2.data_model.tasks import Task
from tau2.domains.clinical_gastroenterology.data_model import GastroenterologyDB
from tau2.domains.clinical_gastroenterology.tools import GastroenterologyTools
from tau2.domains.clinical_gastroenterology.utils import (
    DB_PATH,
    POLICY_PATH,
    TASKS_PATH,
)
from tau2.environment.environment import Environment
from tau2.utils import load_file


def get_environment(db: Optional[GastroenterologyDB] = None) -> Environment:
    """Create the gastroenterology domain environment"""
    if db is None:
        try:
            db = GastroenterologyDB.load(str(DB_PATH))
        except Exception:
            db = GastroenterologyDB()

    tools = GastroenterologyTools(db)

    try:
        with open(POLICY_PATH, "r") as fp:
            policy = fp.read()
    except Exception:
        policy = _get_default_policy()

    env = Environment(
        domain_name="clinical_gastroenterology",
        policy=policy,
        tools=tools,
    )

    return env


def get_tasks(task_split_name: Optional[str] = None) -> list[Task]:
    """Load gastroenterology domain tasks"""
    tasks = load_file(TASKS_PATH)
    tasks = [Task.model_validate(task) for task in tasks]

    if task_split_name is None:
        return tasks

    task_splits = get_tasks_split()
    if task_split_name not in task_splits:
        raise ValueError(f"Invalid task split: {task_split_name}")
    return [task for task in tasks if task.id in task_splits[task_split_name]]


def get_tasks_split() -> dict[str, list[str]]:
    """Load task splits"""
    split_file = Path(TASKS_PATH).parent / f"split_{Path(TASKS_PATH).stem}.json"
    return load_file(split_file)


def _get_default_policy() -> str:
    """Default gastroenterology policy"""
    return """# Clinical Gastroenterology Domain Policy

## Overview
This domain specializes in digestive system and GI tract tasks.

## Clinical Guidelines
- Evaluate liver function tests (ALT, AST, bilirubin)
- Use APRI score for liver fibrosis assessment
- Assess anemia with gender-specific thresholds
- Screen for GI conditions based on symptoms

## Available Tools
- get_patient_liver_function: Retrieve liver function tests
- evaluate_anemia: Assess anemia severity
- assess_liver_fibrosis: Calculate APRI score
- get_patient_by_mrn: Find patients by MRN
"""
