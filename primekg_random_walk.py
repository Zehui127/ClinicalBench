#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrimeKG Random Walk - 向后兼容包装器

此脚本提供向后兼容性，实际功能已迁移到:
medical_task_suite/generation/

【注意】此文件已弃用，请使用以下方式导入：
    from medical_task_suite.generation import PrimeKGRandomWalkPipeline
    或
    from medical_task_suite.generation.core.random_walk import PrimeKGRandomWalkPipeline
"""

import sys
from pathlib import Path

# 添加 medical_task_suite 到路径
sys.path.insert(0, str(Path(__file__).parent / "medical_task_suite"))

# 从 medical_task_suite 导入所有核心类
from generation.core.random_walk import (
    PrimeKGRandomWalkPipeline,
    PrimeKGTaskGenerator,
    ConsultationTask,
    WalkPath,
    PrimeKGAdapter,
    PrimeKGRandomWalkGenerator
)

# 从 medical_task_suite 导入加载器
from generation.core.kg_loader import (
    PrimeKGLoader,
    RealMedicalKnowledgeGraph
)

# 导出与原脚本相同的接口
__all__ = [
    'PrimeKGRandomWalkPipeline',
    'PrimeKGTaskGenerator',
    'ConsultationTask',
    'WalkPath',
    'PrimeKGAdapter',
    'PrimeKGRandomWalkGenerator',
    'PrimeKGLoader',
    'RealMedicalKnowledgeGraph'
]

# 保持向后兼容 - 如果被作为脚本运行，显示提示信息
if __name__ == "__main__":
    print("="*70)
    print(" ⚠️  PRIMEKG RANDOM WALK - 向后兼容模式")
    print("="*70)
    print()
    print("此脚本已迁移到 medical_task_suite/generation/")
    print()
    print("✅ 向后兼容：现有代码无需修改，继续工作")
    print()
    print("📖 推荐阅读：")
    print("   - medical_task_suite/generation/README.md")
    print("   - PRIMEKG_UNIFICATION.md")
    print()
    print("🎯 推荐使用方式：")
    print("   from medical_task_suite.generation import PrimeKGRandomWalkPipeline")
    print("   pipeline = PrimeKGRandomWalkPipeline(use_cache=True)")
    print()
    print("📝 替代导入：")
    print("   ❌ 旧方式: from primekg_random_walk import PrimeKGRandomWalkPipeline")
    print("   ✅ 新方式: from medical_task_suite.generation import PrimeKGRandomWalkPipeline")
    print()
    print("="*70)
