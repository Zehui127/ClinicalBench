#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从零生成示例 - 完全不需要原始数据
Generate from Scratch - No Raw Data Needed

这个脚本展示了如何完全从PrimeKG知识图谱生成高质量数据集，
不需要任何原始医学对话数据作为输入。
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from medical_task_suite.generation.core.task_generator import KGTaskGenerator
from medical_task_suite.optimization.core.task_optimizer import TaskOptimizer


def generate_from_scratch(
    symptoms: list = None,
    walk_type: str = "medium",
    output_file: str = "medical_task_suite/examples/data/from_scratch.json"
):
    """
    完全从零生成数据集

    Args:
        symptoms: 症状关键词列表
        walk_type: 路径类型
        output_file: 输出文件路径
    """
    print("=" * 70)
    print("从零生成数据集 - Generate Dataset from Scratch")
    print("=" * 70)

    print("\n✨ 特点:")
    print("  • 不需要原始医学对话数据")
    print("  • 基于PrimeKG知识图谱（哈佛医学院）")
    print("  • 自动生成+优化")
    print("  • 质量保证")

    # 默认症状（使用英文）
    if symptoms is None:
        symptoms = [
            # 症状类
            "headache", "chest pain", "fever", "cough", "nausea",
            "fatigue", "dizziness", "insomnia",

            # 疾病类
            "hypertension", "diabetes", "asthma", "pneumonia",

            # 疼痛类
            "abdominal pain", "back pain", "joint pain",

            # 心理类
            "anxiety", "depression", "stress",

            # 其他
            "skin rash", "constipation", "diarrhea"
        ]

    # Step 1: 从知识图谱生成
    print(f"\n[Step 1/2] 从知识图谱生成任务")
    print(f"  症状数量: {len(symptoms)}")
    print(f"  知识图谱: PrimeKG (23,087节点)")

    try:
        kg_gen = KGTaskGenerator(use_cache=True)
        print(f"  [OK] 初始化成功")
    except Exception as e:
        print(f"  [FAIL] 初始化失败: {e}")
        return None

    # 生成任务
    print(f"\n  生成任务中...")
    generated_tasks = []

    for i, symptom in enumerate(symptoms, 1):
        try:
            task = kg_gen.generate(symptom, walk_type=walk_type)

            # 转换为tau2格式
            from medical_task_suite.generation.utils.tau2_converter import convert_to_tau2_format
            tau2_task = convert_to_tau2_format(task)
            generated_tasks.append(tau2_task)

            print(f"    [{i:2d}/{len(symptoms)}] ✓ {task.task_id} - {symptom}")

        except Exception as e:
            print(f"    [{i:2d}/{len(symptoms)}] ✗ {symptom}: {str(e)[:30]}")
            continue

    print(f"\n  [OK] 成功生成 {len(generated_tasks)} 个任务")

    if len(generated_tasks) == 0:
        print("  [FAIL] 没有成功生成任何任务")
        return None

    # Step 2: 优化质量
    print(f"\n[Step 2/2] 优化任务质量")
    print(f"  输入任务: {len(generated_tasks)}个")

    try:
        # 临时保存
        import json
        temp_dir = Path("data/temp")
        temp_dir.mkdir(parents=True, exist_ok=True)

        temp_input = temp_dir / "generated.json"
        with open(temp_input, 'w', encoding='utf-8') as f:
            json.dump(generated_tasks, f, ensure_ascii=False, indent=2)

        # 优化
        temp_output = temp_dir / "optimized.json"
        optimizer = TaskOptimizer()
        optimized_tasks = optimizer.optimize(
            input_file=str(temp_input),
            output_file=str(temp_output),
            enable_evaluation_enhancement=True,
            enable_metadata_enrichment=True
        )

        print(f"  [OK] 成功优化 {len(optimized_tasks)} 个任务")

        # 显示质量提升
        stats = optimizer.get_statistics()
        if 'quality_statistics' in stats:
            qs = stats['quality_statistics']
            print(f"\n  质量提升:")
            print(f"    原始: {qs['original_mean']:.2f}")
            print(f"    优化: {qs['optimized_mean']:.2f}")
            print(f"    提升: {qs['quality_improvement']:+.2f}")

        # 保存最终结果
        print(f"\n  保存到: {output_file}")
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(optimized_tasks, f, ensure_ascii=False, indent=2)

        file_size = output_path.stat().st_size / 1024
        print(f"  [OK] 保存成功 ({file_size:.1f} KB)")

        # 清理临时文件
        import shutil
        shutil.rmtree(temp_dir)

    except Exception as e:
        print(f"  [FAIL] 优化失败: {e}")
        import traceback
        traceback.print_exc()
        return None

    # 总结
    print("\n" + "=" * 70)
    print("生成完成!")
    print("=" * 70)
    print(f"\n总结:")
    print(f"  生成任务: {len(generated_tasks)}")
    print(f"  优化任务: {len(optimized_tasks)}")
    print(f"  输出文件: {output_file}")
    print(f"\n优势:")
    print(f"  ✓ 完全从零生成")
    print(f"  ✓ 基于真实医学知识")
    print(f"  ✓ 无需原始数据")
    print(f"  ✓ 质量有保证")
    print(f"  ✓ 可无限扩展")

    return optimized_tasks


def main():
    """主函数"""
    print("\n" + "🚀" * 35)
    print("\n从零生成数据集示例")
    print("不需要任何原始医学对话数据！")
    print("\n" + "🚀" * 35 + "\n")

    # 生成
    tasks = generate_from_scratch(
        symptoms=None,  # 使用默认症状
        walk_type="medium",
        output_file="medical_task_suite/examples/data/from_scratch.json"
    )

    if tasks:
        print(f"\n✅ 成功！现在你有了一个完全从知识图谱生成的数据集。")
        print(f"   你可以直接使用它，无需担心数据版权问题。")
    else:
        print(f"\n❌ 生成失败，请检查配置。")


if __name__ == "__main__":
    main()
