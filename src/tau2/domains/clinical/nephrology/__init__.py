"""
Clinical Nephrology Domain for Tau2
Specialized domain for kidney-related clinical tasks including:
- Glomerular Filtration Rate (eGFR) calculations
- Renal function assessment
- Nephrology consultations
- Kidney disease management
"""

from tau2.domains.clinical.nephrology.environment import (
    get_environment,
    get_tasks,
    get_tasks_split,
)

__all__ = ["get_environment", "get_tasks", "get_tasks_split"]
