"""
Utility functions and constants for Clinical Nephrology Domain
"""

from pathlib import Path

# Domain data paths
DOMAIN_NAME = "clinical_nephrology"
DATA_DIR = Path(__file__).parent.parent.parent.parent.parent / "data" / "tau2" / "domains" / "clinical" / "nephrology"

# File paths
TASKS_PATH = DATA_DIR / "tasks.json"
SPLIT_TASKS_PATH = DATA_DIR / "split_tasks.json"
POLICY_PATH = DATA_DIR / "policy.md"
DB_PATH = DATA_DIR / "db.json"

# CKD staging reference
CKD_STAGES = {
    1: {"egfr_range": (90, 999), "description": "Normal or increased"},
    2: {"egfr_range": (60, 89), "description": "Mildly decreased"},
    "3a": {"egfr_range": (45, 59), "description": "Mild to moderately decreased"},
    "3b": {"egfr_range": (30, 44), "description": "Moderately to severely decreased"},
    4: {"egfr_range": (15, 29), "description": "Severely decreased"},
    5: {"egfr_range": (0, 14), "description": "Kidney failure"}
}

# Nephrology keywords for task classification
NEPHROLOGY_KEYWORDS = [
    "kidney", "renal", "egfr", "creatinine", "dialysis", "glomerul",
    "nephrit", "proteinuria", "hematuria", "albuminuria", "bun",
    "potassium", "sodium", "electrolyte", "acid-base", "ckd"
]
