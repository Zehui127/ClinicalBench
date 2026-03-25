"""
Module Coverage Analyzer for Medical Task Suite

This module analyzes the coverage of 13 core medical modules across
tasks and generates coverage reports.
"""

import os
import yaml
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class ModuleCoverageStats:
    """
    Coverage statistics for a single module.

    Attributes:
        module_id: Module identifier
        module_name: Human-readable name
        priority: P0, P1, P2, or P3
        total_tasks: Total number of tasks
        tasks_covering_module: Number of tasks covering this module
        coverage_percentage: Percentage of tasks covering this module
        difficulty_distribution: Tasks by difficulty (L1, L2, L3)
        target_coverage: Target coverage percentage
        meets_target: Whether target is met
    """
    module_id: str
    module_name: str
    priority: str
    total_tasks: int
    tasks_covering_module: int
    coverage_percentage: float
    difficulty_distribution: Dict[str, int]
    target_coverage: float = 95.0
    meets_target: bool = False

    def __post_init__(self):
        self.meets_target = self.coverage_percentage >= self.target_coverage


@dataclass
class CoverageReport:
    """
    Complete coverage report for all modules.

    Attributes:
        total_tasks: Total number of tasks analyzed
        overall_coverage_percentage: Overall coverage across all modules
        module_stats: List of ModuleCoverageStats for each module
        priority_coverage: Coverage by priority level
        difficulty_coverage: Coverage by difficulty level
        recommendations: Recommendations for improving coverage
        summary: Summary statistics
    """
    total_tasks: int
    overall_coverage_percentage: float
    module_stats: List[ModuleCoverageStats]
    priority_coverage: Dict[str, float]
    difficulty_coverage: Dict[str, float]
    recommendations: List[str]
    summary: Dict[str, Any]


