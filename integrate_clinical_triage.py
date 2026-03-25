#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将临床分诊模块集成到合并任务中

对1,476个合并后的任务应用临床分诊功能
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from DataQualityFiltering.modules.clinical_triage import (
    EnhancedInquiryThresholdValidator,
    analyze_patient_questions
)


class ClinicalTriageIntegrator:
    """临床分诊集成器"""

    def __init__(self):
        self.validator = EnhancedInquiryThresholdValidator()

    def enhance_merged_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        增强合并任务，添加临床分诊功能

        Args:
            task: 原始任务

        Returns:
            增强后的任务
        """
        # 检查是否是合并任务
        merge_count = task.get("metadata", {}).get("merge_count", 1)

        if merge_count <= 1:
            # 单个任务，添加基础分诊规则
            return self._add_basic_triage(task)
        else:
            # 合并任务，添加完整分诊规则
            return self._add_full_triage(task)

    def _add_basic_triage(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """添加基础分诊规则"""
        # 使用原有的追问阈值规则
        return task

    def _add_full_triage(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """添加完整分诊规则"""
        # 获取患者问题和当前科室
        ticket = task.get("ticket", "")
        current_dept = task.get("metadata", {}).get("department_cn", "内科")

        # 生成增强的分诊规则
        triage_rules = analyze_patient_questions(ticket, current_dept)

        # 替换原有的追问阈值规则
        task["inquiry_threshold_validation"] = triage_rules

        # 添加分诊元数据
        task["metadata"]["clinical_triage"] = {
            "enabled": True,
            "multi_department": triage_rules.get("scenario_type") == "MULTI_DEPARTMENT_CONSULTATION",
            "dept_count": len(set(
                [r["target_dept"] for r in triage_rules.get("referral_recommendations", [])] +
                [current_dept]
            )),
            "referral_count": len(triage_rules.get("referral_recommendations", [])),
        }

        return task

    def process_department(self, input_file: Path, output_file: Path) -> Dict[str, Any]:
        """
        处理单个科室的任务

        Args:
            input_file: 输入文件
            output_file: 输出文件

        Returns:
            处理统计
        """
        # 读取任务
        with open(input_file, 'r', encoding='utf-8') as f:
            tasks = json.load(f)

        print(f"\n处理科室: {input_file.stem}")
        print(f"  任务数: {len(tasks)}")

        stats = {
            "total_tasks": len(tasks),
            "merged_tasks": 0,
            "multi_dept_tasks": 0,
            "single_dept_tasks": 0,
            "referral_tasks": 0,
        }

        # 增强每个任务
        enhanced_tasks = []
        for task in tasks:
            enhanced_task = self.enhance_merged_task(task)
            enhanced_tasks.append(enhanced_task)

            # 统计
            merge_count = enhanced_task.get("metadata", {}).get("merge_count", 1)
            if merge_count > 1:
                stats["merged_tasks"] += 1

            triage_info = enhanced_task.get("metadata", {}).get("clinical_triage", {})
            if triage_info.get("enabled"):
                if triage_info.get("multi_department"):
                    stats["multi_dept_tasks"] += 1
                else:
                    stats["single_dept_tasks"] += 1

                if triage_info.get("referral_count", 0) > 0:
                    stats["referral_tasks"] += 1

        # 保存结果
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(enhanced_tasks, f, ensure_ascii=False, indent=2)

        print(f"  合并任务: {stats['merged_tasks']}")
        print(f"  多科室任务: {stats['multi_dept_tasks']}")
        print(f"  单科室任务: {stats['single_dept_tasks']}")
        print(f"  需要转诊: {stats['referral_tasks']}")
        print(f"  保存到: {output_file}")

        return stats

    def process_all_departments(self, input_dir: str, output_dir: str) -> Dict[str, Any]:
        """
        处理所有科室

        Args:
            input_dir: 输入目录
            output_dir: 输出目录

        Returns:
            处理结果
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        departments = {
            'merged_内科.json': '内科',
            'merged_外科.json': '外科',
            'merged_妇产科.json': '妇产科',
            'merged_儿科.json': '儿科',
            'merged_肿瘤科.json': '肿瘤科',
            'merged_男科.json': '男科',
        }

        results = {
            "departments": {},
            "total_tasks": 0,
            "total_merged": 0,
            "total_multi_dept": 0,
            "total_referral": 0,
        }

        for filename, dept_name in departments.items():
            input_file = input_path / filename
            output_file = output_path / filename.replace('.json', '_triaged.json')

            if not input_file.exists():
                print(f"警告: 文件不存在 {input_file}")
                continue

            # 处理科室
            stats = self.process_department(input_file, output_file)

            results["departments"][dept_name] = stats
            results["total_tasks"] += stats["total_tasks"]
            results["total_merged"] += stats["merged_tasks"]
            results["total_multi_dept"] += stats["multi_dept_tasks"]
            results["total_referral"] += stats["referral_tasks"]

        return results


def main():
    """主函数"""
    print("="*60)
    print("将临床分诊功能集成到合并任务")
    print("="*60)

    # 创建集成器
    integrator = ClinicalTriageIntegrator()

    # 处理所有科室
    input_dir = "DataQualityFiltering/test_outputs/merged_tasks"
    output_dir = "DataQualityFiltering/test_outputs/triaged_tasks"

    results = integrator.process_all_departments(input_dir, output_dir)

    # 保存汇总
    summary_file = Path(output_dir) / "triage_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 打印汇总
    print("\n" + "="*60)
    print("集成汇总")
    print("="*60)
    print(f"\n总任务数: {results['total_tasks']}")
    print(f"合并任务: {results['total_merged']}")
    print(f"多科室任务: {results['total_multi_dept']}")
    print(f"需要转诊: {results['total_referral']}")

    print("\n各科室详情:")
    for dept, stats in results["departments"].items():
        print(f"  {dept}:")
        print(f"    总任务: {stats['total_tasks']}")
        print(f"    多科室: {stats['multi_dept_tasks']}")
        print(f"    需转诊: {stats['referral_tasks']}")

    print(f"\n增强后的任务已保存到: {output_dir}")
    print(f"汇总文件: {summary_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
