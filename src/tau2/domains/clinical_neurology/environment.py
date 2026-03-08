"""Environment Setup for Clinical Neurology Domain"""

from pathlib import Path
from typing import Optional

from tau2.data_model.tasks import Task
from tau2.domains.clinical_neurology.data_model import NeurologyDB
from tau2.domains.clinical_neurology.tools import NeurologyTools
from tau2.domains.clinical_neurology.utils import DB_PATH, POLICY_PATH, TASKS_PATH
from tau2.environment.environment import Environment
from tau2.utils import load_file


def get_environment(db: Optional[NeurologyDB] = None) -> Environment:
    """Create neurology domain environment"""
    if db is None:
        try:
            db = NeurologyDB.load(str(DB_PATH))
        except Exception:
            db = NeurologyDB()
    tools = NeurologyTools(db)
    try:
        with open(POLICY_PATH, "r") as fp:
            policy = fp.read()
    except Exception:
        policy = _get_default_policy()
    return Environment(domain_name="clinical_neurology", policy=policy, tools=tools)


def get_tasks(task_split_name: Optional[str] = None) -> list[Task]:
    """Load neurology tasks"""
    tasks = load_file(TASKS_PATH)
    tasks = [Task.model_validate(task) for task in tasks]
    if task_split_name is None:
        return tasks
    task_splits = get_tasks_split()
    if task_split_name not in task_splits:
        raise ValueError(f"Invalid split: {task_split_name}")
    return [task for task in tasks if task.id in task_splits[task_split_name]]


def get_tasks_split() -> dict[str, list[str]]:
    """Load task splits"""
    split_file = Path(TASKS_PATH).parent / f"split_{Path(TASKS_PATH).stem}.json"
    return load_file(split_file)


def _get_default_policy() -> str:
    """Default neurology policy"""
    return """# Clinical Neurology Domain Policy

## Overview
This domain specializes in brain and nervous system tasks.

## Clinical Guidelines
- Assess stroke risk using common risk factors
- Classify headaches by location and characteristics
- Evaluate seizure types and consciousness
- Recommend neurological consultations when appropriate

## Available Tools
- assess_stroke_risk: Basic stroke risk assessment
- interpret_headache: Classify headache types
- evaluate_seizure: Determine seizure classification
- get_patient_by_mrn: Find patients
"""
