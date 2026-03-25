#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成生成脚本 - 组合使用kg_generator和datagenerator
Integrated Generation Script - Combine kg_generator and datagenerator

功能：
1. 使用kg_generator从知识图谱生成新任务
2. 使用datagenerator优化生成的任务
3. 生成高质量、大规模的数据集
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from medical_task_suite.generation.core.task_generator import KGTaskGenerator
from medical_task_suite.optimization.core.task_optimizer import TaskOptimizer


def integrated_generate(
    symptoms: list = None,
    num_tasks: int = 20,
    walk_type: str = "medium",
    output_file: str = None
):
    """
    集成生成流程

    Args:
        symptoms: 症状关键词列表
        num_tasks: 生成任务数量
        walk_type: 路径类型 (short/medium/long)
        output_file: 输出文件路径
    """
    print("=" * 70)
    print("集成数据生成 - Integrated Data Generation")
    print("=" * 70)

    # 默认症状列表（使用英文，因为PrimeKG是英文知识图谱）
    if symptoms is None:
        symptoms = [
            "headache", "chest pain", "fever", "cough", "nausea",
            "fatigue", "dizziness", "hypertension", "diabetes", "pain"
        ]

    # Step 1: 使用kg_generator生成新任务
    print(f"\n[Step 1/3] 使用kg_generator生成新任务")
    print(f"  症状数量: {len(symptoms)}")
    print(f"  路径类型: {walk_type}")

    try:
        kg_gen = KGTaskGenerator(use_cache=True)
        print(f"  [OK] KG生成器初始化成功")
    except Exception as e:
        print(f"  [FAIL] KG生成器初始化失败: {e}")
        return

    # 生成任务
    generated_tasks = []
    temp_dir = Path("data/primekg_tasks/temp")
    temp_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n  开始生成任务...")
    for i, symptom in enumerate(symptoms[:num_tasks], 1):
        try:
            task = kg_gen.generate(
                symptom_keyword=symptom,
                walk_type=walk_type
            )

            # 转换为tau2格式
            from medical_task_suite.generation.utils.tau2_converter import convert_to_tau2_format
            tau2_task = convert_to_tau2_format(task)

            # 保存临时文件
            temp_file = temp_dir / f"{task.task_id}.json"
            kg_gen.export_to_tau2(task, str(temp_file))

            generated_tasks.append(tau2_task)
            print(f"    [{i:2d}/{num_tasks}] {task.task_id} - {symptom}")

        except Exception as e:
            print(f"    [{i:2d}/{num_tasks}] Skip {symptom}: {str(e)[:50]}")
            continue

    print(f"\n  [OK] 成功生成 {len(generated_tasks)} 个任务")

    if len(generated_tasks) == 0:
        print("  [FAIL] 没有成功生成任何任务")
        return

    # Step 2: 使用datagenerator优化
    print(f"\n[Step 2/3] 使用datagenerator优化任务")
    print(f"  输入任务数: {len(generated_tasks)}")

    try:
        optimizer = TaskOptimizer()
        print(f"  [OK] 优化器初始化成功")
    except Exception as e:
        print(f"  [FAIL] 优化器初始化失败: {e}")
        return

    # 优化任务（不使用文件，直接传入任务列表）
    print(f"\n  开始优化任务...")
    try:
        # 临时保存生成的任务
        temp_input = temp_dir / "generated_tasks.json"
        with open(temp_input, 'w', encoding='utf-8') as f:
            json.dump(generated_tasks, f, ensure_ascii=False, indent=2)

        # 优化
        temp_output = temp_dir / "optimized_tasks.json"
        optimized_tasks = optimizer.optimize(
            input_file=str(temp_input),
            output_file=str(temp_output),
            enable_scenario_balancing=True,
            enable_evaluation_enhancement=True,
            enable_metadata_enrichment=True
        )

        print(f"  [OK] 成功优化 {len(optimized_tasks)} 个任务")

        # 显示优化效果
        stats = optimizer.get_statistics()
        if 'quality_statistics' in stats:
            qs = stats['quality_statistics']
            print(f"\n  质量提升:")
            print(f"    原始: {qs['original_mean']:.2f}")
            print(f"    优化: {qs['optimized_mean']:.2f}")
            print(f"    提升: {qs['quality_improvement']:+.2f}")

    except Exception as e:
        print(f"  [FAIL] 优化失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 3: 保存最终结果
    if output_file is None:
        output_file = "data/tau2/domains/clinical/primekg/tasks_integrated.json"

    print(f"\n[Step 3/3] 保存最终结果")
    print(f"  输出文件: {output_file}")

    try:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(optimized_tasks, f, ensure_ascii=False, indent=2)

        file_size = output_path.stat().st_size / (1024 * 1024)
        print(f"  [OK] 保存成功")
        print(f"  文件大小: {file_size:.2f} MB")

    except Exception as e:
        print(f"  [FAIL] 保存失败: {e}")
        return

    # 清理临时文件
    import shutil
    try:
        shutil.rmtree(temp_dir)
        print(f"\n  [OK] 清理临时文件")
    except:
        pass

    # 总结
    print("\n" + "=" * 70)
    print("集成生成完成!")
    print("=" * 70)
    print(f"\n总结:")
    print(f"  生成任务: {len(generated_tasks)}")
    print(f"  优化任务: {len(optimized_tasks)}")
    print(f"  输出文件: {output_file}")
    print(f"\n优势:")
    print(f"  ✓ 知识驱动 (kg_generator)")
    print(f"  ✓ 质量优化 (datagenerator)")
    print(f"  ✓ 最佳组合")

    return optimized_tasks


def main():
    """主函数"""
    # 配置（使用英文症状关键词）
    symptoms = [
        "headache", "chest pain", "fever", "cough", "nausea",
        "fatigue", "dizziness", "hypertension", "diabetes", "pain",
        "vomiting", "diarrhea", "insomnia", "anxiety", "depression"
    ]

    output_file = "data/tau2/domains/clinical/primekg/tasks_integrated.json"

    # 执行集成生成
    integrated_generate(
        symptoms=symptoms,
        num_tasks=15,
        walk_type="medium",
        output_file=output_file
    )


if __name__ == "__main__":
    main()
