#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 PrimeKG 生成的 tau2 任务

展示如何在评估框架中使用 PrimeKG 任务
"""

import json
import sys
import io
from pathlib import Path

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def load_tasks():
    """加载 PrimeKG tau2 任务"""
    tasks_file = Path('data/tau2/domains/clinical/primekg/tasks.json')

    if not tasks_file.exists():
        print(f"错误: 任务文件不存在: {tasks_file}")
        print(f"\n请先运行: python primekg_to_tau2.py")
        return None

    with open(tasks_file, 'r', encoding='utf-8') as f:
        tasks = json.load(f)

    print(f"成功加载 {len(tasks)} 个任务")
    return tasks


def analyze_tasks(tasks):
    """分析任务"""
    print("\n" + "="*70)
    print(" 任务分析")
    print("="*70)

    # 统计症状
    symptoms = [t['user_scenario']['instructions']['reason_for_call'] for t in tasks]
    from collections import Counter
    symptom_counts = Counter(symptoms)

    print(f"\n症状分布:")
    for symptom, count in symptom_counts.items():
        print(f"  {symptom}: {count}")

    # 统计路径长度
    path_lengths = [t['metadata']['primekg_path_length'] for t in tasks]
    print(f"\n路径长度:")
    print(f"  平均: {sum(path_lengths)/len(path_lengths):.1f} 节点")
    print(f"  范围: {min(path_lengths)}-{max(path_lengths)} 节点")

    # 统计对话轮次
    dialogue_lengths = [len(t['reference_dialogue']) for t in tasks]
    print(f"\n对话轮次:")
    print(f"  平均: {sum(dialogue_lengths)/len(dialogue_lengths):.1f} 轮")
    print(f"  范围: {min(dialogue_lengths)}-{max(dialogue_lengths)} 轮")


def simulate_dialogue(task):
    """模拟对话"""
    print(f"\n{'='*70}")
    print(f" 模拟对话: {task['id']}")
    print(f"{'='*70}")

    print(f"\n患者: {task['user_scenario']['persona']}")
    print(f"主诉: {task['user_scenario']['instructions']['reason_for_call']}")

    print(f"\n对话:")
    for i, turn in enumerate(task['reference_dialogue'], 1):
        role = "患者" if turn['role'] == 'user' else "医生"
        print(f"\n  第 {i} 轮:")
        print(f"  {role}: {turn['content']}")


def check_medical_accuracy(task):
    """检查医学准确性"""
    print(f"\n{'='*70}")
    print(f" 医学准确性验证")
    print(f"{'='*70}")

    # 提取疾病信息
    notes = task['description']['notes']
    if "Diagnosis:" in notes:
        diagnosis = notes.split("Diagnosis:")[1].split(".")[0].strip()
        print(f"\n诊断: {diagnosis}")

    # 检查路径合理性
    node_types = task['metadata']['primekg_node_types']
    print(f"\n路径合理性:")
    print(f"  节点类型: {' -> '.join(node_types)}")

    # 验证路径
    expected_pattern = ["effect/phenotype", "disease", "drug"]
    if node_types == expected_pattern:
        print(f"  状态: 符合预期模式")
    else:
        print(f"  状态: 非标准路径")


def export_for_evaluation(tasks, output_file):
    """导出为评估格式"""
    print(f"\n{'='*70}")
    print(f" 导出评估格式")
    print(f"{'='*70}")

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

    print(f"\n已导出: {output_file}")
    print(f"任务数: {len(tasks)}")

    print(f"\n使用方法:")
    print(f"  from evaluation import evaluate_task")
    print(f"  evaluate_task(tasks, domain='clinical', subdomain='primekg')")


def main():
    """主函数"""
    print("\n" + "="*70)
    print(" PrimeKG Tasks 测试工具")
    print("="*70)

    # 1. 加载任务
    print("\n[1/5] 加载任务...")
    tasks = load_tasks()

    if not tasks:
        return 1

    # 2. 分析任务
    print("\n[2/5] 分析任务...")
    analyze_tasks(tasks)

    # 3. 模拟对话
    print("\n[3/5] 模拟对话...")
    # 选择第一个任务
    simulate_dialogue(tasks[0])

    # 4. 检查医学准确性
    print("\n[4/5] 检查医学准确性...")
    check_medical_accuracy(tasks[0])

    # 5. 导出评估格式
    print("\n[5/5] 导出评估格式...")
    export_for_evaluation(
        tasks,
        "data/tau2/domains/clinical/primekg/tasks_for_evaluation.json"
    )

    print("\n" + "="*70)
    print(" 测试完成！")
    print("="*70)

    print("\n下一步:")
    print("  1. 在评估框架中使用这些任务")
    print("  2. 评估模型性能")
    print("  3. 生成更多任务（运行 test_primekg_random_walk.py）")

    return 0


if __name__ == "__main__":
    sys.exit(main())
