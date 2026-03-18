#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quality Threshold Pipeline
质量阈值筛选管道

整合评分、分级、改进功能，实现完整的质量阈值筛选流程。
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import logging
from datetime import datetime

try:
    from .scoring import ExtendedScoringSystem, ScoringConfig
    from .quality_classifier import QualityClassifier, QualityClassificationResult
    from .improver import TaskImprover, ImprovementResult
except ImportError:
    from scoring import ExtendedScoringSystem, ScoringConfig
    from quality_classifier import QualityClassifier, QualityClassificationResult
    from improver import TaskImprover, ImprovementResult


class QualityThresholdPipeline:
    """
    质量阈值筛选管道

    完整流程：
    1. 加载任务
    2. 评分和分级
    3. 分流处理（保留/改进/拒绝）
    4. 生成统计报告
    5. 保存结果
    """

    def __init__(
        self,
        config: Optional[ScoringConfig] = None,
        enable_improvement: bool = True,
        output_dir: str = "./outputs/quality_threshold"
    ):
        """
        初始化管道

        Args:
            config: 评分配置
            enable_improvement: 是否启用自动改进
            output_dir: 输出目录
        """
        self.config = config or ScoringConfig()
        self.enable_improvement = enable_improvement
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 初始化组件
        self.scoring_system = ExtendedScoringSystem(self.config)
        self.classifier = QualityClassifier(self.scoring_system)
        self.improver = TaskImprover(self.scoring_system) if enable_improvement else None

        # 设置日志
        self.logger = logging.getLogger(__name__)

    def run(
        self,
        tasks: List[Dict[str, Any]],
        scores_list: Optional[List[Dict[str, float]]] = None,
        original_scores_list: Optional[List[Dict[str, float]]] = None
    ) -> Dict[str, Any]:
        """
        运行完整的质量阈值筛选管道

        Args:
            tasks: 任务列表
            scores_list: 预计算的扩展分数列表（可选，如果为 None 则跳过评分）
            original_scores_list: 预计算的原始分数列表（可选）

        Returns:
            管道结果 {
                "high_quality": List[dict],
                "medium_quality_improved": List[dict],
                "medium_quality_failed": List[dict],
                "low_quality": List[dict],
                "statistics": dict,
                "classifications": List[QualityClassificationResult],
                "improvements": List[ImprovementResult]
            }
        """
        self.logger.info("=" * 60)
        self.logger.info("质量阈值筛选管道")
        self.logger.info("=" * 60)
        self.logger.info(f"任务数量: {len(tasks)}")
        self.logger.info(f"启用改进: {self.enable_improvement}")

        # 如果没有提供分数，假设所有任务需要评分
        # 这里简化处理：使用默认分数或从任务中提取
        if scores_list is None:
            self.logger.warning("未提供分数列表，将使用默认分数")
            scores_list = [self._get_default_scores() for _ in tasks]

        if original_scores_list is None:
            original_scores_list = scores_list

        # 步骤 1: 批量分级
        self.logger.info("\n步骤 1: 质量分级...")
        classifications = self._classify_tasks(tasks, scores_list, original_scores_list)

        # 步骤 2: 分流处理
        self.logger.info("\n步骤 2: 分流处理...")
        results = self._process_tasks(
            tasks,
            classifications,
            scores_list,
            original_scores_list
        )

        # 步骤 3: 生成统计
        self.logger.info("\n步骤 3: 生成统计...")
        statistics = self._generate_statistics(results, classifications)

        # 步骤 4: 保存结果
        self.logger.info("\n步骤 4: 保存结果...")
        self._save_results(results, statistics, classifications)

        # 添加统计和分级到结果
        results["statistics"] = statistics
        results["classifications"] = [c.__dict__ for c in classifications]
        results["improvements"] = [i.__dict__ for i in results.get("improvement_results", [])]

        # 打印总结
        self._print_summary(statistics)

        return results

    def _get_default_scores(self) -> Dict[str, float]:
        """获取默认分数（用于测试）"""
        return {
            "clinical_accuracy": 7.0,
            "scenario_realism": 6.0,
            "evaluation_completeness": 5.0,
            "difficulty_appropriateness": 4.0
        }

    def _classify_tasks(
        self,
        tasks: List[Dict[str, Any]],
        scores_list: List[Dict[str, float]],
        original_scores_list: List[Dict[str, float]]
    ) -> List[QualityClassificationResult]:
        """批量分级任务"""
        return self.classifier.batch_classify(tasks, scores_list, original_scores_list)

    def _process_tasks(
        self,
        tasks: List[Dict[str, Any]],
        classifications: List[QualityClassificationResult],
        scores_list: List[Dict[str, float]],
        original_scores_list: List[Dict[str, float]]
    ) -> Dict[str, Any]:
        """分流处理任务"""
        results = {
            "high_quality": [],
            "medium_quality_improved": [],
            "medium_quality_failed": [],
            "low_quality": [],
            "improvement_results": []
        }

        for task, classification in zip(tasks, classifications):
            if classification.action == "KEEP":
                # 高质量：保留
                results["high_quality"].append(task)

            elif classification.action == "IMPROVE":
                # 中等质量：尝试改进
                if self.improver:
                    improvement_result = self.improver.improve_medium_quality_task(
                        task, classification
                    )
                    results["improvement_results"].append(improvement_result)

                    if improvement_result.success:
                        results["medium_quality_improved"].append({
                            "task": improvement_result.improved_task,
                            "original_score": improvement_result.original_score,
                            "improved_score": improvement_result.improved_score
                        })
                    else:
                        results["medium_quality_failed"].append({
                            "task": improvement_result.improved_task,
                            "original_score": improvement_result.original_score,
                            "improved_score": improvement_result.improved_score
                        })
                else:
                    # 未启用改进，视为失败
                    results["medium_quality_failed"].append({
                        "task": task,
                        "original_score": classification.total_score,
                        "improved_score": classification.total_score
                    })

            else:  # REJECT
                # 低质量：拒绝
                results["low_quality"].append(task)

        return results

    def _generate_statistics(
        self,
        results: Dict[str, Any],
        classifications: List[QualityClassificationResult]
    ) -> Dict[str, Any]:
        """生成统计信息"""
        # 基础统计
        stats = self.classifier.generate_statistics(classifications)

        # 改进统计
        improvement_results = results.get("improvement_results", [])
        if improvement_results:
            successful = sum(1 for r in improvement_results if r.success)
            failed = len(improvement_results) - successful
            avg_score_delta = sum(r.score_delta for r in improvement_results) / len(improvement_results)

            stats["improvement"] = {
                "total": len(improvement_results),
                "successful": successful,
                "failed": failed,
                "success_rate": round(successful / len(improvement_results) * 100, 2),
                "average_score_delta": round(avg_score_delta, 2)
            }

        return stats

    def _save_results(
        self,
        results: Dict[str, Any],
        statistics: Dict[str, Any],
        classifications: List[QualityClassificationResult]
    ):
        """保存结果到文件"""
        # 保存高质量任务
        self._save_json(
            results["high_quality"],
            self.output_dir / "tasks_high_quality.json"
        )

        # 保存改进成功的中等质量任务
        improved_tasks = [r["task"] for r in results["medium_quality_improved"]]
        self._save_json(
            improved_tasks,
            self.output_dir / "tasks_improved.json"
        )

        # 保存改进失败的中等质量任务
        failed_tasks = [r["task"] for r in results["medium_quality_failed"]]
        self._save_json(
            failed_tasks,
            self.output_dir / "tasks_failed_improvement.json"
        )

        # 保存低质量任务
        self._save_json(
            results["low_quality"],
            self.output_dir / "tasks_low_quality.json"
        )

        # 保存统计报告
        self._save_json(
            statistics,
            self.output_dir / "quality_statistics.json"
        )

        # 保存详细分级结果
        classifications_dict = [c.__dict__ for c in classifications]
        self._save_json(
            classifications_dict,
            self.output_dir / "quality_classifications.json"
        )

        self.logger.info(f"\n结果已保存到: {self.output_dir}")

    def _save_json(self, data: Any, path: Path):
        """保存数据到 JSON 文件"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _print_summary(self, statistics: Dict[str, Any]):
        """打印统计摘要"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("质量阈值筛选完成")
        self.logger.info("=" * 60)
        self.logger.info(f"总任务数: {statistics['total_tasks']}")
        self.logger.info(f"高质量 (保留): {statistics['high_quality']}")
        self.logger.info(f"中等质量: {statistics['medium_quality']}")
        self.logger.info(f"低质量 (拒绝): {statistics['low_quality']}")
        self.logger.info(f"平均分数: {statistics['average_score']}/30")

        if "improvement" in statistics:
            imp = statistics["improvement"]
            self.logger.info(f"\n改进统计:")
            self.logger.info(f"  总改进数: {imp['total']}")
            self.logger.info(f"  成功提升到高质量: {imp['successful']}")
            self.logger.info(f"  仍然中等质量: {imp['failed']}")
            self.logger.info(f"  成功率: {imp['success_rate']}%")
            self.logger.info(f"  平均提升分数: {imp['average_score_delta']:+.2f}")

        self.logger.info("=" * 60)


