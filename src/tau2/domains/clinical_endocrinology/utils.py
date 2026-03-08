"""Utility functions for Clinical Endocrinology Domain"""

from pathlib import Path

DOMAIN_NAME = "clinical_endocrinology"
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "tau2" / "domains" / DOMAIN_NAME

TASKS_PATH = DATA_DIR / "tasks.json"
SPLIT_TASKS_PATH = DATA_DIR / "split_tasks.json"
POLICY_PATH = DATA_DIR / "policy.md"
DB_PATH = DATA_DIR / "db.json"

ENDO_KEYWORDS = [
    "diabetes", "thyroid", "hormone", "insulin", "glucose",
    "hba1c", "tsh", "t4", "metabolism", "cortisol", "parathyroid"
]
