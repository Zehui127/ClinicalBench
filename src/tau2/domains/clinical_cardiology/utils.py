"""Utility functions for Clinical Cardiology Domain"""

from pathlib import Path

DOMAIN_NAME = "clinical_cardiology"
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "tau2" / "domains" / DOMAIN_NAME

TASKS_PATH = DATA_DIR / "tasks.json"
SPLIT_TASKS_PATH = DATA_DIR / "split_tasks.json"
POLICY_PATH = DATA_DIR / "policy.md"
DB_PATH = DATA_DIR / "db.json"

CARDIO_KEYWORDS = [
    "heart", "cardiac", "ecg", "ekg", "echo", "chest pain",
    "blood pressure", "hypertension", "arrhythmia", "palpitation",
    "stent", "catheter", "coronary", "myocardial", "infarction"
]
