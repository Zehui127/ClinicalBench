"""Environment Setup for Clinical Endocrinology Domain"""

from pathlib import Path
from typing import Optional

from tau2.data_model.tasks import Task
from tau2.domains.clinical_endocrinology.data_model import EndocrinologyDB
from tau2.domains.clinical_endocrinology.tools import EndocrinologyTools
from tau2.domains.clinical_endocrinology.utils import DB_PATH, POLICY_PATH, TASKS_PATH
from tau2.environment.environment import Environment
from tau2.utils import load_file


def get_environment(db: Optional[EndocrinologyDB] = None) -> Environment:
    """Create endocrinology domain environment"""
    if db is None:
        try:
            db = EndocrinologyDB.load(str(DB_PATH))
        except Exception:
            db = EndocrinologyDB()
    tools = EndocrinologyTools(db)
    try:
        with open(POLICY_PATH, "r") as fp:
            policy = fp.read()
    except Exception:
        policy = _get_default_policy()
    return Environment(domain_name="clinical_endocrinology", policy=policy, tools=tools)


def get_tasks(task_split_name: Optional[str] = None) -> list[Task]:
    """Load endocrinology tasks"""
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
    """Default endocrinology policy"""
    return """# Clinical Endocrinology Domain Policy

## Overview
This domain specializes in hormone and metabolism-related tasks.

## Clinical Guidelines
- Interpret blood glucose (fasting vs random)
- Classify HbA1c for diabetes assessment
- Evaluate thyroid function (TSH, T4)
- Monitor hormonal imbalances

## Available Tools
- interpret_blood_glucose: Classify glucose levels
- interpret_hba1c: Assess diabetes control
- interpret_thyroid: Evaluate thyroid function
- get_patient_by_mrn: Find patients
"""
