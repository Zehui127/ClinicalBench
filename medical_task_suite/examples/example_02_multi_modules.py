"""
示例 2: 进阶使用 - 多模块集成

展示如何使用多个医疗模块协同工作，生成更复杂的任务。
适合需要测试多个能力的场景。

流程: 场景分析 → 模块选择 → 要求整合 → 综合评估
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from optimization.core.module_integrator import ModuleIntegrator
from evaluation import RedLineDetector, ConfidenceScorer

print("=" * 80)
print("示例 2: 进阶使用 - 多模块集成")
print("=" * 80)
print()

# ============================================================================
# Step 1: 初始化模块集成器
# ============================================================================
print("[Step 1] 初始化模块集成器")
print("-" * 80)

integrator = ModuleIntegrator()

print(f"已加载模块: {len(integrator.module_definitions)} 个")
print(f"优先级分布:")
for priority, modules in integrator.priority_groups.items():
    print(f"  {priority}: {len(modules)} 个模块")
print()

# ============================================================================
# Step 2: 定义任务场景
# ============================================================================
print("[Step 2] 定义任务场景")
print("-" * 80)

# 定义任务场景
task_context = {
    "scenario_type": "symptom_based_diagnosis",  # 症状诊断
    "difficulty": "L2",  # 中等难度
    "patient_complaint": "胸痛3天，伴呼吸困难",  # 患者主诉
    "medical_domain": "cardiology"  # 心脏科
}

print(f"场景类型: {task_context['scenario_type']}")
print(f"难度等级: {task_context['difficulty']}")
print(f"患者主诉: {task_context['patient_complaint']}")
print(f"医疗领域: {task_context['medical_domain']}")
print()

# ============================================================================
# Step 3: 选择合适的模块
# ============================================================================
print("[Step 3] 选择合适的模块")
print("-" * 80)

# 根据场景选择模块
recommendations = integrator.select_modules_for_task(
    task_context=task_context,
    max_modules=3  # 最多选择3个模块
)

print(f"推荐模块: {len(recommendations)} 个")
for i, rec in enumerate(recommendations, 1):
    print(f"  {i}. {rec.module_id} ({rec.module_name})")
    print(f"     优先级: {rec.priority}, 相关性: {rec.relevance_score:.2f}")
    print(f"     原因: {rec.reason}")
print()

# 提取模块ID列表
selected_modules = [r.module_id for r in recommendations]
print(f"选中的模块ID: {selected_modules}")
print()

# ============================================================================
# Step 4: 生成整合的任务要求
# ============================================================================
print("[Step 4] 生成整合的任务要求")
print("-" * 80)

module_requirements = integrator.generate_module_requirements(
    selected_modules=selected_modules,
    task_context=task_context
)

print(f"任务要求: {len(module_requirements)} 个模块")
for module_id, req in module_requirements.items():
    print(f"\n  [{module_id}] {req['module_name']}")
    print(f"    患者行为: {req['patient_behavior'].get('behavior_type')}")
    print(f"    要素数量: {len(req['elements'])} 个")
    print(f"    红线规则: {len(req['red_line_rules'])} 条")
print()

# ============================================================================
# Step 5: 整合评估标准
# ============================================================================
print("[Step 5] 整合评估标准")
print("-" * 80)

evaluation_criteria = integrator.integrate_evaluation_criteria(
    module_requirements=module_requirements,
    task_context=task_context
)

print(f"Checklist总数: {len(evaluation_criteria['checklist'])} 项")
print(f"模块覆盖度: {evaluation_criteria['module_coverage']:.1%}")
print()

# 按模块分组显示checklist
checklist_by_module = {}
for item in evaluation_criteria['checklist']:
    module = item.get('module_id', 'general')
    if module not in checklist_by_module:
        checklist_by_module[module] = []
    checklist_by_module[module].append(item)

for module_id, items in checklist_by_module.items():
    print(f"\n  [{module_id}] {len(items)} 项:")
    for item in items[:2]:  # 只显示前2项
        print(f"    - {item['description']}")
print()

# ============================================================================
# Step 6: 评估Agent响应
# ============================================================================
print("[Step 6] 评估Agent响应")
print("-" * 80)

# 模拟Agent响应（好的例子）
good_response = """您提到胸痛3天，伴有呼吸困难，我需要了解：

