#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量验证所有科室的原始数据
"""
import json
import subprocess
import sys
from pathlib import Path

# 定义所有科室
departments = [
    {
        "name": "内科",
        "csv_pattern": "./data/raw/medical_dialogues/chinese_meddialog/Data_数据/IM_内科/内科5000-33000.csv",
        "output": "DataQualityFiltering/test_outputs/validation_{dept}.json"
    },
    {
        "name": "外科",
        "csv_pattern": "./data/raw/medical_dialogues/chinese_meddialog/Data_数据/Surgical_外科/外科5-14000.csv",
        "output": "DataQualityFiltering/test_outputs/validation_{dept}.json"
    },
    {
        "name": "妇产科",
        "csv_pattern": "./data/raw/medical_dialogues/chinese_meddialog/Data_数据/OAGD_妇产科/妇产科6-28000.csv",
        "output": "DataQualityFiltering/test_outputs/validation_{dept}.json"
    },
    {
        "name": "儿科",
        "csv_pattern": "./data/raw/medical_dialogues/chinese_meddialog/Data_数据/Pediatric_儿科/儿科5-10000.csv",
        "output": "DataQualityFiltering/test_outputs/validation_{dept}.json"
    },
    {
        "name": "肿瘤科",
        "csv_pattern": "./data/raw/medical_dialogues/chinese_meddialog/Data_数据/Oncology_肿瘤科/肿瘤科5-10000.csv",
        "output": "DataQualityFiltering/test_outputs/validation_{dept}.json"
    },
    {
        "name": "男科",
        "csv_pattern": "./data/raw/medical_dialogues/chinese_meddialog/Data_数据/Andriatria_男科/男科5-14000.csv",
        "output": "DataQualityFiltering/test_outputs/validation_{dept}.json"
    }
]

def validate_department(dept_info):
    """验证单个科室"""
    name = dept_info["name"]
    csv_file = dept_info["csv_pattern"]
    output_file = dept_info["output"].format(dept=name)

    print(f"\n{'='*60}")
    print(f"正在验证: {name}")
    print(f"{'='*60}")

    cmd = [
        "python", "-m", "DataQualityFiltering", "raw-data", "validate",
        "--input", csv_file,
        "--output", output_file,
        "--encoding", "gbk",
        "--strict",
        "--min-patient-length", "20",
        "--min-doctor-length", "30",
        "--min-turns", "2"
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
    print("批量验证所有6个科室")
    print("="*60)

    results = {}

    for dept_info in departments:
        success = validate_department(dept_info)
        results[dept_info["name"]] = success

    # 生成汇总报告
    print("\n" + "="*60)
    print("验证汇总")
    print("="*60)

    for name, success in results.items():
        status = "[成功]" if success else "[失败]"
        print(f"{name}: {status}")

    print("\n生成的验证文件:")
    for dept_info in departments:
        print(f"  - {dept_info['output']}")

    # 保存汇总结果
    summary = {
        "timestamp": "2025-03-19",
        "departments_tested": list(departments),
        "results": results
    }

    summary_file = "DataQualityFiltering/test_outputs/validation_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n汇总结果已保存到: {summary_file}")
    return 0 if all(results.values()) else 1

if __name__ == "__main__":
    sys.exit(main())
