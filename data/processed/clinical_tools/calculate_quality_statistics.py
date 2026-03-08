#!/usr/bin/env python3
"""
Clinical Consultation Task Quality Statistics Calculator
临床咨询任务质量统计计算器

Calculates key statistics from filtered tasks and review scores:
- Total raw tasks count
- High-quality tasks count
- Pass rate
- Department breakdown
- Top rejection reasons

Author: Clinical Benchmark Team
Date: 2026-03-03
Version: 1.0
"""

import json
import os
from collections import Counter, defaultdict
from typing import Dict, List, Any


# ============================================================================
# CONFIGURATION
# ============================================================================

class Colors:
    """Console color codes for terminal output."""
    HEADER = '\033[95m'      # Bright magenta
    OKBLUE = '\033[94m'       # Bright blue
    OKCYAN = '\033[96m'       # Bright cyan
    OKGREEN = '\033[92m'      # Bright green
    WARNING = '\033[93m'      # Bright yellow
    FAIL = '\033[91m'         # Bright red
    ENDC = '\033[0m'          # Reset
    BOLD = '\033[1m'          # Bold
    UNDERLINE = '\033[4m'      # Underline


class StatisticsConfig:
    """Configuration for statistics calculation."""

    BASE_DIR = r'C:\Users\方正\tau2-bench\data\processed\clinical_tools'
    TASKS_FILTERED_PATH = os.path.join(BASE_DIR, 'tasks_filtered.json')
    REVIEW_SCORES_PATH = os.path.join(BASE_DIR, 'review_scores.json')

    OUTPUT_JSON_PATH = os.path.join(BASE_DIR, 'task_quality_statistics.json')
    OUTPUT_MD_PATH = os.path.join(BASE_DIR, 'task_quality_statistics.md')


# ============================================================================
# LOADING FUNCTIONS
# ============================================================================

def load_filtered_tasks(file_path: str) -> List[Dict[str, Any]]:
    """
    Load filtered tasks JSON file.
    加载过滤后任务 JSON 文件。

    Args:
        file_path: Path to tasks_filtered.json

    Returns:
        List of filtered task dictionaries
    """
    print(f"{Colors.OKCYAN}[INFO]{Colors.ENDC} Loading filtered tasks from: {file_path}")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle different formats
    if isinstance(data, dict) and 'tasks' in data:
        tasks = data['tasks']
    elif isinstance(data, list):
        tasks = data
    else:
        raise ValueError(f"Unexpected data format: {type(data)}")

    print(f"{Colors.OKGREEN}[INFO]{Colors.ENDC} Loaded {len(tasks)} filtered tasks")
    return tasks


def load_review_scores(file_path: str) -> List[Dict[str, Any]]:
    """
    Load review scores JSON file.
    加载审查评分 JSON 文件。

    Args:
        file_path: Path to review_scores.json

    Returns:
        List of review score dictionaries
    """
    print(f"{Colors.OKCYAN}[INFO]{Colors.ENDC} Loading review scores from: {file_path}")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        scores = json.load(f)

    print(f"{Colors.OKGREEN}[INFO]{Colors.ENDC} Loaded {len(scores)} review score entries")
    return scores


# ============================================================================
# STATISTICS CALCULATION
# ============================================================================

def calculate_basic_statistics(filtered_tasks: List[Dict], review_scores: List[Dict]) -> Dict[str, Any]:
    """
    Calculate basic statistics.
    计算基础统计。

    Args:
        filtered_tasks: List of high-quality tasks
        review_scores: List of all task scores

    Returns:
        Dictionary with basic statistics
    """
    total_raw_tasks = len(review_scores)
    high_quality_tasks = len(filtered_tasks)
    failed_tasks = total_raw_tasks - high_quality_tasks

    pass_rate = (high_quality_tasks / total_raw_tasks * 100) if total_raw_tasks > 0 else 0
    fail_rate = (failed_tasks / total_raw_tasks * 100) if total_raw_tasks > 0 else 0

    return {
        'total_raw_tasks': total_raw_tasks,
        'high_quality_tasks': high_quality_tasks,
        'failed_tasks': failed_tasks,
        'pass_rate': round(pass_rate, 2),
        'fail_rate': round(fail_rate, 2)
    }