def test_quality_threshold_pipeline():
    """测试质量阈值筛选管道"""
    # 创建测试任务
    test_tasks = [
        {
            "id": "task_001",
            "description": "高质量任务",
            "clinical_scenario": "患者胸痛，完整病史"
        },
        {
            "id": "task_002",
            "description": "中等质量任务",
            "clinical_scenario": "患者头痛"
        },
        {
            "id": "task_003",
            "description": "低质量任务",
            "clinical_scenario": "患者不舒服"
        }
    ]

    # 创建测试分数
    scores_list = [
        # 高质量
        {
            "clinical_accuracy": 9.0,
            "scenario_realism": 7.0,
            "evaluation_completeness": 6.0,
            "difficulty_appropriateness": 5.0
        },
        # 中等质量
        {
            "clinical_accuracy": 7.5,
            "scenario_realism": 6.0,
            "evaluation_completeness": 5.0,
            "difficulty_appropriateness": 4.0
        },
        # 低质量
        {
            "clinical_accuracy": 5.0,
            "scenario_realism": 4.0,
            "evaluation_completeness": 4.0,
            "difficulty_appropriateness": 3.0
        }
    ]

    # 创建管道
    pipeline = QualityThresholdPipeline(
        enable_improvement=True,
        output_dir="./test_outputs/quality_threshold"
    )

    # 运行管道
    results = pipeline.run(test_tasks, scores_list)

    print("\n管道运行完成！")
    print(f"高质量任务: {len(results['high_quality'])}")
    print(f"改进成功: {len(results['medium_quality_improved'])}")
    print(f"改进失败: {len(results['medium_quality_failed'])}")
    print(f"低质量任务: {len(results['low_quality'])}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    test_quality_threshold_pipeline()
