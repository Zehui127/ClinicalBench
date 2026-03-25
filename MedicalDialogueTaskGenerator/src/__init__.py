"""
医学对话任务生成器包初始化
Medical Dialogue Task Generator

A reusable generator for creating medical dialogue evaluation tasks.
"""

__version__ = "0.1.0"
__author__ = "Medical Dialogue Task Generator Team"

from .core.task_generator import TaskGenerator
from .models.data_models import RawDialogueData, MedicalDialogueTask
from .utils.validator import TaskValidator

__all__ = [
    "TaskGenerator",
    "RawDialogueData",
    "MedicalDialogueTask",
    "TaskValidator",
]
