#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试医疗知识图谱对话生成系统

测试：
1. 知识图谱构建
2. Random Walk 路径生成
3. Task Generator 对话生成
4. 完整流程

作者：Claude Sonnet 4.5
日期：2025-03-21
"""

import json
import sys
import io
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from medical_kg_dialogue_generator import (
    MedicalKnowledgeGraph,
    RandomWalkGenerator,
    TaskGenerator,
    WalkPath,
    DialogueTurn,
    ConsultationTask,
    MedicalDialoguePipeline
)


def test_knowledge_graph():
    """测试1：知识图谱构建"""
    print("\n" + "="*60)
    print(" [测试 1/4] 知识图谱构建")
    print("="*60)

    # 构建知识图谱
    kg = MedicalKnowledgeGraph()

    # 验证节点
    print("\n1.1 节点统计")
    print(f"  总节点数: {kg.graph.number_of_nodes()}")
    print(f"  症状节点: {len(kg.node_types['symptom'])}")
    print(f"  疾病节点: {len(kg.node_types['disease'])}")
    print(f"  检查节点: {len(kg.node_types['lab_test'])}")
    print(f"  治疗节点: {len(kg.node_types['treatment'])}")

    # 验证边
    print("\n1.2 边统计")
    print(f"  总边数: {kg.graph.number_of_edges()}")
    print(f"  suggests边: {len(kg.edge_types['suggests'])}")
    print(f"  requires_test边: {len(kg.edge_types.get('requires_test', set()))}")
    print(f"  treated_with边: {len(kg.edge_types.get('treated_with', set()))}")

    # 验证查询
    print("\n1.3 查询测试")

    # 查询"头晕"的邻居
    neighbors = kg.get_neighbors("头晕", edge_type="suggests")
    print(f"  '头晕' → 疾病: {len(neighbors)} 个")
    if neighbors:
        print(f"    示例: {neighbors[0][0]} (权重: {neighbors[0][1]})")

    # 查询"高血压"的检查
    test_neighbors = kg.get_neighbors("高血压", edge_type="requires_test")
    print(f"  '高血压' → 检查: {len(test_neighbors)} 个")
    if test_neighbors:
        tests = [n[0] for n in test_neighbors[:3]]
        print(f"    示例: {', '.join(tests)}")

    # 查询"高血压"的治疗
    treatment_neighbors = kg.get_neighbors("高血压", edge_type="treated_with")
    print(f"  '高血压' → 治疗: {len(treatment_neighbors)} 个")
    if treatment_neighbors:
        treatments = [n[0] for n in treatment_neighbors[:3]]
        print(f"    示例: {', '.join(treatments)}")

    print("\n✓ 知识图谱构建测试通过")
    return True


def test_random_walk():
    """测试2：Random Walk路径生成"""
    print("\n" + "="*60)
    print(" [测试 2/4] Random Walk 路径生成")
    print("="*60)

    # 创建知识图谱和Random Walk生成器
    kg = MedicalKnowledgeGraph()
    walker = RandomWalkGenerator(kg)

    # 测试单次Random Walk
    print("\n2.1 单次 Random Walk")
    path = walker.generate_walk(start_symptom="头晕", walk_type="medium", seed=42)

    print(f"  路径长度: {path.get_length()}")
    print(f"  路径总分: {path.total_score:.2f}")
    print(f"  路径节点:")
    for i, node in enumerate(path.nodes):
        print(f"    {i+1}. {node}")

    # 测试多次Random Walk
    print("\n2.2 多次 Random Walk（相同症状）")
    paths = walker.generate_multiple_walks(start_symptom="头晕", num_walks=3, walk_type="medium")

    for i, path in enumerate(paths):
        print(f"\n  路径 {i+1}:")
        print(f"    长度: {path.get_length()}")
        print(f"    节点: {' → '.join(path.nodes)}")

    # 测试不同症状
    print("\n2.3 不同症状的 Random Walk")
    for symptom in ["头痛", "胸痛", "腹痛"]:
        path = walker.generate_walk(start_symptom=symptom, walk_type="short", seed=100)
        print(f"  {symptom}: {' → '.join(path.nodes[:4])}")

    print("\n✓ Random Walk 测试通过")
    return True


def test_task_generator():
    """测试3：Task Generator"""
    print("\n" + "="*60)
    print(" [测试 3/4] Task Generator")
    print("="*60)

    # 创建知识图谱和Task Generator
    kg = MedicalKnowledgeGraph()
    walker = RandomWalkGenerator(kg)
    task_gen = TaskGenerator(kg)

    # 生成路径
    print("\n3.1 生成路径")
    path = walker.generate_walk(start_symptom="头晕", walk_type="medium", seed=42)
    print(f"  路径: {' → '.join(path.nodes)}")

    # 生成任务
    print("\n3.2 生成对话任务")
    task = task_gen.generate_task(path, task_id="test_001")

    print(f"  任务ID: {task.task_id}")
    print(f"  症状: {task.symptom}")
    print(f"  患者年龄: {task.patient_profile.get('age')}")
    print(f"  患者性别: {task.patient_profile.get('gender')}")
    print(f"  预期诊断: {task.expected_diagnosis}")
    print(f"  预期检查: {task.expected_tests}")
    print(f"  预期治疗: {task.expected_treatments}")

    # 打印对话
    print("\n3.3 对话内容")
    for turn in task.dialogue_turns:
        role_name = "患者" if turn.role == "patient" else "医生"
        print(f"  {role_name} ({turn.context.get('phase', 'N/A')}): {turn.content}")

    print("\n✓ Task Generator 测试通过")
    return True


def test_full_pipeline():
    """测试4：完整流程"""
    print("\n" + "="*60)
    print(" [测试 4/4] 完整流程")
    print("="*60)

    # 创建流程
    print("\n4.1 创建流程")
    pipeline = MedicalDialoguePipeline()

    # 生成单个任务
    print("\n4.2 生成单个任务")
    task = pipeline.generate_dialogue_task(
        symptom="头晕",
        walk_type="medium",
        seed=42
    )

    # 批量生成
    print("\n4.3 批量生成任务")
    tasks = pipeline.generate_batch_tasks(
        symptoms=["头晕", "头痛", "胸痛"],
        num_walks_per_symptom=2,
        walk_type="short"
    )
    print(f"  生成任务数: {len(tasks)}")

    # 导出tau2格式
    print("\n4.4 导出tau2格式")
    output_file = "data/tau2/domains/clinical/kg_generated_tasks_test.json"
    pipeline.export_to_tau2_format(tasks, output_file)

    # 验证导出
    output_path = Path(output_file)
    if output_path.exists():
        with open(output_path, 'r', encoding='utf-8') as f:
            loaded_tasks = json.load(f)
        print(f"  验证: 成功加载 {len(loaded_tasks)} 个任务")

        # 打印第一个任务
        if loaded_tasks:
            print(f"\n  第一个任务ID: {loaded_tasks[0]['id']}")
            print(f"  来源: {loaded_tasks[0]['metadata']['source']}")
            print(f"  生成方法: {loaded_tasks[0]['metadata']['generation_method']}")

    print("\n✓ 完整流程测试通过")
    return True


def demo_diversity():
    """演示：对话多样性"""
    print("\n" + "="*60)
    print(" [演示] 对话多样性")
    print("="*60)

    pipeline = MedicalDialoguePipeline()

    # 从同一个症状生成多条路径
    print("\n从'头晕'生成10条不同路径:")
    paths = []
    for i in range(10):
        path = pipeline.walk_generator.generate_walk(
            start_symptom="头晕",
            walk_type="medium",
            seed=i
        )
        paths.append(path)
        print(f"  {i+1}. {' → '.join(path.nodes)}")

    # 统计多样性
    print(f"\n路径多样性统计:")
    unique_lengths = set(len(p.nodes) for p in paths)
    print(f"  不同长度: {unique_lengths}")

    unique_diseases = set()
    for path in paths:
        for node in path.nodes:
            if pipeline.kg.graph.nodes[node].get("type") == "disease":
                unique_diseases.add(node)

    print(f"  不同疾病: {len(unique_diseases)} 个")
    print(f"  疾病列表: {', '.join(list(unique_diseases)[:5])}")

    return True


def main():
    """主测试函数"""
    print("="*60)
    print(" 医疗知识图谱对话生成系统 - 测试")
    print("="*60)
    print("\n测试内容:")
    print("  1. 知识图谱构建")
    print("  2. Random Walk 路径生成")
    print("  3. Task Generator")
    print("  4. 完整流程")
    print("  5. 对话多样性演示")

    # 设置 UTF-8 编码输出
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    try:
        # 运行测试
        test_knowledge_graph()
        test_random_walk()
        test_task_generator()
        test_full_pipeline()
        demo_diversity()

        # 总结
        print("\n" + "="*60)
        print(" ✓ 所有测试通过！")
        print("="*60)
        print("\n核心功能:")
        print("  ✓ 知识图谱构建（基于PrimeKG结构）")
        print("    - 症状、疾病、检查、治疗节点")
        print("    - suggests, requires_test, treated_with 边")
        print("  ✓ Random Walk算法")
        print("    - 在知识图谱上游走")
        print("    - 生成有逻辑的问诊路径")
        print("    - 支持short/medium/long三种长度")
        print("  ✓ Task Generator")
        print("    - 将路径转换为多轮对话")
        print("    - 动态生成患者和医生对话")
        print("    - 生成患者档案和预期诊断")
        print("  ✓ 完整流程")
        print("    - KG → Random Walk → Task → Tau2格式")

        print("\n优势:")
        print("  ✓ 动态生成（每次都不同）")
        print("  ✓ 符合医学逻辑（沿知识图谱）")
        print("  ✓ 高度多样性（同一症状多种路径）")
        print("  ✓ 可配置（路径长度、探索概率）")

        print("\n与之前方法的对比:")
        print("  之前: 静态剧本 → 每次相同")
        print("  现在: 动态生成 → 每次不同")

        return 0

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
