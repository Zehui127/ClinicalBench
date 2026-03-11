"""
Utility functions for Clinical Gastroenterology Domain
"""

from pathlib import Path

DOMAIN_NAME = "clinical_gastroenterology"
DATA_DIR = Path(__file__).parent.parent.parent.parent.parent / "data" / "tau2" / "domains" / "clinical" / "gastroenterology"

TASKS_PATH = DATA_DIR / "tasks.json"
SPLIT_TASKS_PATH = DATA_DIR / "split_tasks.json"
POLICY_PATH = DATA_DIR / "policy.md"
DB_PATH = DATA_DIR / "db.json"

GASTRO_KEYWORDS = [
    "gi", "gastro", "stomach", "digestive", "liver", "hepat",
    "pancreatit", "colon", "diarrhea", "constipat", "endoscop",
    "egd", "colonoscop", "cirrhos", "hepatit", "bilrubin"
]
