#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据集优化脚本 - 使用DataGenerator优化医学对话数据集
Dataset Optimization Script - Optimize Medical Dialogue Dataset with DataGenerator
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from medical_task_suite.optimization.core.task_optimizer import TaskOptimizer


def main():
    """主函数"""
    print("=" * 70)
    print("数据集优化 - Dataset Optimization")
    print("=" * 70)

    # 配置
    input_file = "data/tau2/domains/clinical/chinese_internal_medicine/tasks_realistic_v3.json"
    output_file = "data/tau2/domains/clinical/chinese_internal_medicine/tasks_optimized.json"
    config_file = "medical_task_suite/optimization/config/optimization_rules.yaml"

    # 初始化优化器
    print(f"\n初始化优化器...")
    print(f"  输入: {input_file}")
    print(f"  输出: {output_file}")
    print(f"  配置: {config_file}")

    try:
        optimizer = TaskOptimizer(config_path=config_file)
        print(f"  [OK] 优化器初始化成功")
    except Exception as e:
        print(f"  [FAIL] 优化器初始化失败: {e}")
        return

    # 执行优化
    try:
        optimized_tasks = optimizer.optimize(
            input_file=input_file,
            output_file=output_file,
            enable_scenario_balancing=True,
            enable_evaluation_enhancement=True,
            enable_metadata_enrichment=True
        )

        print(f"\n✅ 优化完成!")
        print(f"   优化任务数: {len(optimized_tasks)}")
        print(f"   输出文件: {output_file}")

        # 打印统计信息
        stats = optimizer.get_statistics()
        print(f"\n📊 优化统计:")
        print(f"   应用优化: {', '.join(stats.get('optimizations_applied', []))}")

        if 'quality_statistics' in stats:
            quality_stats = stats['quality_statistics']
            print(f"\n   质量提升:")
            print(f"     原始平均分: {quality_stats['original_mean']:.2f}")
            print(f"     优化平均分: {quality_stats['optimized_mean']:.2f}")
            print(f"     提升幅度: {quality_stats['quality_improvement']:+.2f}")

        if 'difficulty_distribution' in stats:
            print(f"\n   难度分布:")
            for diff, count in sorted(stats['difficulty_distribution'].items()):
                pct = count / sum(stats['difficulty_distribution'].values()) * 100
                print(f"     {diff}: {count} ({pct:.1f}%)")

        if 'scenario_statistics' in stats:
            scenario_stats = stats['scenario_statistics']
            if 'optimized_distribution' in scenario_stats:
                print(f"\n   场景分布:")
                for scenario, info in sorted(
                    scenario_stats['optimized_distribution'].items(),
                    key=lambda x: x[1]['percentage'],
                    reverse=True
                )[:6]:  # 显示前6个
                    print(f"     {scenario}: {info['percentage']:.1%}")

    except Exception as e:
        print(f"\n❌ 优化失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