class ModuleCoverageAnalyzer:
    """
    Analyzes module coverage across medical task datasets.

    This class:
    1. Analyzes which modules are tested in which tasks
    2. Calculates coverage percentages
    3. Identifies gaps in coverage
    4. Generates recommendations
    5. Creates coverage reports
    """

    # Module definitions and priorities
    MODULE_PRIORITIES = {
        'lab_test_inquiry': 'P0',
        'hallucination_free_diag': 'P0',
        'medication_guidance': 'P0',
        'differential_diag': 'P0',
        'emergency_handling': 'P0',
        'visit_instructions': 'P1',
        'structured_emr': 'P1',
        'history_verification': 'P1',
        'lab_analysis': 'P1',
        'tcm_cognitive': 'P2',
        'cutting_edge_tx': 'P2',
        'insurance_guidance': 'P2',
        'multimodal_understanding': 'P3',
    }

    TARGET_COVERAGE = {
        'P0': 100.0,  # Critical safety modules must have 100% coverage
        'P1': 95.0,   # Core clinical modules
        'P2': 85.0,   # Quality enhancement modules
        'P3': 80.0,   # Advanced capability modules
    }

    def __init__(self, config_dir: str = None):
        """
        Initialize the ModuleCoverageAnalyzer.

        Args:
            config_dir: Directory containing module configuration files.
        """
        if config_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_dir = os.path.join(
                os.path.dirname(os.path.dirname(current_dir)),
                'config'
            )

        self.config_dir = config_dir
        self.module_names = self._load_module_names()

    def _load_module_names(self) -> Dict[str, str]:
        """Load module names from configuration."""
        filepath = os.path.join(self.config_dir, 'module_definitions.yaml')
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                modules = data.get('modules', {})
                return {
                    module_id: config.get('module_name', module_id)
                    for module_id, config in modules.items()
                }
        except Exception as e:
            print(f"Warning: Could not load module names: {e}")
            return {}

    def analyze_dataset_coverage(
        self,
        tasks: List[Dict[str, Any]]
    ) -> CoverageReport:
        """
        Analyze module coverage across a dataset.

        Args:
            tasks: List of task definitions

        Returns:
            CoverageReport object with complete analysis
        """
        total_tasks = len(tasks)

        # Initialize counters
        module_counts = defaultdict(int)
        module_by_difficulty = defaultdict(lambda: defaultdict(int))
        priority_counts = defaultdict(int)

        # Analyze each task
        for task in tasks:
            modules_tested = task.get('modules_tested', [])
            difficulty = task.get('difficulty', 'L1')

            for module_id in modules_tested:
                module_counts[module_id] += 1
                module_by_difficulty[module_id][difficulty] += 1

                # Count by priority
                priority = self.MODULE_PRIORITIES.get(module_id, 'P2')
                priority_counts[priority] += 1

        # Calculate coverage statistics for each module
        module_stats = []
        for module_id in self.MODULE_PRIORITIES.keys():
            count = module_counts.get(module_id, 0)
            coverage_pct = (count / total_tasks * 100) if total_tasks > 0 else 0
            priority = self.MODULE_PRIORITIES[module_id]
            target = self.TARGET_COVERAGE[priority]

            stats = ModuleCoverageStats(
                module_id=module_id,
                module_name=self.module_names.get(module_id, module_id),
                priority=priority,
                total_tasks=total_tasks,
                tasks_covering_module=count,
                coverage_percentage=round(coverage_pct, 2),
                difficulty_distribution=dict(module_by_difficulty[module_id]),
                target_coverage=target
            )
            module_stats.append(stats)

        # Calculate overall coverage
        overall_coverage = sum(
            stat.coverage_percentage for stat in module_stats
        ) / len(module_stats) if module_stats else 0

        # Calculate priority-level coverage
        priority_coverage = {}
        for priority in ['P0', 'P1', 'P2', 'P3']:
            modules_in_priority = [
                stat for stat in module_stats if stat.priority == priority
            ]
            if modules_in_priority:
                priority_coverage[priority] = round(
                    sum(m.coverage_percentage for m in modules_in_priority) /
                    len(modules_in_priority), 2
                )
            else:
                priority_coverage[priority] = 0.0

        # Calculate difficulty-level coverage
        difficulty_coverage = {}
        for difficulty in ['L1', 'L2', 'L3']:
            difficulty_tasks = sum(1 for t in tasks if t.get('difficulty') == difficulty)
            if difficulty_tasks > 0:
                difficulty_coverage[difficulty] = round(
                    (difficulty_tasks / total_tasks * 100), 2
                )
            else:
                difficulty_coverage[difficulty] = 0.0

        # Generate recommendations
        recommendations = self._generate_recommendations(module_stats, priority_coverage)

        # Create summary
        summary = self._create_summary(module_stats, priority_coverage, difficulty_coverage)

        return CoverageReport(
            total_tasks=total_tasks,
            overall_coverage_percentage=round(overall_coverage, 2),
            module_stats=module_stats,
            priority_coverage=priority_coverage,
            difficulty_coverage=difficulty_coverage,
            recommendations=recommendations,
            summary=summary
        )

    def _generate_recommendations(
        self,
        module_stats: List[ModuleCoverageStats],
        priority_coverage: Dict[str, float]
    ) -> List[str]:
        """Generate recommendations for improving coverage."""
        recommendations = []

        # Check overall coverage
        overall = sum(m.coverage_percentage for m in module_stats) / len(module_stats)
        if overall < 95.0:
            recommendations.append(
                f"Overall coverage is {overall:.1f}%, below the 95% target. "
                "Increase module coverage across all tasks."
            )

        # Check priority-level coverage
        for priority in ['P0', 'P1', 'P2', 'P3']:
            coverage = priority_coverage.get(priority, 0)
            target = self.TARGET_COVERAGE[priority]
            if coverage < target:
                recommendations.append(
                    f"{priority} module coverage is {coverage:.1f}%, below {target}% target. "
                    f"Add more tasks testing {priority} modules."
                )

        # Check individual module coverage
        low_coverage_modules = [
            m for m in module_stats
            if m.coverage_percentage < m.target_coverage
        ]

        if low_coverage_modules:
            recommendations.append(
                f"{len(low_coverage_modules)} modules are below target coverage:"
            )
            for module in low_coverage_modules:
                gap = module.target_coverage - module.coverage_percentage
                recommendations.append(
                    f"  - {module.module_name} ({module.module_id}): "
                    f"{module.coverage_percentage:.1f}% (target: {module.target_coverage}%, "
                    f"gap: {gap:.1f}%, need ~{int(gap * module.total_tasks / 100)} more tasks)"
                )

        # Check difficulty distribution
        if any(v < 15 for v in priority_coverage.values() if isinstance(v, (int, float))):
            recommendations.append(
                "Some difficulty levels may be underrepresented. "
                "Ensure balanced distribution across L1, L2, and L3."
            )

        return recommendations

    def _create_summary(
        self,
        module_stats: List[ModuleCoverageStats],
        priority_coverage: Dict[str, float],
        difficulty_coverage: Dict[str, float]
    ) -> Dict[str, Any]:
        """Create summary statistics."""
        # Count modules meeting target
        modules_meeting_target = sum(1 for m in module_stats if m.meets_target)
        total_modules = len(module_stats)

        # Find best and worst covered modules
        if module_stats:
            best = max(module_stats, key=lambda m: m.coverage_percentage)
            worst = min(module_stats, key=lambda m: m.coverage_percentage)
        else:
            best = None
            worst = None

        # Average modules per task
        avg_modules = sum(
            m.tasks_covering_module for m in module_stats
        ) / module_stats[0].total_tasks if module_stats else 0

        return {
            'total_modules': total_modules,
            'modules_meeting_target': modules_meeting_target,
            'modules_below_target': total_modules - modules_meeting_target,
            'target_achievement_rate': (
                modules_meeting_target / total_modules * 100
                if total_modules > 0 else 0
            ),
            'best_covered_module': {
                'name': best.module_name if best else '',
                'coverage': best.coverage_percentage if best else 0
            },
            'worst_covered_module': {
                'name': worst.module_name if worst else '',
                'coverage': worst.coverage_percentage if worst else 0
            },
            'average_modules_per_task': round(avg_modules, 2),
            'priority_targets_met': sum(
                1 for p, c in priority_coverage.items()
                if c >= self.TARGET_COVERAGE[p]
            )
        }

    def generate_coverage_report(
        self,
        tasks: List[Dict[str, Any]],
        output_format: str = 'text'
    ) -> str:
        """
        Generate a human-readable coverage report.

        Args:
            tasks: List of task definitions
            output_format: 'text' or 'markdown'

        Returns:
            Formatted report string
        """
        report = self.analyze_dataset_coverage(tasks)

        if output_format == 'markdown':
            return self._format_markdown_report(report)
        else:
            return self._format_text_report(report)

    def _format_text_report(self, report: CoverageReport) -> str:
        """Format report as plain text."""
        lines = []
        lines.append("=" * 80)
        lines.append("MEDICAL TASK SUITE - MODULE COVERAGE REPORT")
        lines.append("=" * 80)
        lines.append("")

        # Summary
        lines.append("SUMMARY")
        lines.append("-" * 80)
        lines.append(f"Total Tasks: {report.total_tasks}")
        lines.append(f"Overall Coverage: {report.overall_coverage_percentage:.1f}%")
        lines.append(f"Modules Meeting Target: {report.summary['modules_meeting_target']}/{report.summary['total_modules']}")
        lines.append("")

        # Priority Coverage
        lines.append("PRIORITY LEVEL COVERAGE")
        lines.append("-" * 80)
        for priority in ['P0', 'P1', 'P2', 'P3']:
            coverage = report.priority_coverage.get(priority, 0)
            target = self.TARGET_COVERAGE[priority]
            status = "✓" if coverage >= target else "✗"
            lines.append(f"{status} {priority}: {coverage:.1f}% (target: {target}%)")
        lines.append("")

        # Module Coverage
        lines.append("MODULE COVERAGE DETAILS")
        lines.append("-" * 80)
        for stat in report.module_stats:
            status = "✓" if stat.meets_target else "✗"
            lines.append(f"{status} {stat.module_name} ({stat.module_id})")
            lines.append(f"    Priority: {stat.priority}")
            lines.append(f"    Coverage: {stat.coverage_percentage:.1f}% "
                        f"({stat.tasks_covering_module}/{stat.total_tasks} tasks)")
            lines.append(f"    Target: {stat.target_coverage}%")
            lines.append("")

        # Recommendations
        if report.recommendations:
            lines.append("RECOMMENDATIONS")
            lines.append("-" * 80)
            for rec in report.recommendations:
                lines.append(f"• {rec}")
            lines.append("")

        lines.append("=" * 80)
        return "\n".join(lines)

    def _format_markdown_report(self, report: CoverageReport) -> str:
        """Format report as Markdown."""
        lines = []
        lines.append("# Medical Task Suite - Module Coverage Report")
        lines.append("")
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- **Total Tasks**: {report.total_tasks}")
        lines.append(f"- **Overall Coverage**: {report.overall_coverage_percentage:.1f}%")
        lines.append(f"- **Modules Meeting Target**: {report.summary['modules_meeting_target']}/{report.summary['total_modules']}")
        lines.append(f"- **Average Modules per Task**: {report.summary['average_modules_per_task']}")
        lines.append("")

        lines.append("## Priority Level Coverage")
        lines.append("")
        lines.append("| Priority | Coverage | Target | Status |")
        lines.append("|----------|----------|--------|--------|")
        for priority in ['P0', 'P1', 'P2', 'P3']:
            coverage = report.priority_coverage.get(priority, 0)
            target = self.TARGET_COVERAGE[priority]
            status = "✓" if coverage >= target else "✗"
            lines.append(f"| {priority} | {coverage:.1f}% | {target}% | {status} |")
        lines.append("")

        lines.append("## Module Coverage Details")
        lines.append("")
        lines.append("| Module | Priority | Coverage | Target | Status |")
        lines.append("|--------|----------|----------|--------|--------|")
        for stat in report.module_stats:
            status = "✓" if stat.meets_target else "✗"
            lines.append(
                f"| {stat.module_name} | {stat.priority} | "
                f"{stat.coverage_percentage:.1f}% | {stat.target_coverage}% | {status} |"
            )
        lines.append("")

        if report.recommendations:
            lines.append("## Recommendations")
            lines.append("")
            for rec in report.recommendations:
                lines.append(f"- {rec}")
            lines.append("")

        return "\n".join(lines)

    def calculate_coverage_gap(
        self,
        current_tasks: List[Dict[str, Any]],
        target_coverage: float = 95.0
    ) -> Dict[str, int]:
        """
        Calculate how many additional tasks are needed for each module.

        Args:
            current_tasks: Current task list
            target_coverage: Target coverage percentage

        Returns:
            Dictionary mapping module_id to needed task count
        """
        report = self.analyze_dataset_coverage(current_tasks)
        total_tasks = report.total_tasks

        needed_tasks = {}
        for stat in report.module_stats:
            if stat.coverage_percentage < target_coverage:
                # Calculate how many more tasks needed
                current_count = stat.tasks_covering_module
                target_count = int(target_coverage * total_tasks / 100)
                needed = max(0, target_count - current_count)
                needed_tasks[stat.module_id] = needed

        return needed_tasks

    def filter_tasks_by_modules(
        self,
        tasks: List[Dict[str, Any]],
        required_modules: List[str],
        require_all: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Filter tasks by module coverage.

        Args:
            tasks: Task list to filter
            required_modules: Module IDs to filter by
            require_all: If True, task must have ALL required modules.
                        If False, task must have AT LEAST ONE.

        Returns:
            Filtered list of tasks
        """
        filtered = []
        for task in tasks:
            modules_tested = task.get('modules_tested', [])
            has_modules = set(modules_tested) & set(required_modules)

            if require_all:
                if set(required_modules).issubset(set(modules_tested)):
                    filtered.append(task)
            else:
                if has_modules:
                    filtered.append(task)

        return filtered
