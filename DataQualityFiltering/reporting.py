#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quality Report Generator
质量报告生成器

生成详细的质量统计报告和可视化图表。
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import json
from datetime import datetime


class QualityReportGenerator:
    """
    质量报告生成器

    生成统计报告、可视化图表和 HTML 报告。
    """

    def __init__(self, output_dir: str = "./outputs/quality_reports"):
        """
        初始化报告生成器

        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_comprehensive_report(
        self,
        results: Dict[str, Any],
        statistics: Dict[str, Any],
        classifications: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        生成综合报告

        Args:
            results: 管道结果
            statistics: 统计信息
            classifications: 分级结果列表

        Returns:
            生成的报告文件路径字典
        """
        report_files = {}

        # 1. 生成 JSON 报告
        json_report = self._generate_json_report(results, statistics, classifications)
        json_path = self.output_dir / "quality_report.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_report, f, indent=2, ensure_ascii=False)
        report_files["json"] = str(json_path)

        # 2. 生成 Markdown 报告
        md_report = self._generate_markdown_report(results, statistics, classifications)
        md_path = self.output_dir / "quality_report.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_report)
        report_files["markdown"] = str(md_path)

        # 3. 生成 HTML 报告
        html_report = self._generate_html_report(results, statistics, classifications)
        html_path = self.output_dir / "quality_report.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_report)
        report_files["html"] = str(html_path)

        # 4. 尝试生成可视化图表（需要 matplotlib）
        try:
            viz_paths = self._generate_visualizations(statistics)
            report_files["visualizations"] = viz_paths
        except ImportError:
            # matplotlib 不可用，跳过可视化
            pass

        return report_files

    def _generate_json_report(
        self,
        results: Dict[str, Any],
        statistics: Dict[str, Any],
        classifications: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """生成 JSON 格式的报告"""
        return {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_tasks": statistics["total_tasks"],
                "scoring_system": "0-30 point scale",
                "thresholds": {
                    "high": 27.0,
                    "medium": 24.0
                }
            },
            "summary": {
                "high_quality": statistics["high_quality"],
                "medium_quality": statistics["medium_quality"],
                "low_quality": statistics["low_quality"],
                "keep": statistics["keep"],
                "improve": statistics["improve"],
                "reject": statistics["reject"],
                "average_score": statistics["average_score"],
                "pass_rate": statistics["pass_rate"]
            },
            "score_distribution": statistics["score_distribution"],
            "improvement": statistics.get("improvement", {}),
            "tasks": classifications
        }

    def _generate_markdown_report(
        self,
        results: Dict[str, Any],
        statistics: Dict[str, Any],
        classifications: List[Dict[str, Any]]
    ) -> str:
        """生成 Markdown 格式的报告"""
        lines = []
        lines.append("# 质量阈值筛选报告")
        lines.append("")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # 总体统计
        lines.append("## 总体统计")
        lines.append("")
        lines.append("| 指标 | 数值 |")
        lines.append("|------|------|")
        lines.append(f"| 总任务数 | {statistics['total_tasks']} |")
        lines.append(f"| 高质量 (保留) | {statistics['high_quality']} |")
        lines.append(f"| 中等质量 | {statistics['medium_quality']} |")
        lines.append(f"| 低质量 (拒绝) | {statistics['low_quality']} |")
        lines.append(f"| 平均分数 | {statistics['average_score']}/30 |")
        lines.append(f"| 通过率 | {statistics['pass_rate']}% |")
        lines.append("")

        # 分数分布
        lines.append("## 分数分布")
        lines.append("")
        lines.append("| 分数区间 | 任务数 |")
        lines.append("|----------|--------|")
        for range_name, count in statistics["score_distribution"].items():
            lines.append(f"| {range_name} | {count} |")
        lines.append("")

        # 改进统计
        if "improvement" in statistics:
            imp = statistics["improvement"]
            lines.append("## 改进统计")
            lines.append("")
            lines.append(f"- 总改进数: {imp['total']}")
            lines.append(f"- 成功提升到高质量: {imp['successful']}")
            lines.append(f"- 仍然中等质量: {imp['failed']}")
            lines.append(f"- 成功率: {imp['success_rate']}%")
            lines.append(f"- 平均提升分数: {imp['average_score_delta']:+.2f}")
            lines.append("")

        # 任务详情
        lines.append("## 任务详情")
        lines.append("")

        for cls in classifications:
            lines.append(f"### {cls['task_id']}")
            lines.append("")
            lines.append(f"- **总分**: {cls['total_score']}/30")
            lines.append(f"- **质量等级**: {cls['quality_level']}")
            lines.append(f"- **处理动作**: {cls['action']}")
            lines.append(f"- **原因**:")
            for reason in cls.get('reasons', []):
                lines.append(f"  - {reason}")
            lines.append("")

        return "\n".join(lines)

    def _generate_html_report(
        self,
        results: Dict[str, Any],
        statistics: Dict[str, Any],
        classifications: List[Dict[str, Any]]
    ) -> str:
        """生成 HTML 格式的报告"""
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>质量阈值筛选报告</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #555;
            margin-top: 30px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #4CAF50;
        }}
        .stat-label {{
            color: #666;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #4CAF50;
            color: white;
        }}
        .task-card {{
            background: white;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 4px solid #ddd;
        }}
        .task-high {{ border-left-color: #4CAF50; }}
        .task-medium {{ border-left-color: #FF9800; }}
        .task-low {{ border-left-color: #F44336; }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
        }}
        .badge-high {{ background: #4CAF50; color: white; }}
        .badge-medium {{ background: #FF9800; color: white; }}
        .badge-low {{ background: #F44336; color: white; }}
    </style>
</head>
<body>
    <h1>质量阈值筛选报告</h1>
    <p><strong>生成时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

    <div class="summary">
        <div class="stat-card">
            <div class="stat-value">{statistics['total_tasks']}</div>
            <div class="stat-label">总任务数</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{statistics['high_quality']}</div>
            <div class="stat-label">高质量 (保留)</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{statistics['medium_quality']}</div>
            <div class="stat-label">中等质量</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{statistics['low_quality']}</div>
            <div class="stat-label">低质量 (拒绝)</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{statistics['average_score']}</div>
            <div class="stat-label">平均分数/30</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{statistics['pass_rate']}%</div>
            <div class="stat-label">通过率</div>
        </div>
    </div>

    <h2>分数分布</h2>
    <table>
        <tr>
            <th>分数区间</th>
            <th>任务数</th>
        </tr>
"""

        for range_name, count in statistics["score_distribution"].items():
            html += f"        <tr><td>{range_name}</td><td>{count}</td></tr>\n"

        html += "    </table>\n"

        if "improvement" in statistics:
            imp = statistics["improvement"]
            html += f"""
    <h2>改进统计</h2>
    <ul>
        <li>总改进数: {imp['total']}</li>
        <li>成功提升到高质量: {imp['successful']}</li>
        <li>仍然中等质量: {imp['failed']}</li>
        <li>成功率: {imp['success_rate']}%</li>
        <li>平均提升分数: {imp['average_score_delta']:+.2f}</li>
    </ul>
"""

        html += "\n    <h2>任务详情</h2>\n"

        for cls in classifications:
            quality_class = {
                "HIGH": "task-high",
                "MEDIUM": "task-medium",
                "LOW": "task-low"
            }.get(cls["quality_level"], "")

            badge_class = {
                "HIGH": "badge-high",
                "MEDIUM": "badge-medium",
                "LOW": "badge-low"
            }.get(cls["quality_level"], "")

            html += f"""
    <div class="task-card {quality_class}">
        <h3>{cls['task_id']} <span class="badge {badge_class}">{cls['quality_level']}</span></h3>
        <p><strong>总分:</strong> {cls['total_score']}/30</p>
        <p><strong>处理动作:</strong> {cls['action']}</p>
        <p><strong>原因:</strong></p>
        <ul>
"""
            for reason in cls.get('reasons', []):
                html += f"            <li>{reason}</li>\n"

            html += "        </ul>\n    </div>\n"

        html += """
</body>
</html>
"""
        return html

    def _generate_visualizations(
        self,
        statistics: Dict[str, Any]
    ) -> List[str]:
        """生成可视化图表"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')  # 非交互式后端
        except ImportError:
            return []

        viz_paths = []

        # 1. 质量分布柱状图
        fig, ax = plt.subplots(figsize=(10, 6))
        categories = ['High', 'Medium', 'Low']
        counts = [
            statistics['high_quality'],
            statistics['medium_quality'],
            statistics['low_quality']
        ]
        colors = ['#4CAF50', '#FF9800', '#F44336']

        ax.bar(categories, counts, color=colors)
        ax.set_title('Quality Distribution', fontsize=14, fontweight='bold')
        ax.set_ylabel('Number of Tasks', fontsize=12)
        ax.set_xlabel('Quality Level', fontsize=12)

        # 添加数值标签
        for i, v in enumerate(counts):
            ax.text(i, v + 0.1, str(v), ha='center', va='bottom', fontweight='bold')

        plt.tight_layout()
        bar_path = self.output_dir / "quality_distribution_bar.png"
        plt.savefig(bar_path, dpi=150, bbox_inches='tight')
        plt.close()
        viz_paths.append(str(bar_path))

        # 2. 分数分布直方图
        fig, ax = plt.subplots(figsize=(12, 6))

        # 构建分数分布数据
        score_ranges = list(statistics["score_distribution"].keys())
        range_counts = list(statistics["score_distribution"].values())

        ax.bar(score_ranges, range_counts, color='#2196F3', edgecolor='black')
        ax.set_title('Score Distribution', fontsize=14, fontweight='bold')
        ax.set_xlabel('Score Range', fontsize=12)
        ax.set_ylabel('Number of Tasks', fontsize=12)
        ax.axvline(x=2, color='#4CAF50', linestyle='--', linewidth=2, label='High Quality (27)')
        ax.axvline(x=3, color='#FF9800', linestyle='--', linewidth=2, label='Medium Quality (24)')
        ax.legend()

        plt.tight_layout()
        hist_path = self.output_dir / "score_distribution_histogram.png"
        plt.savefig(hist_path, dpi=150, bbox_inches='tight')
        plt.close()
        viz_paths.append(str(hist_path))

        return viz_paths


def test_report_generator():
    """测试报告生成器"""
    # 创建测试数据
    test_results = {
        "high_quality": [{"id": "task_001"}],
        "medium_quality_improved": [],
        "medium_quality_failed": [],
        "low_quality": [{"id": "task_002"}, {"id": "task_003"}]
    }

    test_statistics = {
        "total_tasks": 3,
        "high_quality": 1,
        "medium_quality": 0,
        "low_quality": 2,
        "keep": 1,
        "improve": 0,
        "reject": 2,
        "average_score": 22.5,
        "score_distribution": {
            "0-10": 0,
            "10-15": 0,
            "15-20": 1,
            "20-24": 1,
            "24-27": 0,
            "27-30": 1
        },
        "pass_rate": 33.33
    }

    test_classifications = [
        {
            "task_id": "task_001",
            "total_score": 27.5,
            "quality_level": "HIGH",
            "action": "KEEP",
            "reasons": ["所有维度都达到高标准"]
        },
        {
            "task_id": "task_002",
            "total_score": 22.0,
            "quality_level": "LOW",
            "action": "REJECT",
            "reasons": ["总分低于中等质量阈值"]
        },
        {
            "task_id": "task_003",
            "total_score": 18.0,
            "quality_level": "LOW",
            "action": "REJECT",
            "reasons": ["总分低于中等质量阈值", "多个维度不达标"]
        }
    ]

    # 生成报告
    generator = QualityReportGenerator(output_dir="./test_outputs/reports")
    report_files = generator.generate_comprehensive_report(
        test_results, test_statistics, test_classifications
    )

    print("报告生成完成！")
    print("\n生成的报告文件:")
    for report_type, path in report_files.items():
        print(f"  {report_type}: {path}")


if __name__ == "__main__":
    test_report_generator()
