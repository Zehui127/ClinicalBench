"""
DataGenerator - 医学对话数据集优化器
Medical Dialogue Dataset Optimizer

一个专业的医学对话数据集优化工具，能够整合多个数据集的优势，
生成高质量、均衡分布、可追溯的优化数据集。
"""

__version__ = "1.0.0"
__author__ = "tau2-bench Team"

from .core.task_optimizer import TaskOptimizer
from .core.scenario_balancer import ScenarioBalancer
from .core.evaluation_enhancer import EvaluationEnhancer
from .core.metadata_builder import MetadataBuilder
from .core.quality_scorer import QualityScorer

__all__ = [
    'TaskOptimizer',
    'ScenarioBalancer',
    'EvaluationEnhancer',
    'MetadataBuilder',
    'QualityScorer'
]
