#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrimeKG 任务转换为 tau2 格式

将 PrimeKG Random Walk 生成的任务转换为 tau2-bench 兼容格式
"""

import json
import sys
import io
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 从 core 模块导入（相对导入）
from ..core.random_walk import ConsultationTask, WalkPath


def convert_to_tau2_format(primekg_task: ConsultationTask, domain: str = "primekg") -> Dict[str, Any]:
    """
    将 PrimeKG 任务转换为 tau2 格式

    Args:
        primekg_task: PrimeKG 生成的任务
        domain: 领域名称

    Returns:
        tau2 格式的任务字典
    """
    # 提取对话并转换为 tau2 格式
    dialogue_turns = []
    for turn in primekg_task.dialogue_turns:
        if turn['role'] == 'patient':
            dialogue_turns.append({
                "role": "user",
                "content": turn['content']
            })
        else:  # doctor
            dialogue_turns.append({
                "role": "assistant",
                "content": turn['content']
            })

    # 构建完整的任务描述
    disease_name = primekg_task.patient_profile.get('underlying_condition', 'Unknown condition')
    chief_complaint = primekg_task.patient_profile['chief_complaint']

    # 提取路径信息
    path_info = []
    for i, node_id in enumerate(primekg_task.path.nodes):
        # 这里简化处理，实际应该查询节点名称
        node_type = primekg_task.metadata.get('node_types', [])[i] if i < len(primekg_task.metadata.get('node_types', [])) else "unknown"
        path_info.append(node_type)

    # 构建 tau2 格式任务
    tau2_task = {
        "id": primekg_task.task_id,
        "description": {
            "purpose": f"Medical consultation - {chief_complaint}",
            "relevant_policies": None,
            "notes": f"Generated from PrimeKG knowledge graph. Diagnosis: {disease_name}. Path: {' → '.join(path_info)}"
        },
        "user_scenario": {
            "persona": f"{primekg_task.patient_profile['age']}-year-old {primekg_task.patient_profile['gender']} patient with {chief_complaint}",
            "instructions": {
                "domain": domain,
                "reason_for_call": chief_complaint,
                "known_info": f"Patient has {chief_complaint} for {primekg_task.patient_profile['duration_days']} days. Severity: {primekg_task.patient_profile['severity']}.",
                "unknown_info": disease_name if disease_name != "Unknown condition" else None,
                "task_instructions": f"You are a patient seeking medical advice.\n\nYour concern: {chief_complaint}\n\nDuration: {primekg_task.patient_profile['duration_days']} days\nSeverity: {primekg_task.patient_profile['severity']}\n\nPlease engage in a natural conversation with the doctor about your health concern."
            }
        },
        "ticket": chief_complaint,
        "initial_state": {
            "initialization_actions": [
                {
                    "env_type": "user",
                    "func_name": "set_user_info",
                    "arguments": {
                        "name": f"Patient_{primekg_task.task_id}",
                        "mrn": f"MRN{primekg_task.task_id.replace('primekg_', '').replace('_', '')}",
                        "age": primekg_task.patient_profile['age'],
                        "gender": primekg_task.patient_profile['gender']
                    }
                }
            ]
        },
        "evaluation_criteria": {
            "actions": [
                {
                    "action_id": "provide_medical_advice",
                    "requestor": "assistant",
                    "name": "provide_medical_advice",
                    "arguments": {
                        "should_address": chief_complaint
                    }
                }
            ],
            "communication_checks": [
                {
                    "check_id": "helpful_response",
                    "criteria": "Response should address patient's concern"
                },
                {
                    "check_id": "medical_accuracy",
                    "criteria": "Medical advice should be accurate based on PrimeKG knowledge"
                }
            ]
        },
        "reference_dialogue": dialogue_turns,
        "metadata": {
            "source": "PrimeKG Random Walk Generator",
            "primekg_path_length": primekg_task.metadata.get('path_length', 0),
            "primekg_node_types": primekg_task.metadata.get('node_types', []),
            "primekg_edge_types": primekg_task.metadata.get('edge_types', []),
            "generation_date": "2025-03-22"
        }
    }

    return tau2_task


def load_primekg_task(json_file: Path) -> ConsultationTask:
    """从 JSON 文件加载 PrimeKG 任务"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 重建 ConsultationTask 对象
    path = WalkPath(
        nodes=data['path']['nodes'],
        edges=data['path']['edges']
    )

    task = ConsultationTask(
        task_id=data['task_id'],
        path=path,
        patient_profile=data['patient_profile'],
        dialogue_turns=data['dialogue'],
        metadata=data['metadata']
    )

    return task


