#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量增强所有科室的Tasks（添加追问阈值规则）
"""
import json
import subprocess
import sys
from pathlib import Path

# 定义所有科室
departments = [
    {
        "name": "内科",
        "input": "data/processed/medical_dialogues/chinese_meddialog/tasks_内科.json",
        "output": "DataQualityFiltering/test_outputs/enhanced_tasks_内科.json"
    },
    {
        "name": "外科",
        "input": "data/processed/medical_dialogues/chinese_meddialog/tasks_外科.json",
        "output": "DataQualityFiltering/test_outputs/enhanced_tasks_外科.json"
    },
    {
        "name": "妇产科",
        "input": "data/processed/medical_dialogues/chinese_meddialog/tasks_妇产科.json",
        "output": "DataQualityFiltering/test_outputs/enhanced_tasks_妇产科.json"
    },
    {
        "name": "儿科",
        "input": "data/processed/medical_dialogues/chinese_meddialog/tasks_儿科.json",
        "output": "DataQualityFiltering/test_outputs/enhanced_tasks_儿科.json"
    },
    {
        "name": "肿瘤科",
        "input": "data/processed/medical_dialogues/chinese_meddialog/tasks_肿瘤科.json",
        "output": "DataQualityFiltering/test_outputs/enhanced_tasks_肿瘤科.json"
    },
    {
        "name": "男科",
        "input": "data/processed/medical_dialogues/chinese_meddialog/tasks_男科.json",
        "output": "DataQualityFiltering/test_outputs/enhanced_tasks_男科.json"
    }
]

def enhance_department(dept_info):
    """增强单个科室"""
    name = dept_info["name"]
    input_file = dept_info["input"]
    output_file = dept_info["output"]

    print(f"\n{'='*60}")
    print(f"正在增强: {name}")
    print(f"{'='*60}")

    cmd = [
        "python", "DataQualityFiltering/tasks_json_improver_v2.py",
        "--input", input_file,
        "--output", output_file
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        print(result.stdout)
        if result.stderr:
            print("错误:", result.stderr)
        return True
    except Exception as e:
        print(f"错误: {e}")
        return False

def main():
    """主函数"""
    print("="*60)
    print("批量增强所有6个科室的Tasks")
    print("="*60)

    results = {}

    for dept_info in departments:
        success = enhance_department(dept_info)
        results[dept_info["name"]] = success

    # 生成汇总报告
    print("\n" + "="*60)
    print("增强汇总")
    print("="*60)

    for name, success in results.items():
        status = "[成功]" if success else "[失败]"
        print(f"{name}: {status}")

    print("\n生成的增强Tasks文件:")
    for dept_info in departments:
        print(f"  - {dept_info['output']}")

    # 收集统计信息
    print("\n收集增强统计信息...")
    stats = {}
    for dept_info in departments:
        stats_file = dept_info["output"].replace(".json", "_statistics.json")
        try:
            with open(stats_file, 'r', encoding='utf-8') as f:
                stats[dept_info["name"]] = json.load(f)
        except:
            pass

    # 保存汇总结果
    summary = {
        "timestamp": "2025-03-19",
        "departments_enhanced": departments,
        "results": results,
        "statistics": stats
    }

    summary_file = "DataQualityFiltering/test_outputs/enhancement_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n汇总结果已保存到: {summary_file}")

    # 打印统计摘要
    if stats:
        print("\n" + "="*60)
        print("增强统计摘要")
        print("="*60)
        for name, stat in stats.items():
            total = stat.get("total_tasks", 0)
            improved = stat.get("improved_tasks", 0)
            scenarios = stat.get("improvements_applied", {}).get("scenario_classified", 0)
            print(f"{name}:")
            print(f"  总任务: {total}")
            print(f"  已增强: {improved}")
            print(f"  场景分类: {scenarios}")
            print()

    return 0 if all(results.values()) else 1

if __name__ == "__main__":
    sys.exit(main())
