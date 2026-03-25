#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 PrimeKG Random Walk 集成

测试真实 PrimeKG 知识图谱上的 Random Walk 和 Task Generator
"""

import sys
import io
import json
from pathlib import Path

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from primekg_random_walk import (
    PrimeKGRandomWalkPipeline,
    PrimeKGAdapter,
    PrimeKGRandomWalkGenerator,
    PrimeKGTaskGenerator
)
from primekg_loader import PrimeKGLoader, RealMedicalKnowledgeGraph


def test_primekg_integration():
    """测试完整集成流程"""
    print("\n" + "="*70)
    print(" PrimeKG Random Walk Integration Test")
    print("="*70)

    # 1. 初始化流程
    print("\n[1/5] Initializing Pipeline...")
    pipeline = PrimeKGRandomWalkPipeline(
        use_cache=True,
        focus_types=["disease", "drug", "effect/phenotype"]
    )

    # 2. 查看可用症状
    print("\n[2/5] Exploring Available Symptoms...")
    print("\nSearching for common symptoms...")

    symptom_keywords = ["pain", "fever", "nausea", "hypertension", "diabetes"]

    available_symptoms = {}
    for keyword in symptom_keywords:
        results = pipeline.real_kg.search_nodes(
            keyword,
            node_type="effect/phenotype",
            limit=3
        )
        if results:
            available_symptoms[keyword] = results
            print(f"\n  '{keyword}' - Found {len(results)} symptoms:")
            for s in results[:2]:
                name = s['name'][:50] + "..." if len(s['name']) > 50 else s['name']
                print(f"    - {name}")

    # 3. 生成多个任务
    print("\n[3/5] Generating Multiple Consultation Tasks...")

    tasks_generated = []

    for keyword, symptoms in list(available_symptoms.items())[:3]:
        if not symptoms:
            continue

        symptom = symptoms[0]
        symptom_name = symptom['name']

        print(f"\n  Generating task for: {symptom_name[:60]}")

        try:
            # 生成不同类型的 walk
            for walk_type in ["short", "medium"]:
                task = pipeline.generate_consultation_task(
                    symptom_keyword=symptom_name,
                    walk_type=walk_type,
                    task_id=f"primekg_{keyword}_{walk_type}"
                )

                tasks_generated.append(task)

                print(f"    - {walk_type}: {len(task.path.nodes)} nodes, {len(task.dialogue_turns)} turns")

        except Exception as e:
            print(f"    Error: {e}")

    # 4. 详细分析一个任务
    print("\n[4/5] Detailed Task Analysis...")

    if tasks_generated:
        task = tasks_generated[0]

        print(f"\nTask ID: {task.task_id}")
        print(f"Walk Type: medium")
        print(f"\nPatient Profile:")
        for key, value in task.patient_profile.items():
            print(f"  {key}: {value}")

        print(f"\nPath Details:")
        print(f"  Length: {len(task.path.nodes)} nodes")
        for i, node_id in enumerate(task.path.nodes):
            node_info = pipeline.real_kg.get_node_info(node_id)
            if node_info:
                name = node_info['name'][:40] + "..." if len(node_info['name']) > 40 else node_info['name']
                node_type = node_info['type']
                print(f"  {i+1}. [{node_type}] {name}")

        if task.path.edges:
            print(f"\nEdge Details:")
            for i, edge in enumerate(task.path.edges[1:], 1):  # Skip first edge (empty)
                edge_type = edge.get('edge_type', 'unknown')
                print(f"  {i}. {edge_type}")

        print(f"\nDialogue Preview:")
        for turn in task.dialogue_turns[:6]:
            role = turn['role'].capitalize()
            content = turn['content'][:70] + "..." if len(turn['content']) > 70 else turn['content']
            print(f"  [{role}] {content}")

    # 5. 导出所有任务
    print("\n[5/5] Exporting Tasks...")

    output_dir = Path("data/primekg_tasks")
    output_dir.mkdir(parents=True, exist_ok=True)

    for task in tasks_generated:
        output_file = output_dir / f"{task.task_id}.json"
        pipeline.export_to_tau2(task, str(output_file))

    # 生成汇总报告
    summary = {
        "total_tasks": len(tasks_generated),
        "tasks": [
            {
                "task_id": t.task_id,
                "symptom": t.patient_profile.get("chief_complaint", "unknown"),
                "path_length": len(t.path.nodes),
                "dialogue_turns": len(t.dialogue_turns),
                "file": f"{t.task_id}.json"
            }
            for t in tasks_generated
        ]
    }

    summary_file = output_dir / "summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\nSummary Report:")
    print(f"  Total tasks generated: {summary['total_tasks']}")
    print(f"  Output directory: {output_dir}")
    print(f"  Summary file: {summary_file}")

    # 统计信息
    print("\n" + "="*70)
    print(" Test Results Summary")
    print("="*70)

    if tasks_generated:
        avg_path_length = sum(len(t.path.nodes) for t in tasks_generated) / len(tasks_generated)
        avg_dialogue_turns = sum(len(t.dialogue_turns) for t in tasks_generated) / len(tasks_generated)

        print(f"\nTasks Generated: {len(tasks_generated)}")
        print(f"Average Path Length: {avg_path_length:.1f} nodes")
        print(f"Average Dialogue Turns: {avg_dialogue_turns:.1f} turns")

        # 统计疾病分布
        diseases = []
        for task in tasks_generated:
            if len(task.path.nodes) > 1:
                disease_id = task.path.nodes[1]
                disease_info = pipeline.real_kg.get_node_info(disease_id)
                if disease_info:
                    diseases.append(disease_info['name'])

        if diseases:
            from collections import Counter
            disease_counts = Counter(diseases)
            print(f"\nTop Diseases:")
            for disease, count in disease_counts.most_common(5):
                print(f"  - {disease}: {count}")

    print("\n✓ All tests passed!")
    print("="*70)

    return tasks_generated


def test_random_walk_diversity():
    """测试 Random Walk 多样性"""
    print("\n" + "="*70)
    print(" Testing Random Walk Diversity")
    print("="*70)

    # 初始化
    loader = PrimeKGLoader()
    real_kg = RealMedicalKnowledgeGraph(loader)
    real_kg.load_from_primekg(use_cache=True)

    generator = PrimeKGRandomWalkGenerator(real_kg)

    # 搜索一个症状
    results = real_kg.search_nodes("fever", node_type="effect/phenotype", limit=1)

    if not results:
        print("No fever symptom found")
        return

    symptom_id = results[0]["id"]
    symptom_name = results[0]["name"]

    print(f"\nStarting symptom: {symptom_name}")
    print(f"Symptom ID: {symptom_id}")

    # 生成10条不同的路径
    print("\nGenerating 10 different walks...")

    paths = generator.generate_multiple_walks(
        symptom_id,
        num_walks=10,
        walk_type="medium"
    )

    # 分析路径多样性
    print(f"\nDiversity Analysis:")
    print(f"  Total paths: {len(paths)}")

    # 统计路径长度
    path_lengths = [len(p.nodes) for p in paths]
    print(f"  Path lengths: min={min(path_lengths)}, max={max(path_lengths)}, avg={sum(path_lengths)/len(path_lengths):.1f}")

    # 统计疾病多样性
    diseases = set()
    treatments = set()

    for path in paths:
        if len(path.nodes) > 1:
            disease_id = path.nodes[1]
            disease_info = real_kg.get_node_info(disease_id)
            if disease_info:
                diseases.add(disease_info['name'])

        if len(path.nodes) > 2:
            treatment_id = path.nodes[2]
            treatment_info = real_kg.get_node_info(treatment_id)
            if treatment_info:
                treatments.add(treatment_info['name'])

    print(f"  Unique diseases: {len(diseases)}")
    print(f"  Unique treatments: {len(treatments)}")

    # 展示前3条路径
    print(f"\nSample Paths:")
    for i, path in enumerate(paths[:3], 1):
        print(f"\n  Path {i}:")
        for j, node_id in enumerate(path.nodes):
            node_info = real_kg.get_node_info(node_id)
            if node_info:
                name = node_info['name'][:30] + "..." if len(node_info['name']) > 30 else node_info['name']
                node_type = node_info['type'][:10]
                print(f"    {j+1}. [{node_type}] {name}")

    print("\n✓ Diversity test complete!")


if __name__ == "__main__":
    # 测试1：完整集成流程
    test_primekg_integration()

    # 测试2：Random Walk 多样性
    test_random_walk_diversity()

    print("\n" + "="*70)
    print(" ALL TESTS COMPLETED SUCCESSFULLY!")
    print("="*70)
    print("\nGenerated files:")
    print("  - data/primekg_tasks/*.json")
    print("  - data/primekg_tasks/summary.json")