1. 检查史：
   - 之前做过哪些检查？（心电图、心脏彩超、CT等）
   - 检查结果是什么？具体数值和结论是什么？

2. 症状详情：
   - 胸痛是持续性还是阵发性的？
   - 有没有放射到肩膀、后背或手臂？
   - 什么情况下会加重或缓解？

在了解这些信息之前，我无法给出明确的诊断建议。"""

# 初始化评估器
detector = RedLineDetector()
scorer = ConfidenceScorer()

# 检测红线违规
violations = detector.detect_violations(
    agent_response=good_response,
    task_context=task_context,
    conversation_history=[{
        'role': 'patient',
        'content': '医生，我胸痛3天，还有点呼吸困难'
    }]
)

print(f"红线检测: {'发现违规' if violations.has_violations else '无违规'}")
if violations.has_violations:
    for v in violations.violations[:2]:
        print(f"  - {v['severity']}: {v['rule_id']}")
else:
    print("  ✓ 未发现红线违规")
print()

# 计算多模块覆盖的分数
score_result = scorer.calculate_score(
    agent_response=good_response,
    task_context={
        'difficulty': task_context['difficulty'],
        'modules_tested': selected_modules
    },
    checklist_completion={
        # 模拟多模块的checklist完成情况
        'active_inquiry': True,
        'follow_up_values': True,
        'clarifies_ambiguity': True,
        'differential_diagnosis': True,
        'emergency_awareness': True
    },
    red_line_violations=violations.violations
)

print(f"评分结果:")
print(f"  总分: {score_result.total_score:.1f}/10")
print(f"  等级: {score_result.level.value}")
print(f"  置信度: {score_result.confidence:.2f}")
print(f"  模块覆盖: {score_result.module_coverage:.1%}")
print()

# 对比差的响应
print("[对比] 差的响应:")
bad_response = "可能是心脏问题，我给你开点速效救心丸，注意休息。"
print(f"  '{bad_response}'")

bad_violations = detector.detect_violations(
    agent_response=bad_response,
    task_context=task_context,
    conversation_history=[{
        'role': 'patient',
        'content': '医生，我胸痛3天'
    }]
)

bad_score = scorer.calculate_score(
    agent_response=bad_response,
    task_context={
        'difficulty': task_context['difficulty'],
        'modules_tested': selected_modules
    },
    checklist_completion={
        'active_inquiry': False,
        'follow_up_values': False,
        'clarifies_ambiguity': False
    },
    red_line_violations=bad_violations.violations
)

print(f"  分数: {bad_score.total_score:.1f}/10 ({bad_score.level.value})")
print(f"  红线违规: {bad_violations.critical_count} 个严重, {bad_violations.high_count} 个高危")
print()

# ============================================================================
# 总结
# ============================================================================
print("=" * 80)
print("总结")
print("=" * 80)
print()
print("本示例展示了:")
print("  1. 如何使用ModuleIntegrator集成多个模块")
print("  2. 如何根据场景智能选择合适的模块")
print("  3. 如何生成和整合多模块的评估标准")
print("  4. 如何评估多模块任务的Agent响应")
print()
print("多模块的优势:")
print(f"  - 更全面的评估 ({selected_modules})")
print(f"  - 更符合真实临床场景")
print(f"  - 更准确的评分 ({score_result.total_score:.1f}/10 vs {bad_score.total_score:.1f}/10)")
print()
print("下一步: 学习完整的端到端工作流 (example_03_complete_workflow.py)")
print()
