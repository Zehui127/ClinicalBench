"""
Environment Setup for Clinical Gastroenterology Domain
"""

from pathlib import Path
from typing import Optional

from tau2.data_model.tasks import Task
from tau2.domains.clinical.gastroenterology.tools import GastroenterologyTools
from tau2.domains.clinical.gastroenterology.utils import (
    DB_PATH,
    POLICY_PATH,
    TASKS_PATH,
)
from tau2.environment.environment import Environment
from tau2.utils import load_file



# === DATA MODELS ===
"""Data Models for Clinical Gastroenterology Domain

Defines patient records, GI lab results, and digestive system data
"""

import json
from typing import Dict, List, Optional
from pydantic import BaseModel
from tau2.domains.clinical.user_simulator import ClinicalUserDB, ClinicalUserTools



class GILabResults(BaseModel):
    """Gastrointestinal lab results"""
    liver_enzymes_alt: Optional[float] = None  # U/L
    liver_enzymes_ast: Optional[float] = None  # U/L
    bilirubin: Optional[float] = None  # mg/dL
    albumin: Optional[float] = None  # g/dL
    inr: Optional[float] = None  # International Normalized Ratio
    hemoglobin: Optional[float] = None  # g/dL
    platelets: Optional[float] = None  # K/uL


class EndoscopyRecord(BaseModel):
    """Endoscopy procedure record"""
    procedure_type: str  # colonoscopy, egd, sigmoidoscopy
    date: str
    findings: List[str] = []
    biopsy_taken: bool = False
    pathology_results: Optional[str] = None


class PatientRecord(BaseModel):
    """Patient medical record for gastroenterology"""
    patient_id: str
    name: str
    age: int
    gender: str
    diagnoses: List[str] = []
    gi_lab_results: Optional[GILabResults] = None
    endoscopies: List[EndoscopyRecord] = []
    medications: List[str] = []
    comorbidities: List[str] = []
    chief_complaint: Optional[str] = None


class GastroenterologyDB(BaseModel):
    """Gastroenterology domain database"""
    patients: Dict[str, PatientRecord] = {}
    lab_results: Dict[str, GILabResults] = {}
    procedures: Dict[str, EndoscopyRecord] = {}

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def load(cls, db_path: str) -> "GastroenterologyDB":
        """Load database from JSON file"""
        import json
        from pathlib import Path

        path = Path(db_path)
        if not path.exists():
            return cls()

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return cls(**data)

    def get_patient(self, patient_id: str) -> Optional[PatientRecord]:
        """Get patient by ID"""
        return self.patients.get(patient_id)
def get_environment(db: Optional[GastroenterologyDB] = None, solo_mode: bool = False) -> Environment:
    """Create the gastroenterology domain environment"""
    if db is None:
        try:
            db = GastroenterologyDB.load(str(DB_PATH))
        except Exception:
            db = GastroenterologyDB()

    tools = GastroenterologyTools(db)

    # Create user tools for patient information
    user_db = ClinicalUserDB()
    user_tools = ClinicalUserTools(user_db)

    try:
        with open(POLICY_PATH, "r") as fp:
            policy = fp.read()
    except Exception:
        policy = _get_default_policy()

    env = Environment(
        domain_name="clinical_gastroenterology",
        policy=policy,
        tools=tools,
        user_tools=user_tools,
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