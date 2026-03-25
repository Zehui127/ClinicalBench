"""
示例 1: 基础使用 - 单模块任务生成

这是最简单的示例，展示如何使用单个医疗模块生成任务。
适合新手上手，了解基本流程。

流程: 选择模块 → 生成要求 → 生成评估标准
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules import create_lab_test_inquiry_module
from evaluation import RedLineDetector, ConfidenceScorer

print("=" * 80)
print("示例 1: 基础使用 - 单模块任务生成")
print("=" * 80)
print()

# ============================================================================
# Step 1: 创建模块
# ============================================================================
print("[Step 1] 创建模块")
print("-" * 80)

# 使用工厂函数创建模块
module = create_lab_test_inquiry_module()

print(f"模块名称: {module.config.module_name}")
print(f"模块ID: {module.config.module_id}")
print(f"模块描述: {module.config.description}")
print()

# ============================================================================
# Step 2: 生成任务要求
# ============================================================================
print("[Step 2] 生成任务要求")
print("-" * 80)

# 选择难度和患者行为
difficulty = 'L2'  # L1=简单, L2=中等, L3=困难
patient_behavior = 'forgetful'  # cooperative=配合, forgetful=记不清, concealing=隐瞒

# 生成任务要求
requirements = module.generate_task_requirements(
    difficulty=difficulty,
    patient_behavior=patient_behavior,
    context={}
)

print(f"难度等级: {requirements['difficulty']}")
print(f"患者行为: {requirements['patient_behavior']}")
print(f"核心要素: {len(requirements['elements'])} 个")
print()

# 显示核心要素
for i, element in enumerate(requirements['elements'][:3], 1):
    print(f"  要素{i}: {element['name']}")
    print(f"    场景: {element['scenario']}")
print()

# ============================================================================
# Step 3: 生成评估标准
# ============================================================================
print("[Step 3] 生成评估标准")
print("-" * 80)

evaluation_criteria = module.generate_evaluation_criteria(requirements)

print(f"Checklist项目: {len(evaluation_criteria['checklist'])} 个")
print()

# 显示前3个checklist项
for i, item in enumerate(evaluation_criteria['checklist'][:3], 1):
    print(f"  {i}. [{item['check_id']}] {item['description']}")
    print(f"     权重: {item['weight']}")
print()

# ============================================================================
# Step 4: 评估Agent响应
# ============================================================================
print("[Step 4] 评估Agent响应")
print("-" * 80)

# 模拟Agent响应
agent_response = """您之前做过心电图检查吗？结果是什么时候做的？
具体的心电图报告上写了什么结论？"""

# 初始化评估器
detector = RedLineDetector()
scorer = ConfidenceScorer()

# 检测红线违规
violations = detector.detect_violations(
    agent_response=agent_response,
    task_context={
        'difficulty': difficulty,
        'modules_tested': ['module_01']
    },
    conversation_history=[{
        'role': 'patient',
        'content': '我胸痛几天了'
    }]
)

print(f"红线检测: {'发现违规' if violations.has_violations else '无违规'}")
if violations.has_violations:
    for v in violations.violations:
        print(f"  - {v['severity']}: {v['rule_id']}")
print()

# 计算分数
score_result = scorer.calculate_score(
    agent_response=agent_response,
    task_context={
        'difficulty': difficulty,
        'modules_tested': ['module_01']
    },
    checklist_completion={
        'active_inquiry': True,  # 主动询问
        'follow_up_values': False,  # 没有追问数值
        'clarifies_ambiguity': False  # 没有澄清模糊信息
    },
    red_line_violations=violations.violations
)

print(f"评分结果:")
print(f"  总分: {score_result.total_score:.1f}/10")
print(f"  等级: {score_result.level.value}")
print(f"  通过: {score_result.passed}")
print()

# ============================================================================
# 总结
# ============================================================================
print("=" * 80)
print("总结")
print("=" * 80)
print()
print("本示例展示了:")
print("  1. 如何创建单个医疗模块")
print("  2. 如何生成任务要求和评估标准")
print("  3. 如何评估Agent的响应")
print()
print("下一步: 学习如何使用多个模块 (example_02_multi_modules.py)")
print()
