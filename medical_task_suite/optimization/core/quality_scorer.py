"""
质量评分器 - 评估和计算任务质量分数
Quality Scorer - Evaluate and Calculate Task Quality Scores

功能：
1. 综合评估任务质量
2. 计算多维度质量得分
3. 生成质量报告
4. 提供改进建议
"""

from typing import Dict, List, Any
from collections import Counter


class QualityScorer:
    """质量评分器 - 评估任务质量"""

    # 质量维度权重配置
    DIMENSION_WEIGHTS = {
        'difficulty_appropriateness': 0.20,
        'scenario_accuracy': 0.15,
        'evaluation_completeness': 0.25,
        'information_richness': 0.20,
        'metadata_completeness': 0.10,
        'redline_coverage': 0.10
    }

    def __init__(self, config: Dict[str, Any] = None):
        """初始化质量评分器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.dimension_weights = self.config.get(
            'dimension_weights',
            self.DIMENSION_WEIGHTS
        )

    def score_difficulty_appropriateness(self, task: Dict[str, Any]) -> float:
        """评分难度适当性 (0-10)

        L3任务应该具有挑战性，L1任务应该相对简单

        Args:
            task: 任务字典

        Returns:
            难度适当性得分
        """
        difficulty = task.get('difficulty', 'L1')

        # 基础分
        base_score = {'L1': 8.0, 'L2': 8.5, 'L3': 9.0}.get(difficulty, 7.0)

        # L3任务检查
        if difficulty == 'L3':
            # 应该有红线测试
            if task.get('red_line_tests'):
                base_score += 0.5
            else:
                base_score -= 1.0

            # 应该有复杂患者行为
            behaviors = task.get('patient_behavior', {}).get('behaviors', [])
            if len(behaviors) >= 2:
                base_score += 0.3

        # L2任务检查
        if difficulty == 'L2':
            # 应该有对话流程
            if task.get('conversation_flow'):
                base_score += 0.3
            else:
                base_score -= 0.2

        return min(base_score, 10.0)

    def score_scenario_accuracy(self, task: Dict[str, Any]) -> float:
        """评分场景准确性 (0-10)

        检查场景类型是否与任务内容匹配

        Args:
            task: 任务字典

        Returns:
            场景准确性得分
        """
        scenario_type = task.get('metadata', {}).get('scenario_type')
        scenario_name = task.get('metadata', {}).get('scenario_name')

        # 基础分
        base_score = 8.0 if scenario_type else 5.0

        # 检查场景名称是否匹配
        if scenario_type and scenario_name:
            base_score += 0.5

        # 检查inquiry_requirements
        inquiry_reqs = task.get('metadata', {}).get('inquiry_requirements', {})
        if inquiry_reqs:
            base_score += 0.5

            # 检查inquiry_requirements的质量
            total_reqs = 0
            for category in inquiry_reqs.values():
                if isinstance(category, dict):
                    total_reqs += len(category)

            if total_reqs >= 4:
                base_score += 1.0

        return min(base_score, 10.0)

    def score_evaluation_completeness(self, task: Dict[str, Any]) -> float:
        """评分评估完整性 (0-10)

        检查评估标准的完整性

        Args:
            task: 任务字典

        Returns:
            评估完整性得分
        """
        eval_criteria = task.get('evaluation_criteria', {})
        actions = eval_criteria.get('actions', [])
        checks = eval_criteria.get('communication_checks', [])

        base_score = 5.0

        # Actions评分
        if len(actions) > 0:
            base_score += 1.0
        if len(actions) >= 2:
            base_score += 0.5

        # Communication checks评分
        if len(checks) > 0:
            base_score += 1.0
        if len(checks) >= 2:
            base_score += 0.5
        if len(checks) >= 3:
            base_score += 0.5

        # 检查是否有weight字段
        has_weights = any(check.get('weight') for check in checks)
        if has_weights:
            base_score += 1.0

        # 检查检查项的质量
        check_ids = [check.get('check_id', '') for check in checks]
        if 'safety_checking' in check_ids:
            base_score += 0.3
        if 'information_gathering' in check_ids:
            base_score += 0.3

        return min(base_score, 10.0)

    def score_information_richness(self, task: Dict[str, Any]) -> float:
        """评分信息丰富度 (0-10)

        检查任务信息的丰富程度

        Args:
            task: 任务字典

        Returns:
            信息丰富度得分
        """
        base_score = 5.0

        # Known info长度
        known_info = task.get('user_scenario', {}).get('instructions', {}).get('known_info', '')
        if len(known_info) > 50:
            base_score += 1.0
        if len(known_info) > 100:
            base_score += 0.5

        # Ticket长度
        ticket = task.get('ticket', '')
        if len(ticket) > 20:
            base_score += 0.5

        # 对话流程
        if task.get('conversation_flow'):
            base_score += 1.0

            flow = task['conversation_flow']
            if flow.get('expected_rounds'):
                base_score += 0.3
            if flow.get('unfolding_pattern'):
                base_score += 0.2

        # 系统记录
        if task.get('system_records'):
            base_score += 1.0

        # 红线测试
        if task.get('red_line_tests'):
            base_score += 1.0

        return min(base_score, 10.0)

    def score_metadata_completeness(self, task: Dict[str, Any]) -> float:
        """评分元数据完整性 (0-10)

        检查元数据的完整性

        Args:
            task: 任务字典

        Returns:
            元数据完整性得分
        """
        base_score = 5.0

        metadata = task.get('metadata', {})

        # 基础字段
        required_fields = ['source', 'department_cn', 'scenario_type', 'scenario_name']
        for field in required_fields:
            if metadata.get(field):
                base_score += 0.5

        # inquiry_requirements
        if metadata.get('inquiry_requirements'):
            base_score += 1.0

        # safety_rules
        if metadata.get('safety_rules'):
            base_score += 1.0

        # conversion_metadata
        if task.get('conversion_metadata'):
            base_score += 1.0

            conv_meta = task['conversion_metadata']
            if conv_meta.get('quality_score'):
                base_score += 0.5
            if conv_meta.get('optimizations_applied'):
                base_score += 0.5

        # original_task_id
        if task.get('original_task_id'):
            base_score += 0.5

        return min(base_score, 10.0)

    def score_redline_coverage(self, task: Dict[str, Any]) -> float:
        """评分红线测试覆盖 (0-10)

        检查红线测试的存在和质量

        Args:
            task: 任务字典

        Returns:
            红线测试覆盖得分
        """
        base_score = 5.0

        # L3任务应该有红线测试
        if task.get('difficulty') == 'L3':
            if task.get('red_line_tests'):
                base_score += 3.0

                # 检查红线测试的质量
                redline_tests = task['red_line_tests']
                if len(redline_tests) >= 1:
                    base_score += 1.0
                if len(redline_tests) >= 2:
                    base_score += 1.0
            else:
                base_score -= 2.0

        # L2任务可以有红线测试
        elif task.get('difficulty') == 'L2':
            if task.get('red_line_tests'):
                base_score += 2.0

        # 检查safety_rules
        safety_rules = task.get('metadata', {}).get('safety_rules', [])
        if safety_rules:
            base_score += 1.0

        return min(max(base_score, 0), 10.0)

    def calculate_task_quality_score(self, task: Dict[str, Any]) -> float:
        """计算任务综合质量得分 (0-10)

        Args:
            task: 任务字典

        Returns:
            综合质量得分
        """
        # 计算各维度得分
        scores = {
            'difficulty_appropriateness': self.score_difficulty_appropriateness(task),
            'scenario_accuracy': self.score_scenario_accuracy(task),
            'evaluation_completeness': self.score_evaluation_completeness(task),
            'information_richness': self.score_information_richness(task),
            'metadata_completeness': self.score_metadata_completeness(task),
            'redline_coverage': self.score_redline_coverage(task)
        }

        # 计算加权总分
        total_score = sum(
            scores[dim] * weight
            for dim, weight in self.dimension_weights.items()
        )

        return round(total_score, 2)

    def calculate_tasks_quality_scores(self, tasks: List[Dict[str, Any]]) -> List[float]:
        """批量计算任务质量得分

        Args:
            tasks: 任务列表

        Returns:
            质量得分列表
        """
        scores = []

        for task in tasks:
            score = self.calculate_task_quality_score(task)
            scores.append(score)

        return scores

    def get_statistics(self, tasks: List[Dict[str, Any]],
                     scores: List[float] = None) -> Dict[str, Any]:
        """获取质量统计信息

        Args:
            tasks: 任务列表
            scores: 质量得分列表（可选）

        Returns:
            统计信息字典
        """
        if scores is None:
            scores = self.calculate_tasks_quality_scores(tasks)

        if not scores:
            return {}

        import statistics

        # 基础统计
        stats = {
            'count': len(scores),
            'mean': statistics.mean(scores),
            'median': statistics.median(scores),
            'stdev': statistics.stdev(scores) if len(scores) > 1 else 0,
            'min': min(scores),
            'max': max(scores)
        }

        # 分数分布
        distribution = {
            'excellent': sum(1 for s in scores if s >= 9.0),
            'good': sum(1 for s in scores if 7.5 <= s < 9.0),
            'acceptable': sum(1 for s in scores if 6.0 <= s < 7.5),
            'poor': sum(1 for s in scores if s < 6.0)
        }

        stats['distribution'] = distribution
        stats['distribution_percentages'] = {
            level: count / len(scores) if scores else 0
            for level, count in distribution.items()
        }

        return stats

    def generate_quality_report(self, original_tasks: List[Dict[str, Any]],
                               optimized_tasks: List[Dict[str, Any]],
                               output_file: str = None) -> str:
        """生成质量报告

        Args:
            original_tasks: 原始任务列表
            optimized_tasks: 优化后任务列表
            output_file: 输出文件路径（可选）

        Returns:
            报告内容
        """
        original_scores = self.calculate_tasks_quality_scores(original_tasks)
        optimized_scores = self.calculate_tasks_quality_scores(optimized_tasks)

        original_stats = self.get_statistics(original_tasks, original_scores)
        optimized_stats = self.get_statistics(optimized_tasks, optimized_scores)

        report = []
        report.append("# 数据集质量报告\n")
        report.append("=" * 70 + "\n")

        # 原始数据集质量
        report.append("## 原始数据集质量\n")
        report.append(f"- 平均分: {original_stats['mean']:.2f}\n")
        report.append(f"- 中位数: {original_stats['median']:.2f}\n")
        report.append(f"- 标准差: {original_stats['stdev']:.2f}\n")
        report.append(f"- 最低分: {original_stats['min']:.2f}\n")
        report.append(f"- 最高分: {original_stats['max']:.2f}\n")
        report.append("\n分数分布:\n")
        for level, count in original_stats['distribution'].items():
            pct = original_stats['distribution_percentages'][level]
            report.append(f"- {level}: {count} ({pct:.1%})\n")

        # 优化数据集质量
        report.append("\n## 优化数据集质量\n")
        report.append(f"- 平均分: {optimized_stats['mean']:.2f}\n")
        report.append(f"- 中位数: {optimized_stats['median']:.2f}\n")
        report.append(f"- 标准差: {optimized_stats['stdev']:.2f}\n")
        report.append(f"- 最低分: {optimized_stats['min']:.2f}\n")
        report.append(f"- 最高分: {optimized_stats['max']:.2f}\n")
        report.append("\n分数分布:\n")
        for level, count in optimized_stats['distribution'].items():
            pct = optimized_stats['distribution_percentages'][level]
            report.append(f"- {level}: {count} ({pct:.1%})\n")

        # 质量提升
        improvement = optimized_stats['mean'] - original_stats['mean']
        report.append(f"\n## 质量提升\n")
        report.append(f"- 平均分提升: {improvement:+.2f}\n")

        report_content = ''.join(report)

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)

        return report_content
