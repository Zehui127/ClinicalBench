#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent Evaluation Pipeline with Multi-threading Support
Agent 评估管道（支持多线程处理）

提供批量评估、进度跟踪、结果统计等功能。
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# 导入本模块的组件
from .evaluators.medical_dimensions import (
    ClinicalAccuracyEvaluator,
    DialogueFluencyEvaluator,
    SafetyEmpathyEvaluator,
)
from .reviewers.medical_agent_reviewer import MedicalAgentReviewer


class AgentEvaluationPipeline:
    """
    Agent 评估管道

    支持批量评估、多线程处理、进度跟踪等功能。
    """

    def __init__(
        self,
        model: str = "gpt-4-turbo",
        max_workers: int = 4,
        cache_dir: Optional[str] = None,
        use_cache: bool = True,
        pass_threshold: float = 3.5,
        save_intermediate: bool = True,
    ):
        """
        初始化评估管道

        Args:
            model: LLM 模型名称
            max_workers: 最大并发数
            cache_dir: 缓存目录
            use_cache: 是否使用缓存
            pass_threshold: 通过阈值
            save_intermediate: 是否保存中间结果
        """
        self.model = model
        self.max_workers = max_workers
        self.cache_dir = cache_dir
        self.use_cache = use_cache
        self.pass_threshold = pass_threshold
        self.save_intermediate = save_intermediate

        # 设置日志
        self.logger = logging.getLogger(__name__)

        # 创建审查器
        self.reviewer = MedicalAgentReviewer(
            model=model,
            cache_dir=cache_dir,
            use_cache=use_cache,
            pass_threshold=pass_threshold,
        )

        # 统计信息
        self.stats = {
            "total": 0,
            "completed": 0,
            "passed": 0,
            "failed": 0,
            "errors": [],
        }

    def evaluate_single(
        self,
        item: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        评估单个项目

        Args:
            item: 评估项目 {
                "task_id": str,
                "patient_question": str,
                "ai_response": str,
                "context_info": str (optional),
                "reference_answer": str (optional),
            }

        Returns:
            评估结果
        """
        try:
            result = self.reviewer.review(
                patient_question=item["patient_question"],
                ai_response=item["ai_response"],
                context_info=item.get("context_info", ""),
                reference_answer=item.get("reference_answer"),
                task_id=item.get("task_id"),
            )

            # 更新统计
            self.stats["completed"] += 1
            if result.get("pass_status", False):
                self.stats["passed"] += 1
            else:
                self.stats["failed"] += 1

            return result

        except Exception as e:
            self.logger.error(f"评估失败 ({item.get('task_id')}): {e}")
            self.stats["errors"].append(str(e))

            return {
                "task_id": item.get("task_id", "unknown"),
                "error": str(e),
                "pass_status": False,
                "overall_score": 0.0,
            }

    def evaluate_batch(
        self,
        items: List[Dict[str, Any]],
        max_workers: Optional[int] = None,
        show_progress: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[Dict[str, Any]]:
        """
        批量评估（多线程）

        Args:
            items: 评估项目列表
            max_workers: 最大并发数（覆盖实例设置）
            show_progress: 是否显示进度
            progress_callback: 进度回调函数

        Returns:
            评估结果列表
        """
        max_workers = max_workers or self.max_workers
        self.stats["total"] = len(items)
        self.stats["completed"] = 0
        self.stats["passed"] = 0
        self.stats["failed"] = 0
        self.stats["errors"] = []

        results = []
        start_time = datetime.now()

        if show_progress:
            self.logger.info(f"开始批量评估: {len(items)} 个项目")
            self.logger.info(f"并发数: {max_workers}")

        # 使用线程池处理
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_item = {
                executor.submit(self.evaluate_single, item): item
                for item in items
            }

            # 收集结果
            for future in as_completed(future_to_item):
                item = future_to_item[future]
                task_id = item.get("task_id", "unknown")

                try:
                    result = future.result()
                    results.append(result)

                    # 更新进度
                    completed = self.stats["completed"]
                    total = self.stats["total"]

                    if show_progress and (completed % 10 == 0 or completed == total):
                        pass_rate = (self.stats["passed"] / completed * 100) if completed > 0 else 0
                        self.logger.info(
                            f"进度: {completed}/{total} ({completed/total*100:.1f}%) | "
                            f"通过: {self.stats['passed']} | "
                            f"失败: {self.stats['failed']} | "
                            f"通过率: {pass_rate:.1f}%"
                        )

                    # 调用进度回调
                    if progress_callback:
                        progress_callback(completed, total)

                except Exception as e:
                    self.logger.error(f"处理结果失败 ({task_id}): {e}")

        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        if show_progress:
            self.logger.info(f"\n批量评估完成:")
            self.logger.info(f"  总数: {len(items)}")
            self.logger.info(f"  通过: {self.stats['passed']}")
            self.logger.info(f"  失败: {self.stats['failed']}")
            self.logger.info(f"  错误: {len(self.stats['errors'])}")
            self.logger.info(f"  耗时: {elapsed:.1f}秒")
            self.logger.info(f"  平均: {elapsed/len(items):.2f}秒/个")

        return results

    def evaluate_from_file(
        self,
        input_file: str,
        output_file: Optional[str] = None,
        max_workers: Optional[int] = None,
        show_progress: bool = True,
    ) -> Dict[str, Any]:
        """
        从文件读取并批量评估

        Args:
            input_file: 输入 JSON 文件路径
            output_file: 输出文件路径（可选）
            max_workers: 最大并发数
            show_progress: 是否显示进度

        Returns:
            评估结果和统计信息
        """
        # 加载数据
        self.logger.info(f"从文件加载数据: {input_file}")

        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 处理不同的数据格式
        if isinstance(data, dict):
            items = data.get("items", data.get("evaluations", []))
        elif isinstance(data, list):
            items = data
        else:
            raise ValueError(f"不支持的数据格式: {type(data)}")

        if not items:
            raise ValueError(f"文件中没有找到评估项目: {input_file}")

        self.logger.info(f"加载了 {len(items)} 个评估项目")

        # 批量评估
        results = self.evaluate_batch(
            items,
            max_workers=max_workers,
            show_progress=show_progress,
        )

        # 生成统计
        stats = self.reviewer.get_statistics(results)

        # 保存结果
        if output_file:
            self.save_results(results, stats, output_file)

        return {
            "results": results,
            "statistics": stats,
        }

    def save_results(
        self,
        results: List[Dict[str, Any]],
        statistics: Dict[str, Any],
        output_file: str,
    ):
        """
        保存评估结果

        Args:
            results: 评估结果列表
            statistics: 统计信息
            output_file: 输出文件路径
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        output_data = {
            "metadata": {
                "model": self.model,
                "pass_threshold": self.pass_threshold,
                "timestamp": datetime.now().isoformat(),
                "total_items": len(results),
            },
            "statistics": statistics,
            "results": results,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        self.logger.info(f"结果已保存到: {output_path}")

    def generate_report(
        self,
        results: List[Dict[str, Any]],
        output_file: Optional[str] = None,
        format: str = "markdown",
    ) -> str:
        """
        生成评估报告

        Args:
            results: 评估结果列表
            output_file: 输出文件路径（可选）
            format: 报告格式（markdown/json）

        Returns:
            报告内容
        """
        stats = self.reviewer.get_statistics(results)

        if format == "markdown":
            report = self._generate_markdown_report(results, stats)
        else:
            report = json.dumps({
                "statistics": stats,
                "results": results,
            }, ensure_ascii=False, indent=2)

        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report)

            self.logger.info(f"报告已保存到: {output_path}")

        return report

    def _generate_markdown_report(
        self,
        results: List[Dict[str, Any]],
        statistics: Dict[str, Any],
    ) -> str:
        """生成 Markdown 格式的报告"""
        lines = []

        lines.append("# Agent 评估报告\n")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        lines.append(f"**模型**: {self.model}\n")

        # 统计摘要
        lines.append("## 📊 统计摘要\n")
        lines.append(f"- **总数**: {statistics['total_reviews']}\n")
        lines.append(f"- **通过**: {statistics['passed']}\n")
        lines.append(f"- **失败**: {statistics['failed']}\n")
        lines.append(f"- **通过率**: {statistics['pass_rate']}%\n")
        lines.append(f"\n**平均分数**:\n")
        lines.append(f"- 临床准确性: {statistics['average_scores']['clinical_accuracy']}/5.0\n")
        lines.append(f"- 对话流畅性: {statistics['average_scores']['dialogue_fluency']}/5.0\n")
        lines.append(f"- 安全性与同理心: {statistics['average_scores']['safety_empathy']}/5.0\n")
        lines.append(f"- 总体: {statistics['average_scores']['overall']}/5.0\n")

        # 分数分布
        lines.append("\n## 📈 分数分布\n")
        dist = statistics['score_distribution']
        lines.append(f"- 优秀 (4.5-5.0): {dist['excellent']}\n")
        lines.append(f"- 良好 (4.0-4.5): {dist['good']}\n")
        lines.append(f"- 满意 (3.5-4.0): {dist['satisfactory']}\n")
        lines.append(f"- 需改进 (3.0-3.5): {dist['needs_improvement']}\n")
        lines.append(f"- 差 (<3.0): {dist['poor']}\n")

        # 详细结果
        lines.append("\n## 📝 详细结果\n")

        for result in results:
            task_id = result.get("task_id", "unknown")
            score = result.get("overall_score", 0)
            passed = result.get("pass_status", False)

            status = "✅" if passed else "❌"
            lines.append(f"\n### {status} {task_id}\n")
            lines.append(f"- **总分**: {score}/5.0\n")

            if "dimension_scores" in result:
                ds = result["dimension_scores"]
                lines.append(f"- **临床准确性**: {ds['clinical_accuracy']}/5.0\n")
                lines.append(f"- **对话流畅性**: {ds['dialogue_fluency']}/5.0\n")
                lines.append(f"- **安全性与同理心**: {ds['safety_empathy']}/5.0\n")

            if result.get("strengths"):
                lines.append(f"- **优点**: {', '.join(result['strengths'])}\n")

            if result.get("weaknesses"):
                lines.append(f"- **不足**: {', '.join(result['weaknesses'])}\n")

            if result.get("errors"):
                lines.append(f"- **错误**: {', '.join(result['errors'])}\n")

            if result.get("comments"):
                lines.append(f"\n{result['comments']}\n")

        return "".join(lines)


# 导出
__all__ = ["AgentEvaluationPipeline"]