def batch_convert(
    primekg_tasks_dir: str,
    output_dir: str,
    domain: str = "primekg_internal_medicine"
) -> List[Dict[str, Any]]:
    """
    批量转换 PrimeKG 任务为 tau2 格式

    Args:
        primekg_tasks_dir: PrimeKG 任务目录
        output_dir: tau2 输出目录
        domain: 领域名称

    Returns:
        转换后的 tau2 任务列表
    """
    input_path = Path(primekg_tasks_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f" PrimeKG → tau2 转换工具")
    print(f"{'='*60}")
    print(f"\n输入目录: {input_path}")
    print(f"输出目录: {output_path}")
    print(f"领域: {domain}")

    # 查找所有 PrimeKG 任务文件
    primekg_files = list(input_path.glob("primekg_*.json"))

    if not primekg_files:
        print(f"\n错误: 在 {input_path} 中没有找到 PrimeKG 任务文件")
        print(f"请先运行: python test_primekg_random_walk.py")
        return []

    print(f"\n找到 {len(primekg_files)} 个任务文件")

    tau2_tasks = []

    # 转换每个任务
    for i, primekg_file in enumerate(primekg_files, 1):
        print(f"\n[{i}/{len(primekg_files)}] 转换: {primekg_file.name}")

        try:
            # 加载 PrimeKG 任务
            primekg_task = load_primekg_task(primekg_file)

            # 转换为 tau2 格式
            tau2_task = convert_to_tau2_format(primekg_task, domain)
            tau2_tasks.append(tau2_task)

            print(f"  ✓ 转换成功: {tau2_task['id']}")

        except Exception as e:
            print(f"  ✗ 转换失败: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*60}")
    print(f" 转换完成")
    print(f"{'='*60}")
    print(f"\n总任务数: {len(tau2_tasks)}")

    if not tau2_tasks:
        return tau2_tasks

    # 保存任务文件
    output_file = output_path / "tasks.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(tau2_tasks, f, ensure_ascii=False, indent=2)

    print(f"✓ 任务文件: {output_file}")

    # 生成 train/test split
    import random
    random.seed(42)
    random.shuffle(tau2_tasks)

    split_point = max(1, int(len(tau2_tasks) * 0.8))
    train_tasks = tau2_tasks[:split_point]
    test_tasks = tau2_tasks[split_point:]

    split_data = {
        "train": [t['id'] for t in train_tasks],
        "test": [t['id'] for t in test_tasks],
        "metadata": {
            "total_tasks": len(tau2_tasks),
            "train_size": len(train_tasks),
            "test_size": len(test_tasks),
            "split_ratio": "80/20"
        }
    }

    split_file = output_path / "split_tasks.json"
    with open(split_file, 'w', encoding='utf-8') as f:
        json.dump(split_data, f, ensure_ascii=False, indent=2)

    print(f"✓ 划分文件: {split_file}")
    print(f"  训练集: {len(train_tasks)} 任务")
    print(f"  测试集: {len(test_tasks)} 任务")

    # 生成数据库信息文件
    db_data = {
        "domain": domain,
        "description": f"Medical consultation tasks generated from PrimeKG knowledge graph using Random Walk algorithm",
        "source": "Harvard Medical School PrimeKG",
        "task_count": len(tau2_tasks),
        "metadata": {
            "primekg_version": "v2",
            "primekg_nodes": 23087,
            "primekg_edges": 617118,
            "generated_by": "PrimeKG Random Walk Generator",
            "generated_date": "2025-03-22",
            "algorithm": "Random Walk with weighted edge selection"
        }
    }

    db_file = output_path / "db.json"
    with open(db_file, 'w', encoding='utf-8') as f:
        json.dump(db_data, f, ensure_ascii=False, indent=2)

    print(f"✓ 数据库文件: {db_file}")

    # 统计信息
    print(f"\n{'='*60}")
    print(f" 任务统计")
    print(f"{'='*60}")

    # 症状统计
    symptoms = [t['user_scenario']['instructions']['reason_for_call'] for t in tau2_tasks]
    from collections import Counter
    symptom_counts = Counter(symptoms)

    print(f"\n症状分布:")
    for symptom, count in symptom_counts.most_common(10):
        print(f"  {symptom}: {count}")

    # 路径长度统计
    path_lengths = [t['metadata']['primekg_path_length'] for t in tau2_tasks]
    avg_length = sum(path_lengths) / len(path_lengths)

    print(f"\n路径长度:")
    print(f"  平均: {avg_length:.1f} 节点")
    print(f"  最短: {min(path_lengths)} 节点")
    print(f"  最长: {max(path_lengths)} 节点")

    # 对话轮次统计
    dialogue_lengths = [len(t['reference_dialogue']) for t in tau2_tasks]
    avg_dialogue = sum(dialogue_lengths) / len(dialogue_lengths)

    print(f"\n对话轮次:")
    print(f"  平均: {avg_dialogue:.1f} 轮")
    print(f"  最短: {min(dialogue_lengths)} 轮")
    print(f"  最长: {max(dialogue_lengths)} 轮")

    print(f"\n{'='*60}")
    print(f" 转换成功！")
    print(f"{'='*60}")
    print(f"\n输出文件:")
    print(f"  - {output_file}")
    print(f"  - {split_file}")
    print(f"  - {db_file}")

    return tau2_tasks


def main():
    """主函数"""
    # 默认路径
    primekg_tasks_dir = "data/primekg_tasks"
    output_dir = "data/tau2/domains/clinical/primekg"
    domain = "primekg_internal_medicine"

    # 检查输入目录
    if not Path(primekg_tasks_dir).exists():
        print(f"\n错误: PrimeKG 任务目录不存在: {primekg_tasks_dir}")
        print(f"\n请先运行以下命令生成 PrimeKG 任务:")
        print(f"  python test_primekg_random_walk.py")
        return 1

    # 执行转换
    try:
        tau2_tasks = batch_convert(
            primekg_tasks_dir=primekg_tasks_dir,
            output_dir=output_dir,
            domain=domain
        )

        if tau2_tasks:
            print(f"\n✓ 成功转换 {len(tau2_tasks)} 个任务")
            print(f"\n下一步:")
            print(f"  1. 查看生成的任务: {output_dir}/tasks.json")
            print(f"  2. 在评估框架中使用这些任务")
            print(f"  3. 根据需要调整任务内容")
            return 0
        else:
            print(f"\n✗ 没有转换任何任务")
            return 1

    except Exception as e:
        print(f"\n✗ 转换失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
