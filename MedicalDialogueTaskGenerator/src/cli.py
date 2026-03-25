"""
医学对话任务生成器命令行接口
Medical Dialogue Task Generator - CLI

This module provides a command-line interface for the task generator.
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Optional

from .core.task_generator import TaskGenerator
from .models.data_models import RawDialogueData
from .utils.validator import TaskValidator


def load_raw_data(file_path: str) -> list:
    """加载原始对话数据

    Args:
        file_path: 文件路径

    Returns:
        原始对话数据列表
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 如果是单个对象，转换为列表
    if isinstance(data, dict):
        data = [data]

    return data


def save_tasks(tasks: list, file_path: str):
    """保存任务到文件

    Args:
        tasks: 任务列表
        file_path: 文件路径
    """
    # 转换为字典格式
    tasks_dict = [task.to_dict() if hasattr(task, 'to_dict') else task for task in tasks]

    # 确保目录存在
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(tasks_dict, f, ensure_ascii=False, indent=2)


def generate_single(input_path: str, output_path: str, config_path: Optional[str] = None):
    """生成单个任务

    Args:
        input_path: 输入文件路径
        output_path: 输出文件路径
        config_path: 配置文件路径（可选）
    """
    print(f"Loading data from {input_path}...")
    raw_data_list = load_raw_data(input_path)

    if len(raw_data_list) == 0:
        print("Error: No data found in input file")
        return

    if len(raw_data_list) > 1:
        print(f"Warning: Input file contains {len(raw_data_list)} items, processing only the first one")

    raw_data_dict = raw_data_list[0]
    raw_data = RawDialogueData(**raw_data_dict)

    print(f"Generating task for: {raw_data.id}")

    # 初始化生成器
    generator = TaskGenerator(config_path=config_path)

    # 生成任务
    task = generator.generate(raw_data)

    print(f"Task generated successfully:")
    print(f"  ID: {task.id}")
    print(f"  Difficulty: {task.difficulty}")
    print(f"  Scenario: {task.metadata.scenario_name}")

    # 保存任务
    save_tasks([task], output_path)
    print(f"Task saved to {output_path}")


