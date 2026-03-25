"""
KGGenerator - 医学知识图谱任务生成器
Medical Knowledge Graph Task Generator

一个基于PrimeKG医学知识图谱的对话任务生成系统，
能够自动生成真实、多样、高质量的医学对话任务。
"""

__version__ = "1.0.0"
__author__ = "tau2-bench Team"

from .core.kg_loader import PrimeKGLoader
from .core.random_walk import PrimeKGRandomWalkPipeline, ConsultationTask
from .core.task_generator import KGTaskGenerator
from .utils.tau2_converter import convert_to_tau2_format, batch_convert

__all__ = [
    'PrimeKGLoader',
    'PrimeKGRandomWalkPipeline',
    'ConsultationTask',
    'KGTaskGenerator',
    'convert_to_tau2_format',
    'batch_convert'
]
