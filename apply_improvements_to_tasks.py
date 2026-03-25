#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行数据质量改进器

对 chinese_internal_medicine/tasks.json 应用所有数据质量改进模块

作者：Claude Sonnet 4.5
日期：2025-03-20
"""

import json
import sys
from pathlib import Path

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent / "DataQualityFiltering"))

# 导入改进器
from modules.scenario_classifier import ScenarioClassifier
from modules.uncertainty_handler import UncertaintyHandler
from modules.safety_validator import SafetyValidator
from modules.inquiry_threshold_validator import InquiryThresholdValidator


def apply_improvements(input_file: str, output_file: str):
    """
    应用所有数据质量改进到任务文件

    Args:
        input_file: 输入的 tasks.json 文件路径
        output_file: 输出的改进后 tasks.json 文件路径
    """
    print("="*60)
    print(" 数据质量改进器")
    print("="*60)

    # 1. 加载原始数据
    print(f"\n[1/5] 加载数据: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        tasks = json.load(f)
    print(f"✓ 加载了 {len(tasks)} 个任务")

    # 2. 初始化改进模块
    print("\n[2/5] 初始化改进模块")
    scenario_classifier = ScenarioClassifier()
    uncertainty_handler = UncertaintyHandler()
    safety_validator = SafetyValidator()
    threshold_validator = InquiryThresholdValidator({})
    print("✓ 场景分类器")
    print("✓ 不确定性处理器")
    print("✓ 安全验证器")
    print("✓ 追问阈值验证器")

    # 3. 应用改进
    print("\n[3/5] 应用改进...")
    improved_count = 0

    for i, task in enumerate(tasks):
        # 确保 metadata 存在
        if 'metadata' not in task:
            task['metadata'] = {}

        # 3.1 场景分类（传入完整任务）
        scenario_result = scenario_classifier.classify(task)
        scenario_type = scenario_result.get('type')  # 修正：用 'type' 不是 'scenario_type'
        task['metadata']['scenario_type'] = scenario_type
        task['metadata']['scenario_name'] = scenario_result.get('name')
        task['metadata']['scenario_confidence'] = scenario_result.get('confidence_score', 0)

        # 3.2 添加不确定性处理
        task_with_uncertainty = uncertainty_handler.add_uncertainty(task)
        if task_with_uncertainty.get('uncertainties_added'):
            task['metadata']['has_uncertainty'] = True
            task['metadata']['uncertainty_tags'] = task_with_uncertainty.get('uncertainties_added', [])

        # 3.3 添加安全规则
        safety_result = safety_validator.generate_rules(task, scenario_result)
        if safety_result.get('rules'):
            task['metadata']['safety_rules'] = safety_result.get('rules', [])

        # 3.4 添加追问阈值规则
        threshold_result = threshold_validator.generate_threshold_rules(task)
        if threshold_result.get('rules'):
            task['metadata']['threshold_rules'] = threshold_result.get('rules', [])

        improved_count += 1

        # 每50个任务显示进度
        if (i + 1) % 50 == 0:
            print(f"  进度: {i+1}/{len(tasks)}")

    print(f"✓ 改进了 {improved_count} 个任务")

    # 4. 统计改进效果
    print("\n[4/5] 改进效果统计")
    scenarios = {}
    uncertainties = 0
    safeties = 0

    for task in tasks:
        scenario = task.get('metadata', {}).get('scenario_type', 'UNKNOWN')
        scenarios[scenario] = scenarios.get(scenario, 0) + 1

        if task.get('metadata', {}).get('has_uncertainty'):
            uncertainties += 1

        if task.get('metadata', {}).get('safety_rules'):
            safeties += 1

    print(f"✓ 场景分类分布:")
    for scenario, count in sorted(scenarios.items(), key=lambda x: -x[1])[:5]:
        print(f"    - {scenario}: {count}")

    print(f"✓ 添加不确定性标记: {uncertainties} 个任务")
    print(f"✓ 添加安全规则: {safeties} 个任务")

    # 5. 保存改进后的数据
    print(f"\n[5/5] 保存改进数据: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)
    print(f"✓ 保存完成")

    # 显示对比
    print("\n" + "="*60)
    print(" 改进对比")
    print("="*60)
    print(f"原始文件: {input_file}")
    print(f"改进文件: {output_file}")

    # 显示一个改进示例
    original_task = tasks[0]
    print(f"\n改进示例 (任务 {original_task['id']}):")
    print(f"  原始字段: {list(original_task.keys())}")
    print(f"  新增 metadata 字段: {list(original_task.get('metadata', {}).keys())}")
    print(f"  场景类型: {original_task.get('metadata', {}).get('scenario_type', 'N/A')}")
    print(f"  不确定性标记: {original_task.get('metadata', {}).get('uncertainty_markers', [])}")
    print(f"  安全规则: {len(original_task.get('metadata', {}).get('safety_rules', []))} 条")

    return tasks


if __name__ == "__main__":
    import sys
    import io

    # 设置 UTF-8 编码输出
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # 输入输出文件路径
    input_file = "data/tau2/domains/clinical/chinese_internal_medicine/tasks.json"
    output_file = "data/tau2/domains/clinical/chinese_internal_medicine/tasks_improved.json"

    # 运行改进
    try:
        improved_tasks = apply_improvements(input_file, output_file)

        print("\n" + "="*60)
        print(" ✓ 改进完成！")
        print("="*60)
        print(f"\n下一步:")
        print(f"1. 查看改进后的文件: {output_file}")
        print(f"2. 对比原始文件和改进文件的差异")
        print(f"3. 在评估中使用改进后的任务数据")

    except Exception as e:
        print(f"\n[错误] 改进失败: {e}")
        import traceback
        traceback.print_exc()
