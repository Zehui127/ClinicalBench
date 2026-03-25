#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据集转换器 - 将基础医学任务转换为高级tau2任务
Dataset Converter - Upgrade basic medical tasks to advanced tau2 tasks
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any
import argparse

# Add MedicalDialogueTaskGenerator to path
sys.path.insert(0, str(Path(__file__).parent / "MedicalDialogueTaskGenerator"))

from src.core.task_generator import TaskGenerator
from src.models.data_models import RawDialogueData
from src.utils.validator import TaskValidator

def extract_raw_data(basic_task: Dict[str, Any]) -> RawDialogueData:
    """从基础任务中提取原始对话数据

    Args:
        basic_task: 基础任务字典

    Returns:
        RawDialogueData对象
    """
    # 从user_scenario中提取信息
    user_scenario = basic_task.get("user_scenario", {})
    instructions = user_scenario.get("instructions", {})
    metadata = basic_task.get("metadata", {})

    raw_data = RawDialogueData(
        id=basic_task.get("id", ""),
        ticket=instructions.get("reason_for_call", basic_task.get("ticket", "")),
        known_info=instructions.get("known_info", ""),
        department_cn=metadata.get("department_cn", "内科"),
        source=metadata.get("source", "Chinese MedDialog"),
        original_title=metadata.get("original_title", basic_task.get("ticket", ""))
    )

    return raw_data

def convert_single_task(basic_task: Dict[str, Any], generator: TaskGenerator, task_index: int) -> Dict[str, Any]:
    """转换单个任务

    Args:
        basic_task: 基础任务字典
        generator: 任务生成器
        task_index: 任务索引

    Returns:
        转换后的高级任务字典
    """
    try:
        # 提取原始数据
        raw_data = extract_raw_data(basic_task)

        # 生成高级任务
        advanced_task = generator.generate(raw_data)

        # 转换为字典
        advanced_dict = advanced_task.to_dict()

        # 保留原始任务的重要字段
        advanced_dict["original_task_id"] = basic_task.get("id")
        advanced_dict["conversion_metadata"] = {
            "converted_from": "basic_tau2_task",
            "converter_version": "1.0",
            "conversion_index": task_index
        }

        return advanced_dict

    except Exception as e:
        print(f"Error converting task {basic_task.get('id')}: {e}")
        import traceback
        traceback.print_exc()
        return None

