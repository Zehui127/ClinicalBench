#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrimeKG Random Walk - 兼容性包装器

此脚本保留用于向后兼容，实际功能已迁移到:
medical_task_suite/generation/

推荐使用方式:
    from medical_task_suite.generation import PrimeKGRandomWalkPipeline
"""

import sys
from pathlib import Path

# 添加 medical_task_suite 到路径
sys.path.insert(0, str(Path(__file__).parent / "medical_task_suite"))

# 从 medical_task_suite 导入
from generation.core.random_walk import (
    PrimeKGRandomWalkPipeline,
    PrimeKGTaskGenerator,
    ConsultationTask,
    WalkPath,
    PrimeKGAdapter
)

# 导出与原脚本相同的接口
__all__ = [
    'PrimeKGRandomWalkPipeline',
    'PrimeKGTaskGenerator',
    'ConsultationTask',
    'WalkPath',
    'PrimeKGAdapter'
]

# 保持向后兼容的别名
RealMedicalKnowledgeGraph = None  # 从 generation.core.kg_loader 导入
PrimeKGLoader = None  # 从 generation.core.kg_loader 导入

if __name__ == "__main__":
    print("="*70)
    print(" PrimeKG Random Walk Pipeline")
    print(" (已迁移到 medical_task_suite/generation/)")
    print("="*70)
    print()
    print("推荐使用方式:")
    print()
    print("  from medical_task_suite.generation import PrimeKGRandomWalkPipeline")
    print("  pipeline = PrimeKGRandomWalkPipeline(use_cache=True)")
    print()
    print("或者使用根目录脚本:")
    print("  python generate_primekg_tasks.py")
    print()
    print("文档位置:")
    print("  - medical_task_suite/generation/README.md")
    print("  - PRIMEKG_USAGE_GUIDE.md")
    print()