def calculate_department_breakdown(filtered_tasks: List[Dict]) -> Dict[str, Dict[str, int]]:
    """
    Calculate department breakdown for high-quality tasks.
    计算高质量任务的科室分布。

    Args:
        filtered_tasks: List of high-quality tasks

    Returns:
        Dictionary with department counts and percentages
    """
    department_counts = Counter()
    department_map = {
        'nephrology': ['nephrology', 'renal', 'kidney', 'ckd', 'egfr'],
        'cardiology': ['cardio', 'heart', 'hypertension', 'chest_pain', 'mi', 'coronary'],
        'gastroenterology': ['gastro', 'stomach', 'ulcer', 'digestive', 'liver']
    }

    for task in filtered_tasks:
        # Extract department from task_id or other fields
        task_id = str(task.get('id') or task.get('task_id', '')).lower()
        ticket = str(task.get('ticket', '')).lower()
        diagnosis = str(task.get('diagnosis', task.get('clinical_scenario', {}).get('diagnosis', '')).lower()
        original_format = str(task.get('original_format', '')).lower()

        # Check department keywords
        matched = False
        for dept, keywords in department_map.items():
            if any(keyword in task_id or keyword in ticket or keyword in diagnosis or dept in original_format
                   for keyword in keywords):
                department_counts[dept] += 1
                matched = True
                break

        if not matched:
            department_counts['general_practice'] += 1

    # Calculate percentages
    total_tasks = len(filtered_tasks)
    department_breakdown = {}

    for dept, count in department_counts.items():
        percentage = (count / total_tasks * 100) if total_tasks > 0 else 0
        department_breakdown[dept] = {
            'count': count,
            'percentage': round(percentage, 2)
        }

    # Sort by count (descending)
    department_breakdown = dict(sorted(department_breakdown.items(),
                                           key=lambda x: x[1]['count'],
                                           reverse=True))

    return department_breakdown


def calculate_top_rejection_reasons(review_scores: List[Dict], top_n: int = 3) -> List[Dict[str, Any]]:
    """
    Calculate top rejection reasons for failed tasks.
    计算失败任务的主要拒绝原因。

    Args:
        review_scores: List of all task scores
        top_n: Number of top reasons to return

    Returns:
        List of rejection reason dictionaries
    """
    rejection_reasons = Counter()

    for score in review_scores:
        if not score.get('pass_status', False):
            reason = score.get('rejection_reason', 'Unknown reason')
            if reason:
                # Extract primary reason (before first colon)
                primary_reason = reason.split(':')[0].strip() if ':' in reason else reason
                rejection_reasons[primary_reason] += 1

    # Get top N reasons
    top_reasons = rejection_reasons.most_common(top_n)

    total_failed = sum(1 for s in review_scores if not s.get('pass_status', False))

    result = []
    for reason, count in top_reasons:
        percentage = (count / total_failed * 100) if total_failed > 0 else 0
        result.append({
            'rank': len(result) + 1,
            'reason': reason,
            'count': count,
            'percentage': round(percentage, 2)
        })

    return result


def calculate_score_distribution(review_scores: List[Dict]) -> Dict[str, int]:
    """
    Calculate score distribution across ranges.
    计算分数分布。

    Args:
        review_scores: List of all task scores

    Returns:
        Dictionary with score range counts
    """
    score_ranges = [
        (0, 1, '0-1'),
        (1, 2, '1-2'),
        (2, 3, '2-3'),
        (3, 4, '3-4'),
        (4, 5, '4-5')
    ]

    distribution = {}
    total_tasks = len(review_scores)

    for min_score, max_score, label in score_ranges:
        count = sum(1 for s in review_scores
                     if min_score <= s.get('average_score', 0) < max_score)
        percentage = (count / total_tasks * 100) if total_tasks > 0 else 0
        distribution[label] = {
            'count': count,
            'percentage': round(percentage, 2)
        }

    return distribution


def calculate_dimension_averages(review_scores: List[Dict]) -> Dict[str, float]:
    """
    Calculate average scores for each dimension.
    计算各维度平均分。

    Args:
        review_scores: List of all task scores

    Returns:
        Dictionary with average scores for each dimension
    """
    dimensions = [
        'clinical_accuracy_score',
        'scenario_realism_score',
        'evaluation_completeness_score',
        'difficulty_appropriateness_score'
    ]

    averages = {}
    for dimension in dimensions:
        scores = [s.get(dimension, 0) for s in review_scores]
        if scores:
            avg = sum(scores) / len(scores)
            averages[dimension] = round(avg, 2)

    return averages


# ============================================================================
# OUTPUT FUNCTIONS
# ============================================================================

def print_console_report(basic_stats: Dict, dept_breakdown: Dict,
                          top_rejections: List[Dict], distribution: Dict,
                          dimension_avgs: Dict):
    """
    Print formatted report to console with colors.
    打印带颜色的格式化报告到控制台。

    Args:
        basic_stats: Basic statistics dictionary
        dept_breakdown: Department breakdown dictionary
        top_rejections: Top rejection reasons list
        distribution: Score distribution dictionary
        dimension_avgs: Dimension averages dictionary
    """
    print()
    print("=" * 80)
    print(f"{Colors.HEADER}CLINICAL CONSULTATION TASK QUALITY STATISTICS{Colors.ENDC}")
    print(f"{Colors.HEADER}临床咨询任务质量统计{Colors.ENDC}")
    print("=" * 80)
    print()

    # Basic Statistics
    print(f"{Colors.BOLD}Basic Statistics / 基础统计{Colors.ENDC}")
    print("-" * 80)
    print(f"  Total Raw Tasks / 原始任务总数:       {Colors.OKBLUE}{basic_stats['total_raw_tasks']:,}{Colors.ENDC}")
    print(f"  High-Quality Tasks / 高质量任务:      {Colors.OKGREEN}{basic_stats['high_quality_tasks']:,}{Colors.ENDC}")
    print(f"  Failed Tasks / 失败任务:             {Colors.FAIL}{basic_stats['failed_tasks']:,}{Colors.ENDC}")
    print()
    print(f"  Pass Rate / 通过率:                  {Colors.OKGREEN}{basic_stats['pass_rate']}%{Colors.ENDC}")
    print(f"  Fail Rate / 失败率:                  {Colors.FAIL}{basic_stats['fail_rate']}%{Colors.ENDC}")
    print()

    # Score Distribution
    print(f"{Colors.BOLD}Score Distribution / 评分分布{Colors.ENDC}")
    print("-" * 80)
    for label, data in distribution.items():
        bar = '█' * int(data['percentage'] / 2)
        color = Colors.OKGREEN if data['percentage'] >= 20 else Colors.WARNING if data['percentage'] >= 10 else Colors.FAIL
        print(f"  {label:<8}  {color}{data['count']:>5} ({data['percentage']:>5}%){Colors.ENDC}  {bar}")
    print()

    # Dimension Averages
    print(f"{Colors.BOLD}Dimension Averages / 维度平均分{Colors.ENDC}")
    print("-" * 80)
    dimension_names = {
        'clinical_accuracy_score': 'Clinical Accuracy / 临床准确性',
        'scenario_realism_score': 'Scenario Realism / 场景真实性',
        'evaluation_completeness_score': 'Evaluation Completeness / 评估完整性',
        'difficulty_appropriateness_score': 'Difficulty Appropriateness / 难度适当性'
    }

    for dim_key, dim_name in dimension_names.items():
        score = dimension_avgs.get(dim_key, 0)
        color = Colors.OKGREEN if score >= 4 else Colors.WARNING if score >= 3 else Colors.FAIL
        print(f"  {dim_name:<45}  {color}{score}/5.0{Colors.ENDC}")
    print()

    # Department Breakdown
    print(f"{Colors.BOLD}Department Breakdown (High-Quality Tasks) / 科室分布（高质量任务）{Colors.ENDC}")
    print("-" * 80)
    print(f"  {'Department':<25}  {'Count':<10}  {'Percentage':<12}")
    print(f"  {'-' * 25}  {'-' * 10}  {'-' * 12}")

    for dept, data in dept_breakdown.items():
        dept_name = dept.replace('_', ' ').title()
        print(f"  {dept_name:<25}  {Colors.OKCYAN}{data['count']:>10}{Colors.ENDC}  {data['percentage']:>11}%")
    print()

    # Top Rejection Reasons
    print(f"{Colors.BOLD}Top {len(top_rejections)} Rejection Reasons / 前 {len(top_rejections)} 位拒绝原因{Colors.ENDC}")
    print("-" * 80)
    print(f"  {'Rank':<6}  {'Reason':<50}  {'Count':<8}  {'%':<8}")
    print(f"  {'-' * 6}  {'-' * 50}  {'-' * 8}  {'-' * 8}")

    for rejection in top_rejections:
        rank = rejection['rank']
        reason = rejection['reason'][:47] + '...' if len(rejection['reason']) > 47 else rejection['reason']
        count = rejection['count']
        percentage = rejection['percentage']
        print(f"  {rank:<6}  {reason:<50}  {Colors.FAIL}{count:<8}{Colors.ENDC}  {percentage:>7}%")
    print()

    print("=" * 80)


def save_json_report(basic_stats: Dict, dept_breakdown: Dict,
                    top_rejections: List[Dict], distribution: Dict,
                    dimension_avgs: Dict, output_path: str):
    """
    Save statistics as JSON report.
    保存统计为 JSON 报告。

    Args:
        basic_stats: Basic statistics dictionary
        dept_breakdown: Department breakdown dictionary
        top_rejections: Top rejection reasons list
        distribution: Score distribution dictionary
        dimension_avgs: Dimension averages dictionary
        output_path: Path to save JSON report
    """
    report = {
        'generated_timestamp': __import__('datetime').datetime.now().isoformat(),
        'basic_statistics': basic_stats,
        'score_distribution': distribution,
        'dimension_averages': dimension_avgs,
        'department_breakdown': dept_breakdown,
        'top_rejection_reasons': top_rejections
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"{Colors.OKGREEN}[INFO]{Colors.ENDC} JSON report saved to: {output_path}")


def save_markdown_report(basic_stats: Dict, dept_breakdown: Dict,
                        top_rejections: List[Dict], distribution: Dict,
                        dimension_avgs: Dict, output_path: str):
    """
    Save statistics as Markdown report.
    保存统计为 Markdown 报告。

    Args:
        basic_stats: Basic statistics dictionary
        dept_breakdown: Department breakdown dictionary
        top_rejections: Top rejection reasons list
        distribution: Score distribution dictionary
        dimension_avgs: Dimension averages dictionary
        output_path: Path to save Markdown report
    """
    import datetime

    report = f"""# Clinical Consultation Task Quality Statistics Report
# 临床咨询任务质量统计报告

**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Executive Summary / 执行摘要

- **Total Raw Tasks / 原始任务总数:** {basic_stats['total_raw_tasks']:,}
- **High-Quality Tasks / 高质量任务:** {basic_stats['high_quality_tasks']:,}
- **Failed Tasks / 失败任务:** {basic_stats['failed_tasks']:,}
- **Pass Rate / 通过率:** **{basic_stats['pass_rate']}%**
- **Fail Rate / 失败率:** {basic_stats['fail_rate']}%

---

## Score Distribution / 评分分布

| Score Range | Count | Percentage | Bar |
|-------------|-------|------------|-----|
"""

    for label, data in distribution.items():
        bar_length = int(data['percentage'] / 2)
        bar = '█' * bar_length
        report += f"| {label} | {data['count']:>6} | {data['percentage']:>9}% | {bar} |\n"

    report += f"""

---

## Dimension Analysis / 维度分析

| Dimension / 维度 | Average Score / 平均分 | Assessment / 评估 |
|------------------|----------------------|-------------|
"""

    dimension_names = {
        'clinical_accuracy_score': 'Clinical Accuracy / 临床准确性',
        'scenario_realism_score': 'Scenario Realism / 场景真实性',
        'evaluation_completeness_score': 'Evaluation Completeness / 评估完整性',
        'difficulty_appropriateness_score': 'Difficulty Appropriateness / 难度适当性'
    }

    for dim_key, dim_name in dimension_names.items():
        score = dimension_avgs.get(dim_key, 0)
        if score >= 4:
            assessment = f"{Colors.OKGREEN}Excellent{''} ✓"  # Will be rendered
        elif score >= 3:
            assessment = "Good ✓"
        elif score >= 2:
            assessment = "Fair ▼"
        else:
            assessment = "Poor ✗"

        # Remove color codes for markdown
        assessment_clean = assessment.replace('[OKGREEN]', '').replace('[FAIL]', '')

        report += f"| {dim_name} | {score}/5.0 | {assessment_clean} |\n"

    report += f"""

---

## Department Breakdown (High-Quality Tasks) / 科室分布（高质量任务）

| Department / 科室 | Count / 数量 | Percentage / 百分比 |
|-------------------|---------------|------------------|
"""

    for dept, data in dept_breakdown.items():
        dept_name = dept.replace('_', ' ').title()
        report += f"| {dept_name} | {data['count']:,} | {data['percentage']}% |\n"

    report += f"""

---

## Top {len(top_rejections)} Rejection Reasons / 前 {len(top_rejections)} 位拒绝原因

| Rank | Reason / 原因 | Count / 数量 | Percentage / 百分比 |
|------|-------------------|---------------|------------------|
"""

    for rejection in top_rejections:
        report += f"| {rejection['rank']} | {rejection['reason']} | {rejection['count']:,} | {rejection['percentage']}% |\n"

    report += f"""

---

## Interpretation / 结果解读

### Pass Rate / 通过率

"""

    if basic_stats['pass_rate'] >= 70:
        report += f"- **Excellent (≥70%):** High-quality task set suitable for Agent benchmark evaluation\n"
    elif basic_stats['pass_rate'] >= 50:
        report += f"- **Good (50-69%):** Moderate quality, consider reviewing rejected tasks\n"
    else:
        report += f"- **Poor (<50%):** Low quality, significant issues in task design\n"

    report += f"""

### Department Representation / 科室代表性

"""

    # Check department balance
    dept_percentages = [data['percentage'] for data in dept_breakdown.values()]
    if max(dept_percentages) - min(dept_percentages) < 30:
        report += "- **Well-balanced:** All departments represented (±30%)\n"
    else:
        report += "- **Imbalanced:** Department distribution shows significant variation\n"

    report += f"""

### Quality Dimensions / 质量维度

"""

    for dim_key, dim_name in dimension_names.items():
        score = dimension_avgs.get(dim_key, 0)
        report += f"- **{dim_name}:** {score}/5.0 "

        if score >= 4:
            report += "Excellent\n"
        elif score >= 3:
            report += "Good\n"
        elif score >= 2:
            report += "Fair - needs improvement\n"
        else:
            report += "Poor - requires attention\n"

    report += f"""

---

## Recommendations / 建议

### For Dataset Improvement / 数据集改进建议

"""

    # Analyze lowest dimension
    lowest_dim = min(dimension_avgs.items(), key=lambda x: x[1])
    lowest_score = lowest_dim[1]
    lowest_dim_name = dimension_names[lowest_dim[0]]

    if lowest_score < 3:
        report += f"1. **Priority: Improve {lowest_dim_name}** - Average score of {lowest_score}/5.0 indicates systemic issues\n"

    # Check rejection reasons
    if top_rejections:
        top_reason = top_rejections[0]['reason']
        report += f"2. **Address Top Rejection Reason:** '{top_reason}' accounts for {top_rejections[0]['percentage']}% of failures\n"

    report += f"""
3. **Maintain Strengths:** Preserve high-quality task characteristics in future dataset generation

### For Agent Testing / 智能体测试建议

- Use {basic_stats['high_quality_tasks']:,} high-quality tasks for benchmark evaluation
- Review failed tasks to understand common failure modes
- Consider curating subset of tasks by department (e.g., Nephrology-only evaluation)

---

*Report generated by Clinical Consultation Quality Statistics Calculator v1.0*
"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"{Colors.OKGREEN}[INFO]{Colors.ENDC} Markdown report saved to: {output_path}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function."""

    print("=" * 80)
    print(f"{Colors.HEADER}CLINICAL CONSULTATION TASK QUALITY STATISTICS CALCULATOR")
    print(f"{Colors.HEADER}临床咨询任务质量统计计算器")
    print("=" * 80)
    print()

    try:
        # Load data files
        print(f"{Colors.BOLD}[Step 1/5] Loading data files...{Colors.ENDC}")
        print()

        filtered_tasks = load_filtered_tasks(StatisticsConfig.TASKS_FILTERED_PATH)
        review_scores = load_review_scores(StatisticsConfig.REVIEW_SCORES_PATH)
        print()

        # Calculate statistics
        print(f"{Colors.BOLD}[Step 2/5] Calculating statistics...{Colors.ENDC}")
        print()

        basic_stats = calculate_basic_statistics(filtered_tasks, review_scores)
        dept_breakdown = calculate_department_breakdown(filtered_tasks)
        top_rejections = calculate_top_rejection_reasons(review_scores, top_n=3)
        distribution = calculate_score_distribution(review_scores)
        dimension_avgs = calculate_dimension_averages(review_scores)
        print()

        # Save reports
        print(f"{Colors.BOLD}[Step 3/5] Saving reports...{Colors.ENDC}")
        print()

        save_json_report(
            basic_stats, dept_breakdown, top_rejections,
            distribution, dimension_avgs,
            StatisticsConfig.OUTPUT_JSON_PATH
        )

        save_markdown_report(
            basic_stats, dept_breakdown, top_rejections,
            distribution, dimension_avgs,
            StatisticsConfig.OUTPUT_MD_PATH
        )
        print()

        # Print console report
        print(f"{Colors.BOLD}[Step 4/5] Console report{Colors.ENDC}")
        print()

        print_console_report(
            basic_stats, dept_breakdown, top_rejections,
            distribution, dimension_avgs
        )

        # Final summary
        print()
        print("=" * 80)
        print(f"{Colors.OKGREEN}PROCESSING COMPLETE{Colors.ENDC}")
        print("=" * 80)
        print()
        print(f"Output files saved:")
        print(f"  • JSON report: {StatisticsConfig.OUTPUT_JSON_PATH}")
        print(f"  • Markdown report: {StatisticsConfig.OUTPUT_MD_PATH}")
        print()
        print(f"{Colors.BOLD}Summary:{Colors.ENDC}")
        print(f"  Total tasks:    {basic_stats['total_raw_tasks']:,}")
        print(f"  High quality:   {basic_stats['high_quality_tasks']:,} ({basic_stats['pass_rate']}%)")
        print(f"  Failed:         {basic_stats['failed_tasks']:,} ({basic_stats['fail_rate']}%)")
        print()
        print("=" * 80)

    except FileNotFoundError as e:
        print(f"{Colors.FAIL}[ERROR]{Colors.ENDC} {e}")
        print()
        print(f"{Colors.WARNING}[INFO]{Colors.ENDC} Please ensure the following files exist:")
        print(f"  - {StatisticsConfig.TASKS_FILTERED_PATH}")
        print(f"  - {StatisticsConfig.REVIEW_SCORES_PATH}")

    except json.JSONDecodeError as e:
        print(f"{Colors.FAIL}[ERROR]{Colors.ENDC} JSON decode error: {e}")

    except Exception as e:
        print(f"{Colors.FAIL}[ERROR]{Colors.ENDC} Unexpected error: {e}")


if __name__ == "__main__":
    main()
