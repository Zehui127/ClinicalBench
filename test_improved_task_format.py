#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的医疗任务格式

展示使用新的 MedicalPersona 和 MedicalEvaluationCriteria 的任务格式
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, 'src')
sys.path.insert(0, 'medical_task_suite/generation')

from tau2.data_model.medical_tasks import MedicalPersona, MedicalEvaluationCriteria, ToolCategory
from medical_task_suite.generation.utils.tau2_converter import create_medical_persona, create_medical_evaluation_criteria


def show_improved_task_format():
    """展示改进后的任务格式"""
    print("=" * 70)
    print("改进后的医疗任务格式示例")
    print("=" * 70)
    print()

    # 模拟一个 PrimeKG 任务
    class MockConsultationTask:
        def __init__(self):
            self.task_id = "primekg_task_cluster_headache"
            self.patient_profile = {
                'age': 54,
                'gender': 'male',
                'chief_complaint': 'Cluster headache',
                'duration_days': 21,
                'severity': 'severe',
                'underlying_condition': 'cluster headache, familial',
                'additional_symptoms': ['eye pain', 'nasal congestion', 'restlessness']
            }

    mock_task = MockConsultationTask()

    # 1. 创建医疗角色
    print("1. 医疗角色 (MedicalPersona)")
    print("-" * 70)
    medical_persona = create_medical_persona(mock_task, mock_task.patient_profile['chief_complaint'])
    print(json.dumps(medical_persona, indent=2, ensure_ascii=False))
    print()

    # 2. 创建医疗评估标准
    print("2. 医疗评估标准 (MedicalEvaluationCriteria)")
    print("-" * 70)
    medical_criteria = create_medical_evaluation_criteria(
        mock_task,
        mock_task.patient_profile['chief_complaint'],
        mock_task.patient_profile['underlying_condition']
    )
    print(json.dumps(medical_criteria, indent=2, ensure_ascii=False))
    print()

    # 3. 完整任务结构
    print("3. 完整任务结构关键字段")
    print("-" * 70)
    print("新增字段:")
    print("  - medical_persona: 结构化的医疗角色数据")
    print("  - evaluation_criteria.medical_criteria: 医疗评估标准")
    print("    ├─ expected_tool_category: 工具类别")
    print("    ├─ required_tools: 必需工具列表")
    print("    ├─ reasoning_steps: 推理步骤")
    print("    ├─ safety_checks: 安全检查项")
    print("    ├─ red_flags: 红线规则")
    print("    └─ min_turns/max_turns: 对话轮次限制")
    print()

    # 4. 对比旧格式
    print("4. 与旧格式的对比")
    print("-" * 70)
    print("旧格式问题:")
    print("  ✗ persona是字符串: \"54-year-old male patient...\"")
    print("  ✗ 缺少结构化的症状信息")
    print("  ✗ evaluation_criteria 只有通用字段")
    print("  ✗ 没有工具分类和推理步骤")
    print()
    print("新格式优势:")
    print("  ✓ medical_persona是结构化对象")
    print("  ✓ 症状清晰列在 symptoms 数组中")
    print("  ✓ medical_criteria 包含详细评估标准")
    print("  ✓ 工具分类支持自动评估")
    print("  ✓ 推理步骤可量化")
    print("  ✓ 安全检查和红线规则明确")
    print()

    print("=" * 70)
    print("下一步: 重新生成所有任务文件")
    print("=" * 70)
    print()
    print("要应用新的任务格式，需要:")
    print("  1. 运行更新后的 tau2_converter.py")
    print("  2. 重新生成所有 tasks_optimal_complete.json 等文件")
    print("  3. 验证新格式的任务能正确加载")


if __name__ == "__main__":
    show_improved_task_format()