def convert_dataset(input_file: str, output_file: str, sample_size: int = None,
                   difficulty_distribution: str = None):
    """转换整个数据集

    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径
        sample_size: 样本大小（用于测试）
        difficulty_distribution: 难度分布 (如 "L1:0.5,L2:0.3,L3:0.2")
    """
    print("=" * 70)
    print("数据集转换器 - Dataset Converter")
    print("=" * 70)

    # 1. 读取基础任务
    print(f"\n1. 读取基础任务: {input_file}")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            basic_tasks = json.load(f)
        print(f"   [OK] 读取了 {len(basic_tasks)} 个基础任务")
    except Exception as e:
        print(f"   [FAIL] 读取失败: {e}")
        return

    # 采样（如果指定）
    if sample_size and sample_size < len(basic_tasks):
        print(f"\n2. 采样 {sample_size} 个任务用于测试")
        basic_tasks = basic_tasks[:sample_size]
        print(f"   [OK] 采样完成")

    # 2. 初始化生成器
    print(f"\n3. 初始化任务生成器")
    try:
        # 解析难度分布
        config = {}
        if difficulty_distribution:
            print(f"   使用自定义难度分布: {difficulty_distribution}")
            # 这里可以添加难度分布解析逻辑

        generator = TaskGenerator(config=config)
        print(f"   [OK] 生成器初始化成功")
    except Exception as e:
        print(f"   [FAIL] 生成器初始化失败: {e}")
        return

    # 3. 转换任务
    print(f"\n4. 开始转换任务")
    advanced_tasks = []
    success_count = 0
    fail_count = 0

    for i, basic_task in enumerate(basic_tasks, 1):
        if i % 10 == 0:
            print(f"   进度: {i}/{len(basic_tasks)}...")

        advanced_task = convert_single_task(basic_task, generator, i)
        if advanced_task:
            advanced_tasks.append(advanced_task)
            success_count += 1
        else:
            fail_count += 1

    print(f"\n   [OK] 转换完成: {success_count} 成功, {fail_count} 失败")

    # 4. 验证任务
    print(f"\n5. 验证转换后的任务")
    validator = TaskValidator()
    valid_count = 0
    invalid_count = 0

    for task in advanced_tasks:
        try:
            # 这里我们简单验证必要字段是否存在
            if all(key in task for key in ['id', 'description', 'user_scenario', 'ticket',
                                            'evaluation_criteria', 'metadata', 'difficulty']):
                valid_count += 1
            else:
                invalid_count += 1
        except Exception as e:
            invalid_count += 1

    print(f"   验证结果: {valid_count} 通过, {invalid_count} 失败")

    # 5. 保存结果
    print(f"\n6. 保存转换结果: {output_file}")
    try:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(advanced_tasks, f, ensure_ascii=False, indent=2)
        print(f"   [OK] 保存成功")

        # 文件大小统计
        file_size = output_path.stat().st_size
        print(f"   文件大小: {file_size / 1024 / 1024:.2f} MB")

    except Exception as e:
        print(f"   [FAIL] 保存失败: {e}")
        return

    # 6. 统计分析
    print(f"\n7. 转换统计")
    from collections import Counter

    difficulty_dist = Counter(task.get('difficulty', 'Unknown') for task in advanced_tasks)
    scenario_dist = Counter(task.get('metadata', {}).get('scenario_type', 'Unknown') for task in advanced_tasks)

    print(f"\n   难度分布:")
    for diff, count in sorted(difficulty_dist.items()):
        percentage = count / len(advanced_tasks) * 100
        print(f"     - {diff}: {count} ({percentage:.1f}%)")

    print(f"\n   场景类型分布:")
    for scenario, count in scenario_dist.most_common():
        percentage = count / len(advanced_tasks) * 100
        print(f"     - {scenario}: {count} ({percentage:.1f}%)")

    # 7. 对比分析
    print(f"\n8. 转换前后对比")
    print(f"   原始任务数: {len(basic_tasks)}")
    print(f"   转换后任务数: {len(advanced_tasks)}")
    print(f"   成功率: {success_count / len(basic_tasks) * 100:.1f}%")

    # 分析新增功能
    advanced_features = {
        '难度分级': sum(1 for task in advanced_tasks if task.get('difficulty')),
        '患者行为': sum(1 for task in advanced_tasks if task.get('patient_behavior')),
        '对话流程': sum(1 for task in advanced_tasks if task.get('conversation_flow')),
        '红线测试': sum(1 for task in advanced_tasks if task.get('red_line_tests')),
        '系统记录': sum(1 for task in advanced_tasks if task.get('system_records')),
    }

    print(f"\n   新增功能统计:")
    for feature, count in advanced_features.items():
        percentage = count / len(advanced_tasks) * 100
        print(f"     - {feature}: {count} ({percentage:.1f}%)")

    print("\n" + "=" * 70)
    print("转换完成!")
    print("=" * 70)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='转换基础医学任务为高级tau2任务')
    parser.add_argument('--input', '-i', required=True, help='输入文件路径')
    parser.add_argument('--output', '-o', required=True, help='输出文件路径')
    parser.add_argument('--sample', '-s', type=int, help='样本大小（用于测试）')
    parser.add_argument('--difficulty', '-d', help='难度分布 (如 "L1:0.5,L2:0.3,L3:0.2")')

    args = parser.parse_args()

    convert_dataset(
        input_file=args.input,
        output_file=args.output,
        sample_size=args.sample,
        difficulty_distribution=args.difficulty
    )
