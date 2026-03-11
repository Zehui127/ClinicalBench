"""Utility functions for Clinical Neurology Domain"""

from pathlib import Path

DOMAIN_NAME = "clinical_neurology"
DATA_DIR = Path(__file__).parent.parent.parent.parent.parent / "data" / "tau2" / "domains" / "clinical" / "neurology"

TASKS_PATH = DATA_DIR / "tasks.json"
SPLIT_TASKS_PATH = DATA_DIR / "split_tasks.json"
POLICY_PATH = DATA_DIR / "policy.md"
DB_PATH = DATA_DIR / "db.json"

NEURO_KEYWORDS = [
    "brain", "neuro", "seizure", "stroke", "headache", "migraine",
    "neural", "cognitive", "dementia", "parkinson", "multiple sclerosis",
    "concussion", "spinal", "nerve", "numbness", "weakness"
]
