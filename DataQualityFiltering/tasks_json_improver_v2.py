#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tasks.json Improver V2.0
任务改进工具 v2.0 - 真实世界压力测试数据升级

从"理想化模拟数据"升级为"真实世界压力测试数据"

核心改进：
1. 数据维度：增加信息缺失、模糊性、矛盾、干扰信息
2. 对话维度：模拟真实医患互动（打断、情绪变化、复杂对话流）
3. 评估维度：场景化、强制安全门槛

作者：Tau2 Data Quality Team
版本：2.0
日期：2025-03
"""

import json
import random
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent))

from modules.uncertainty_handler import UncertaintyHandler
from modules.complexity_enhancer import ComplexityEnhancer
from modules.scenario_classifier import ScenarioClassifier
from modules.safety_validator import SafetyValidator
from modules.inquiry_threshold_validator import InquiryThresholdValidator


# 改进概率配置
IMPROVEMENT_PROBABILITIES = {
    "add_uncertainty": 0.3,         # 30%任务添加模糊信息
    "add_distraction": 0.25,        # 25%任务添加干扰信息
    "add_contradiction": 0.15,      # 15%任务添加矛盾信息
    "add_emotion_change": 0.35,     # 35%任务添加情绪变化
    "add_interruption": 0.20,       # 20%任务添加打断
    "add_nested_questions": 0.40    # 40%任务添加嵌套问题
}


class TasksJsonImproverV2:
    """
    Tasks.json 改进器 V2.0

    升级策略：
    1. 场景分类：自动识别任务类型
    2. 添加不确定性：模糊信息、矛盾、干扰
    3. 增加复杂性：情绪变化、打断、嵌套问题
    4. 场景化评估：针对不同场景设置不同评估标准
    5. 强制安全门槛：安全警告缺失直接判为不合格
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化改进器 v2.0

        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.probabilities = self.config.get("probabilities", IMPROVEMENT_PROBABILITIES)

        # 初始化模块
        self.uncertainty_handler = UncertaintyHandler(self.config)
        self.complexity_enhancer = ComplexityEnhancer(self.config)
        self.scenario_classifier = ScenarioClassifier(self.config)
        self.safety_validator = SafetyValidator(self.config)
        self.inquiry_threshold_validator = InquiryThresholdValidator(self.config)

        # 统计信息
        self.stats = {
            "total_tasks": 0,
            "improved_tasks": 0,
            "improvements_applied": {
                "uncertainty_added": 0,
                "distraction_added": 0,
                "contradiction_added": 0,
                "emotion_change_added": 0,
                "interruption_added": 0,
                "nested_questions_added": 0,
                "scenario_classified": 0,
                "safety_rules_added": 0,
                "threshold_rules_added": 0
            },
            "scenario_distribution": {},
            "uncertainty_coverage": 0.0,
            "complexity_coverage": 0.0
        }

    def detect_disease_from_text(self, text: str) -> str:
        """
        从文本中检测疾病类型

        Args:
            text: 输入文本

        Returns:
            疾病类型
        """
        disease_keywords = {
            "高血压": ["高血压", "血压", "降压"],
            "糖尿病": ["糖尿病", "血糖", "降糖"],
            "冠心病": ["冠心病", "心脏", "胸痛", "心绞痛"],
            "感冒": ["感冒", "发烧", "咳嗽", "流涕"],
            "胃炎": ["胃", "胃炎", "胃痛", "消化"],
            "头痛": ["头痛", "头晕", "偏头痛"]
        }

        for disease, keywords in disease_keywords.items():
            if any(keyword in text for keyword in keywords):
                return disease

        return "一般疾病"  # 默认

    def improve_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        改进单个任务（v2.0）

        Args:
            task: 原始任务

        Returns:
            改进后的任务
        """
        improved = task.copy()

        # 步骤1：场景分类
        scenario = self.scenario_classifier.classify(improved)
        improved["scenario_type"] = scenario["type"]
        improved["scenario_info"] = scenario
        self.stats["improvements_applied"]["scenario_classified"] += 1

        # 更新场景分布统计
        scenario_type = scenario["type"]
        self.stats["scenario_distribution"][scenario_type] = \
            self.stats["scenario_distribution"].get(scenario_type, 0) + 1

        # 步骤2：添加不确定性（30%任务）
        if random.random() < self.probabilities["add_uncertainty"]:
            improved = self.uncertainty_handler.add_uncertainty(improved)
            self.stats["improvements_applied"]["uncertainty_added"] += 1

        # 步骤3：添加干扰信息（25%任务）
        if random.random() < self.probabilities["add_distraction"]:
            improved = self.uncertainty_handler.add_distraction(improved)
            self.stats["improvements_applied"]["distraction_added"] += 1

        # 步骤4：添加矛盾信息（15%任务）
        if random.random() < self.probabilities["add_contradiction"]:
            improved = self.uncertainty_handler.add_contradiction(improved)
            self.stats["improvements_applied"]["contradiction_added"] += 1

        # 步骤5：添加情绪变化（35%任务）
        if random.random() < self.probabilities["add_emotion_change"]:
            improved = self.complexity_enhancer.add_emotion_transition(improved)
            self.stats["improvements_applied"]["emotion_change_added"] += 1

        # 步骤6：添加打断（20%任务）
        if random.random() < self.probabilities["add_interruption"]:
            improved = self.complexity_enhancer.add_interruption(improved)
            self.stats["improvements_applied"]["interruption_added"] += 1

        # 步骤7：添加嵌套问题（40%任务）
        if random.random() < self.probabilities["add_nested_questions"]:
            improved = self.complexity_enhancer.add_nested_questions(improved)
            self.stats["improvements_applied"]["nested_questions_added"] += 1

        # 步骤8：生成场景特定的评估标准
        scenario_criteria = self.scenario_classifier.generate_scenario_criteria(scenario)
        improved["evaluation_criteria_v2"] = scenario_criteria

        # 步骤9：添加强制安全检查
        safety_rules = self.safety_validator.generate_rules(improved, scenario)
        improved["safety_validation"] = safety_rules
        self.stats["improvements_applied"]["safety_rules_added"] += 1

        # 步骤9.5：添加追问阈值规则（新功能）
        threshold_rules = self.inquiry_threshold_validator.generate_threshold_rules(improved)
        improved["inquiry_threshold_validation"] = threshold_rules
        self.stats["improvements_applied"]["threshold_rules_added"] = \
            self.stats["improvements_applied"].get("threshold_rules_added", 0) + 1

        # 步骤10：添加v2.0质量元数据
        improved["quality_metadata_v2"] = {
            "improvement_version": "2.0",
            "improvement_date": datetime.now().isoformat(),
            "improvement_type": "real_world_stress_test",
            "quality_dimensions": {
                "uncertainty_level": self._calculate_uncertainty_level(improved),
                "complexity_level": self._calculate_complexity_level(improved),
                "safety_criticality": self._calculate_safety_criticality(scenario),
                "realism_score": self._calculate_realism_score(improved)
            },
            "applied_improvements": self._get_applied_improvements(improved)
        }

        # 更新统计
        self.stats["improved_tasks"] += 1

        return improved

    def _calculate_uncertainty_level(self, task: Dict[str, Any]) -> str:
        """计算不确定性等级"""
        uncertainty_markers = task.get("uncertainty_markers", {})
        has_vague = uncertainty_markers.get("has_vague_info", False)
        has_contradiction = uncertainty_markers.get("has_contradiction", False)
        has_distraction = task.get("complexity_features", {}).get("has_distraction", False)

        count = sum([has_vague, has_contradiction, has_distraction])

        if count == 0:
            return "LOW"
        elif count == 1:
            return "MEDIUM"
        else:
            return "HIGH"

    def _calculate_complexity_level(self, task: Dict[str, Any]) -> str:
        """计算复杂性等级"""
        complexity_features = task.get("complexity_features", {})
        has_emotion = complexity_features.get("has_emotion_transition", False)
        has_interruption = complexity_features.get("has_interruption", False)
        nested_count = complexity_features.get("nested_question_count", 0)

        if nested_count > 0:
            return "HIGH"
        elif has_emotion or has_interruption:
            return "MEDIUM"
        else:
            return "LOW"

    def _calculate_safety_criticality(self, scenario: Dict[str, Any]) -> str:
        """计算安全关键性"""
        scenario_type = scenario.get("type", "")
        if scenario_type in ["MEDICATION_CONSULTATION", "SYMPTOM_ANALYSIS", "EMERGENCY_CONCERN"]:
            return "HIGH"
        elif scenario_type in ["CHRONIC_MANAGEMENT"]:
            return "MEDIUM"
        else:
            return "LOW"

    def _calculate_realism_score(self, task: Dict[str, Any]) -> float:
        """计算真实度分数（0-1）"""
        score = 0.5  # 基础分

        uncertainty_markers = task.get("uncertainty_markers", {})
        if uncertainty_markers.get("has_vague_info"):
            score += 0.1
        if uncertainty_markers.get("has_contradiction"):
            score += 0.15

        complexity_features = task.get("complexity_features", {})
        if complexity_features.get("has_emotion_transition"):
            score += 0.1
        if complexity_features.get("has_interruption"):
            score += 0.1
        if complexity_features.get("nested_question_count", 0) > 0:
            score += 0.05

        return min(score, 1.0)

    def _get_applied_improvements(self, task: Dict[str, Any]) -> List[str]:
        """获取已应用的改进列表"""
        applied = []

        uncertainty_markers = task.get("uncertainty_markers", {})
        if uncertainty_markers.get("has_vague_info"):
            applied.append("模糊信息")
        if uncertainty_markers.get("has_contradiction"):
            applied.append("矛盾信息")

        complexity_features = task.get("complexity_features", {})
        if complexity_features.get("has_distraction"):
            applied.append("干扰信息")
        if complexity_features.get("has_emotion_transition"):
            applied.append("情绪变化")
        if complexity_features.get("has_interruption"):
            applied.append("话题打断")
        if complexity_features.get("nested_question_count", 0) > 0:
            applied.append("嵌套问题")

        return applied

    def run(self, input_path: str, output_path: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        运行改进流程

        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            limit: 限制改进的任务数量（用于测试）

        Returns:
            改进结果统计
        """
        print("=" * 80)
        print("Tasks.json 改进工具 V2.0 - 真实世界压力测试数据升级")
        print("=" * 80)
        print(f"输入文件: {input_path}")
        print(f"输出文件: {output_path}")
        print()

        # 创建输出目录
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # 读取原始文件
        print("正在读取输入文件...")
        with open(input_path, 'r', encoding='utf-8') as f:
            tasks = json.load(f)

        self.stats["total_tasks"] = len(tasks)
        print(f"总任务数: {self.stats['total_tasks']}")

        if limit:
            tasks = tasks[:limit]
            print(f"限制改进数量: {limit}")

        print("\n开始改进任务（V2.0 - 真实世界压力测试）...\n")

        # 改进每个任务
        improved_tasks = []
        for i, task in enumerate(tasks, 1):
            task_id = task.get('id', 'unknown')
            print(f"[{i}/{len(tasks)}] 改进任务: {task_id}", end=" ")

            # 场景分类
            scenario = self.scenario_classifier.classify(task)
            print(f"→ 场景: {scenario['name']}", end=" ")

            # 改进任务
            improved_task = self.improve_task(task)
            improved_tasks.append(improved_task)

            # 显示应用的改进
            improvements = improved_task.get("quality_metadata_v2", {}).get("applied_improvements", [])
            if improvements:
                print(f"| 改进: {', '.join(improvements)}")
            else:
                print()

        # 保存改进后的文件
        print(f"\n保存改进后的文件到: {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(improved_tasks, f, indent=2, ensure_ascii=False)

        # 计算覆盖率
        if self.stats["improved_tasks"] > 0:
            self.stats["uncertainty_coverage"] = \
                (self.stats["improvements_applied"]["uncertainty_added"] +
                 self.stats["improvements_applied"]["contradiction_added"]) / self.stats["improved_tasks"]

            self.stats["complexity_coverage"] = \
                (self.stats["improvements_applied"]["emotion_change_added"] +
                 self.stats["improvements_applied"]["interruption_added"] +
                 self.stats["improvements_applied"]["nested_questions_added"]) / self.stats["improved_tasks"]

        # 保存统计报告
        stats_path = Path(output_path).parent / "improvement_statistics_v2.json"
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)

        # 打印统计
        self._print_statistics()

        return {
            "input_path": input_path,
            "output_path": output_path,
            "stats_path": str(stats_path),
            "total_tasks": self.stats["total_tasks"],
            "improved_tasks": self.stats["improved_tasks"],
            "statistics": self.stats
        }

    def _print_statistics(self):
        """打印统计信息"""
        print("\n" + "=" * 80)
        print("改进完成统计 (V2.0)")
        print("=" * 80)
        print(f"总任务数: {self.stats['total_tasks']}")
        print(f"改进任务数: {self.stats['improved_tasks']}")
        print()
        print("应用的改进:")
        for key, value in self.stats["improvements_applied"].items():
            print(f"  - {key}: {value}")
        print()
        print("场景分布:")
        for scenario, count in sorted(self.stats["scenario_distribution"].items()):
            print(f"  - {scenario}: {count}")
        print()
        print(f"不确定性覆盖率: {self.stats['uncertainty_coverage']:.1%}")
        print(f"复杂性覆盖率: {self.stats['complexity_coverage']:.1%}")
        print("=" * 80)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Tasks.json Improver V2.0")
    parser.add_argument(
        "--input",
        default="chinese_internal_medicine_tasks_improved.json",
        help="输入文件路径"
    )
    parser.add_argument(
        "--output",
        default="chinese_internal_medicine_tasks_v2.json",
        help="输出文件路径"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="限制改进的任务数量（用于测试）"
    )

    args = parser.parse_args()

    # 创建改进器
    config = {
        "probabilities": IMPROVEMENT_PROBABILITIES
    }
    improver = TasksJsonImproverV2(config)

    # 运行改进
    result = improver.run(args.input, args.output, args.limit)

    print(f"\n[OK] 改进完成 (V2.0)！")
    print(f"输入文件: {result['input_path']}")
    print(f"输出文件: {result['output_path']}")
    print(f"统计报告: {result['stats_path']}")
    print(f"改进任务数: {result['improved_tasks']}")


if __name__ == "__main__":
    main()
