"""
Output Generators for UniClinicalDataEngine
UniClinicalDataEngine 的输出生成器

Generates output files: tasks.json, db.json, tools.json, policy.md
Also provides dialogue generators for converting medical data to consultation format.
"""

from .output_generator import OutputGenerator

# Dialogue generators for consultation data
try:
    from .base_generator import BaseGenerator
    from .mcq_converter import MCQToDialogueConverter
    from .template_manager import TemplateManager

    __all__ = [
        "OutputGenerator",
        "BaseGenerator",
        "MCQToDialogueConverter",
        "TemplateManager",
    ]
except ImportError:
    __all__ = ["OutputGenerator"]
