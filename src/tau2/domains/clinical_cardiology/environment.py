"""Environment Setup for Clinical Cardiology Domain"""

from pathlib import Path
from typing import Optional

from tau2.data_model.tasks import Task
from tau2.domains.clinical_cardiology.data_model import CardiologyDB
from tau2.domains.clinical_cardiology.tools import CardiologyTools
from tau2.domains.clinical_cardiology.utils import DB_PATH, POLICY_PATH, TASKS_PATH
from tau2.environment.environment import Environment
from tau2.utils import load_file


def get_environment(db: Optional[CardiologyDB] = None) -> Environment:
    """Create cardiology domain environment"""
    if db is None:
        try:
            db = CardiologyDB.load(str(DB_PATH))
        except Exception:
            db = CardiologyDB()
    tools = CardiologyTools(db)
    try:
        with open(POLICY_PATH, "r") as fp:
            policy = fp.read()
    except Exception:
        policy = _get_default_policy()
    return Environment(domain_name="clinical_cardiology", policy=policy, tools=tools)


def get_tasks(task_split_name: Optional[str] = None) -> list[Task]:
    """Load cardiology tasks"""
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
    """Default cardiology policy"""
    return """# Clinical Cardiology Domain Policy

## Overview
This domain specializes in heart and cardiovascular system tasks.

## Clinical Guidelines
- Assess blood pressure using ACC/AHA guidelines
- Calculate QTc using Bazett's formula
- Interpret heart rate based on age-specific norms
- Evaluate cardiac symptoms and risk factors

## Available Tools
- assess_blood_pressure: Classify blood pressure
- calculate_qtc: Calculate corrected QT interval
- interpret_heart_rate: Assess heart rate
- get_patient_by_mrn: Find patients
"""
