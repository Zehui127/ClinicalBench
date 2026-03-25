#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用TaskMerger将3,000个简单任务合并成中等复杂度任务

简化版本：直接实现合并逻辑，避免复杂的导入依赖
"""
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict
from difflib import SequenceMatcher
import re


class SimpleTaskMerger:
    """简化的任务合并器"""

    def __init__(self, merge_min_tasks: int = 2, merge_max_tasks: int = 5):
        """
        Args:
            merge_min_tasks: 最小合并任务数
            merge_max_tasks: 最大合并任务数
        """
        self.merge_min_tasks = merge_min_tasks
        self.merge_max_tasks = merge_max_tasks

        # 风险等级优先级
        self.risk_priority = {
            "MEDICATION_CONSULTATION": 6,
            "SYMPTOM_ANALYSIS": 5,
            "CHRONIC_MANAGEMENT": 4,
            "EMERGENCY_CONCERN": 3,
            "LIFESTYLE_ADVICE": 2,
            "INFORMATION_QUERY": 1,
        }

    def normalize_text(self, text: str) -> str:
        """标准化文本用于比较"""
        if not text:
            return ""
        return " ".join(text.lower().split())

    def text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        norm1 = self.normalize_text(text1)
        norm2 = self.normalize_text(text2)
        return SequenceMatcher(None, norm1, norm2).ratio()

    def extract_significant_words(self, text: str) -> set:
        """提取关键词"""
        if not text:
            return set()

        # 医学停用词
        stopwords = {
            "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
            "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有",
            "看", "好", "自己", "这", "the", "a", "an", "and", "or", "but", "in", "on",
        }

        # 提取中文词汇（简单方法：提取2-4个字符的词）
        words = re.findall(r'[\u4e00-\u9fa5]{2,4}', text.lower())
        return {w for w in words if w not in stopwords}

    def get_task_similarity(self, task1: Dict, task2: Dict) -> float:
        """计算两个任务的相似度"""
        # 1. 场景类型相似度 (权重: 0.3)
        scenario1 = task1.get("scenario_type", "INFORMATION_QUERY")
        scenario2 = task2.get("scenario_type", "INFORMATION_QUERY")
        scenario_sim = 1.0 if scenario1 == scenario2 else 0.5

        # 2. 问题内容相似度 (权重: 0.5)
        ticket1 = task1.get("ticket", "")
        ticket2 = task2.get("ticket", "")
        content_sim = self.text_similarity(ticket1, ticket2)

        # 3. 关键词重叠度 (权重: 0.2)
        words1 = self.extract_significant_words(ticket1)
        words2 = self.extract_significant_words(ticket2)
        if not words1 or not words2:
            word_sim = 0.0
        else:
            intersection = words1 & words2
            union = words1 | words2
            word_sim = len(intersection) / len(union) if union else 0.0

        # 综合相似度
        overall_sim = (
            scenario_sim * 0.3 +
            content_sim * 0.5 +
            word_sim * 0.2
        )

        return overall_sim

    def group_related_tasks(self, tasks: List[Dict]) -> List[List[Dict]]:
        """将相关任务分组"""
        if not tasks:
            return []

        # 按场景类型分组
        scenario_groups = defaultdict(list)
        for task in tasks:
            scenario = task.get("scenario_type", "INFORMATION_QUERY")
            scenario_groups[scenario].append(task)

        # 在每个场景组内，找相似任务
        all_groups = []

        for scenario_type, scenario_tasks in scenario_groups.items():
            # 已经分组的任务索引
            grouped_indices = set()

            for i, task1 in enumerate(scenario_tasks):
                if i in grouped_indices:
                    continue

                # 找到与当前任务相似的其他任务
                similar_tasks = [task1]
                similar_indices = {i}

                for j, task2 in enumerate(scenario_tasks):
                    if j <= i or j in grouped_indices:
                        continue

                    sim = self.get_task_similarity(task1, task2)
                    if sim >= 0.6:  # 相似度阈值（提高到0.6）
                        similar_tasks.append(task2)
                        similar_indices.add(j)
                        grouped_indices.add(j)

                grouped_indices.add(i)
                all_groups.append(similar_tasks)

        return all_groups

    def merge_task_group(self, tasks: List[Dict]) -> Dict:
        """合并一组相关任务"""
        if len(tasks) == 1:
            return tasks[0]

        # 使用第一个任务作为模板
        merged = tasks[0].copy()

        # 生成新ID
        source_ids = [t["id"] for t in tasks]
        merged["id"] = f"merged_{'_'.join(source_ids[:3])}_{len(tasks)}"

        # 合并问题内容
        tickets = [t.get("ticket", "") for t in tasks if t.get("ticket")]
        if len(tickets) > 1:
            merged["ticket"] = f"多问题咨询: {'; '.join(tickets[:3])}"
        else:
            merged["ticket"] = tickets[0] if tickets else ""

        # 合并描述
        merged["description"]["purpose"] = f"Medical consultation - 合并{len(tasks)}个相关问题"

        # 合并user_scenario
        known_infos = []
        for t in tasks:
            known = t.get("user_scenario", {}).get("instructions", {}).get("known_info", "")
            if known:
                known_infos.append(known)

        instructions = merged["user_scenario"]["instructions"]
        if len(known_infos) > 1:
            instructions["known_info"] = " ".join(known_infos)
            instructions["task_instructions"] = (
                f"您有{len(tasks)}个关注点需要咨询：\n" +
                "\n".join([f"{i+1}. {tickets[i]}" for i in range(min(len(tickets), 5))]) +
                "\n\n请向医生详细描述您的症状和顾虑。"
            )

        # 合并追问阈值规则（选择最高风险）
        threshold_rules = self._merge_threshold_rules(tasks)
        merged["inquiry_threshold_validation"] = threshold_rules

        # 合并安全规则
        safety_rules = self._merge_safety_rules(tasks)
        merged["safety_validation"] = safety_rules

        # 更新场景类型（选择最高风险）
        merged["scenario_type"] = self._get_highest_risk_scenario(tasks)

        # 更新元数据
        merged["metadata"]["merged_from"] = source_ids
        merged["metadata"]["merge_count"] = len(tasks)
        merged["metadata"]["difficulty"] = "medium"

        return merged

    def _merge_threshold_rules(self, tasks: List[Dict]) -> Dict:
        """合并追问阈值规则"""
        risk_priority = {
            "HIGH": 3,
            "MEDIUM": 2,
            "LOW": 1,
        }

        # 找最高风险规则
        highest_rule = None
        highest_priority = 0

        for task in tasks:
            rule = task.get("inquiry_threshold_validation", {})
            if not isinstance(rule, dict):
                continue

            risk_level = rule.get("risk_level", "LOW")
            priority = risk_priority.get(risk_level, 0)

            if priority > highest_priority:
                highest_priority = priority
                highest_rule = rule.copy()

        if highest_rule and len(tasks) > 1:
            # 标记为合并任务
            highest_rule["merged_from_multiple"] = True
            highest_rule["source_task_count"] = len(tasks)

            # 提高最小问题数
            if "threshold_config" in highest_rule:
                highest_rule["threshold_config"] = highest_rule["threshold_config"].copy()
                current_min = highest_rule["threshold_config"].get("min_questions_before_advice", 0)
                highest_rule["threshold_config"]["min_questions_before_advice"] = max(current_min + 1, 3)

        return highest_rule or {}

    def _merge_safety_rules(self, tasks: List[Dict]) -> Dict:
        """合并安全规则"""
        all_mandatory = set()
        all_blocking = []

        for task in tasks:
            safety = task.get("safety_validation", {})
            if not isinstance(safety, dict):
                continue

            mandatory = safety.get("mandatory_rules", [])
            if isinstance(mandatory, list):
                all_mandatory.update(mandatory)

            blocking = safety.get("blocking_conditions", [])
            if isinstance(blocking, list):
                all_blocking.extend(blocking)

        return {
            "mandatory_rules": list(all_mandatory),
            "blocking_conditions": all_blocking,
        }

    def _get_highest_risk_scenario(self, tasks: List[Dict]) -> str:
        """获取最高风险场景"""
        highest_scenario = "INFORMATION_QUERY"
        highest_priority = 0

        for task in tasks:
            scenario = task.get("scenario_type", "INFORMATION_QUERY")
            priority = self.risk_priority.get(scenario, 0)
            if priority > highest_priority:
                highest_priority = priority
                highest_scenario = scenario

        return highest_scenario

    def merge_department(self, tasks: List[Dict], dept_name: str) -> List[Dict]:
        """合并单个科室的任务"""
        print(f"\n{'='*60}")
        print(f"合并科室: {dept_name}")
        print(f"{'='*60}")
        print(f"原始任务数: {len(tasks)}")

        # 分组相关任务
        task_groups = self.group_related_tasks(tasks)

        print(f"分组数: {len(task_groups)}")

        # 合并每组
        merged_tasks = []
        stats = {
            "merged_groups": 0,
            "single_tasks": 0,
            "total_original": len(tasks),
        }

        for group in task_groups:
            if len(group) >= self.merge_min_tasks:
                # 合并
                merged = self.merge_task_group(group)
                merged_tasks.append(merged)
                stats["merged_groups"] += 1
            else:
                # 保留原样
                merged_tasks.extend(group)
                stats["single_tasks"] += len(group)

        print(f"合并后任务数: {len(merged_tasks)}")
        print(f"  - 合并任务: {stats['merged_groups']} 个")
        print(f"  - 单独任务: {stats['single_tasks']} 个")
        print(f"减少率: {(1 - len(merged_tasks)/stats['total_original'])*100:.1f}%")

        return merged_tasks

    def merge_all_departments(self, input_dir: str, output_dir: str) -> Dict:
        """合并所有科室"""
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        departments = {
            'enhanced_tasks_内科.json': '内科',
            'enhanced_tasks_外科.json': '外科',
            'enhanced_tasks_妇产科.json': '妇产科',
            'enhanced_tasks_儿科.json': '儿科',
            'enhanced_tasks_肿瘤科.json': '肿瘤科',
            'enhanced_tasks_男科.json': '男科',
        }

        results = {
            "departments": {},
            "total_original": 0,
            "total_merged": 0,
        }

        for filename, dept_name in departments.items():
            input_file = input_path / filename

            if not input_file.exists():
                print(f"警告: 文件不存在 {input_file}")
                continue

            # 读取任务
            with open(input_file, 'r', encoding='utf-8') as f:
                tasks = json.load(f)

            original_count = len(tasks)
            results["total_original"] += original_count

            # 合并
            merged_tasks = self.merge_department(tasks, dept_name)
            merged_count = len(merged_tasks)
            results["total_merged"] += merged_count

            # 保存
            output_file = output_path / f"merged_{dept_name}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(merged_tasks, f, ensure_ascii=False, indent=2)

            results["departments"][dept_name] = {
                "original_count": original_count,
                "merged_count": merged_count,
                "reduction_rate": f"{(1 - merged_count/original_count)*100:.1f}%",
                "output_file": str(output_file)
            }

        return results


def main():
    """主函数"""
    print("="*60)
    print("使用TaskMerger合并3,000个简单任务")
    print("="*60)

    # 创建合并器（调整参数）
    merger = SimpleTaskMerger(
        merge_min_tasks=3,  # 最少合并3个任务（提高）
        merge_max_tasks=5,  # 最多合并5个任务
    )

    # 合并所有科室
    input_dir = "DataQualityFiltering/test_outputs"
    output_dir = "DataQualityFiltering/test_outputs/merged_tasks"

    results = merger.merge_all_departments(input_dir, output_dir)

    # 保存汇总
    summary_file = Path(output_dir) / "merge_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 打印汇总
    print("\n" + "="*60)
    print("合并汇总")
    print("="*60)
    print(f"\n总原始任务: {results['total_original']}")
    print(f"总合并后: {results['total_merged']}")
    print(f"减少率: {(1 - results['total_merged']/results['total_original'])*100:.1f}%")

    print("\n各科室详情:")
    for dept, stats in results["departments"].items():
        print(f"  {dept}: {stats['original_count']} → {stats['merged_count']} ({stats['reduction_rate']})")

    print(f"\n合并结果已保存到: {output_dir}")
    print(f"汇总文件: {summary_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
