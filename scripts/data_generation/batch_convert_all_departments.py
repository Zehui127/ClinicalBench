#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量转换所有科室的验证通过数据
"""
import json
import subprocess
import sys
from pathlib import Path

# 定义所有科室
departments = [
    {
        "name": "内科",
        "csv_file": "./data/raw/medical_dialogues/chinese_meddialog/Data_数据/IM_内科/内科5000-33000.csv",
        "validation": "DataQualityFiltering/test_outputs/validation_内科.json",
        "output": "data/processed/medical_dialogues/chinese_meddialog/tasks_内科.json",
        "max_samples": 500
    },
    {
        "name": "外科",
        "csv_file": "./data/raw/medical_dialogues/chinese_meddialog/Data_数据/Surgical_外科/外科5-14000.csv",
        "validation": "DataQualityFiltering/test_outputs/validation_外科.json",
        "output": "data/processed/medical_dialogues/chinese_meddialog/tasks_外科.json",
        "max_samples": 500
    },
    {
        "name": "妇产科",
        "csv_file": "./data/raw/medical_dialogues/chinese_meddialog/Data_数据/OAGD_妇产科/妇产科6-28000.csv",
        "validation": "DataQualityFiltering/test_outputs/validation_妇产科.json",
        "output": "data/processed/medical_dialogues/chinese_meddialog/tasks_妇产科.json",
        "max_samples": 500
    },
    {
        "name": "儿科",
        "csv_file": "./data/raw/medical_dialogues/chinese_meddialog/Data_数据/Pediatric_儿科/儿科5-14000.csv",
        "validation": "DataQualityFiltering/test_outputs/validation_儿科.json",
        "output": "data/processed/medical_dialogues/chinese_meddialog/tasks_儿科.json",
        "max_samples": 500
    },
    {
        "name": "肿瘤科",
        "csv_file": "./data/raw/medical_dialogues/chinese_meddialog/Data_数据/Oncology_肿瘤科/肿瘤科5-10000.csv",
        "validation": "DataQualityFiltering/test_outputs/validation_肿瘤科.json",
        "output": "data/processed/medical_dialogues/chinese_meddialog/tasks_肿瘤科.json",
        "max_samples": 500
    },
    {
        "name": "男科",
        "csv_file": "./data/raw/medical_dialogues/chinese_meddialog/Data_数据/Andriatria_男科/男科5-13000.csv",
        "validation": "DataQualityFiltering/test_outputs/validation_男科.json",
        "output": "data/processed/medical_dialogues/chinese_meddialog/tasks_男科.json",
        "max_samples": 500
    }
]

def convert_department(dept_info):
    """转换单个科室"""
    name = dept_info["name"]

    print(f"\n{'='*60}")
    print(f"正在转换: {name}")
    print(f"{'='*60}")

    cmd = [
        "python", "convert_chinese_meddialog.py",
        "--departments", name,
        "--max-samples", str(dept_info["max_samples"]),
        "--use-validated"
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
    print("批量转换所有6个科室")
    print("="*60)

    results = {}

    for dept_info in departments:
        success = convert_department(dept_info)
        results[dept_info["name"]] = success

    # 生成汇总报告
    print("\n" + "="*60)
    print("转换汇总")
    print("="*60)

    for name, success in results.items():
        status = "[成功]" if success else "[失败]"
        print(f"{name}: {status}")

    print("\n生成的Tasks文件:")
    for dept_info in departments:
        print(f"  - {dept_info['output']}")

    # 保存汇总结果
    summary = {
        "timestamp": "2025-03-19",
        "departments_converted": departments,
        "results": results
    }

    summary_file = "DataQualityFiltering/test_outputs/conversion_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n汇总结果已保存到: {summary_file}")
    return 0 if all(results.values()) else 1

if __name__ == "__main__":
    sys.exit(main())