def generate_batch(input_dir: str, output_dir: str, config_path: Optional[str] = None):
    """批量生成任务

    Args:
        input_dir: 输入目录
        output_dir: 输出目录
        config_path: 配置文件路径（可选）
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    # 确保输出目录存在
    output_path.mkdir(parents=True, exist_ok=True)

    # 查找所有输入文件
    input_files = list(input_path.glob("*.json"))
    if not input_files:
        print(f"Error: No JSON files found in {input_dir}")
        return

    print(f"Found {len(input_files)} input files")

    # 初始化生成器
    generator = TaskGenerator(config_path=config_path)
    all_tasks = []

    # 处理每个文件
    for input_file in input_files:
        print(f"\nProcessing {input_file.name}...")

        try:
            raw_data_list = load_raw_data(str(input_file))
            print(f"  Loaded {len(raw_data_list)} items")

            # 生成任务
            for raw_data_dict in raw_data_list:
                try:
                    raw_data = RawDialogueData(**raw_data_dict)
                    task = generator.generate(raw_data)
                    all_tasks.append(task)
                except Exception as e:
                    print(f"  Error generating task for {raw_data_dict.get('id', 'unknown')}: {e}")

        except Exception as e:
            print(f"  Error processing file: {e}")

    # 保存所有任务
    output_file = output_path / "all_tasks.json"
    save_tasks(all_tasks, str(output_file))
    print(f"\nGenerated {len(all_tasks)} tasks in total")
    print(f"Saved to {output_file}")


def validate_tasks(input_path: str):
    """验证任务

    Args:
        input_path: 输入文件路径
    """
    print(f"Loading tasks from {input_path}...")

    with open(input_path, 'r', encoding='utf-8') as f:
        tasks_data = json.load(f)

    if isinstance(tasks_data, dict):
        tasks_data = [tasks_data]

    print(f"Loaded {len(tasks_data)} tasks")

    # 验证任务
    validator = TaskValidator()
    valid_count = 0
    invalid_count = 0

    for i, task_dict in enumerate(tasks_data):
        from .models.data_models import MedicalDialogueTask
        try:
            task = MedicalDialogueTask.from_dict(task_dict)
            if validator.validate(task):
                valid_count += 1
            else:
                invalid_count += 1
                errors = validator.get_errors()
                print(f"  Task {i+1} ({task_dict.get('id', 'unknown')}) validation failed:")
                for error in errors:
                    print(f"    - {error}")
        except Exception as e:
            invalid_count += 1
            print(f"  Task {i+1} ({task_dict.get('id', 'unknown')}) error: {e}")

    print(f"\nValidation results:")
    print(f"  Valid: {valid_count}")
    print(f"  Invalid: {invalid_count}")
    print(f"  Pass rate: {valid_count/(valid_count+invalid_count)*100:.1f}%")


def show_statistics(input_path: str):
    """显示任务统计信息

    Args:
        input_path: 输入文件路径
    """
    print(f"Loading tasks from {input_path}...")

    with open(input_path, 'r', encoding='utf-8') as f:
        tasks_data = json.load(f)

    if isinstance(tasks_data, dict):
        tasks_data = [tasks_data]

    print(f"\nTotal tasks: {len(tasks_data)}")

    # 难度分布
    from collections import Counter
    difficulty_dist = Counter(t.get('difficulty') for t in tasks_data)
    print("\nDifficulty distribution:")
    for diff, count in sorted(difficulty_dist.items()):
        print(f"  {diff}: {count} ({count/len(tasks_data)*100:.1f}%)")

    # 场景类型分布
    scenario_dist = Counter(t.get('metadata', {}).get('scenario_type') for t in tasks_data)
    print("\nScenario type distribution:")
    for scenario, count in scenario_dist.most_common():
        print(f"  {scenario}: {count} ({count/len(tasks_data)*100:.1f}%)")

    # 患者行为分布
    behavior_counts = Counter()
    for task in tasks_data:
        behaviors = task.get('patient_behavior', {}).get('behaviors', [])
        for behavior in behaviors:
            behavior_counts[behavior] += 1

    print("\nPatient behavior distribution:")
    for behavior, count in behavior_counts.most_common():
        print(f"  {behavior}: {count}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="医学对话任务生成器 - Medical Dialogue Task Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 生成单个任务
  python -m src.cli --input input.json --output output.json

  # 批量生成
  python -m src.cli --input-dir raw_data/ --output-dir tasks/

  # 验证任务
  python -m src.cli --validate --input tasks.json

  # 显示统计信息
  python -m src.cli --stats --input tasks.json
        """
    )

    parser.add_argument('--input', type=str, help='输入文件路径')
    parser.add_argument('--input-dir', type=str, help='输入目录路径（批量处理）')
    parser.add_argument('--output', type=str, help='输出文件路径')
    parser.add_argument('--output-dir', type=str, help='输出目录路径（批量处理）')
    parser.add_argument('--config', type=str, help='配置文件路径')
    parser.add_argument('--validate', action='store_true', help='验证模式')
    parser.add_argument('--stats', action='store_true', help='统计模式')
    parser.add_argument('--input', type=str, help='输入文件路径（用于验证或统计）')

    args = parser.parse_args()

    # 验证模式
    if args.validate:
        if not args.input:
            print("Error: --input is required for validation")
            sys.exit(1)
        validate_tasks(args.input)
        return

    # 统计模式
    if args.stats:
        if not args.input:
            print("Error: --input is required for statistics")
            sys.exit(1)
        show_statistics(args.input)
        return

    # 生成模式
    if args.input_dir:
        # 批量生成
        if not args.output_dir:
            print("Error: --output-dir is required with --input-dir")
            sys.exit(1)
        generate_batch(args.input_dir, args.output_dir, args.config)
    elif args.input:
        # 单个文件生成
        if not args.output:
            print("Error: --output is required with --input")
            sys.exit(1)
        generate_single(args.input, args.output, args.config)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
