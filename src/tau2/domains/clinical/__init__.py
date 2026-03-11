"""Clinical domains for tau2 benchmarking.

This package contains all clinical specialty domains for medical
consultation task evaluation.

Available Domains:
- cardiology: Cardiovascular medicine and heart conditions
- endocrinology: Hormonal and metabolic disorders
- gastroenterology: Digestive system and GI tract
- nephrology: Kidney diseases and renal function
- neurology: Nervous system and neurological conditions

Example:
    from tau2.domains.clinical.cardiology.environment import get_environment
    from tau2.domains.clinical.neurology.environment import get_tasks

    env = get_environment()
    tasks = get_tasks()
"""

# This package is a namespace container for clinical domains
# Individual domains should be imported directly:
# from tau2.domains.clinical.cardiology import ...
# from tau2.domains.clinical.neurology import ...
# etc.

__all__ = [
    "cardiology",
    "endocrinology",
    "gastroenterology",
    "nephrology",
    "neurology",
]
