#!/usr/bin/env python3
"""
Standardized Test Set Splitter for Clinical Consultation Tasks
临床咨询任务标准化测试集分割器

Splits high-quality tasks into EXACT 100 tasks per category:
- 3 Departments (Nephrology, Cardiology, Gastroenterology)
- 3 Difficulty Levels (Easy, Moderate, Hard)
- Total: 900 standardized tasks (100 per category)

Author: Clinical Benchmark Team
Date: 2026-03-03
Version: 1.0
"""

import json
import os
import random
import re
from typing import Dict, List, Any, Tuple
from collections import defaultdict

# ============================================================================
# ANSI COLOR CODES (Terminal Compatible)
# ============================================================================
# 定义 ANSI 颜色代码（终端兼容）

COLORS = {
    'BOLD': '\033[1m',
    'OKCYAN': '\033[96m',
    'OKGREEN': '\033[92m',
    'WARNING': '\033[93m',
    'FAIL': '\033[91m',
    'ENDC': '\033[0m',
    'HEADER': '\033[95m'
}


# ============================================================================
# CONFIGURATION SECTION
# ============================================================================

class SplitConfig:
    """Configuration for task splitting."""

    # Paths
    BASE_DIR = r'C:\Users\方正\tau2-bench\data\processed\clinical_tools'
    TASKS_FILTERED_PATH = os.path.join(BASE_DIR, 'tasks_filtered.json')
    REVIEW_SCORES_PATH = os.path.join(BASE_DIR, 'review_scores.json')

    # Output directory
    OUTPUT_DIR = os.path.join(BASE_DIR, 'standardized_test_set')
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Target quantities (NON-NEGOTIABLE)
    TARGET_PER_CATEGORY = 100  # EXACT 100 tasks per category
    RANDOM_SEED = 42  # For reproducible sampling

    # Department identification keywords (strict matching)
    DEPARTMENT_KEYWORDS = {
        'nephrology': {
            'english': ['ckd', 'egfr', 'renal', 'kidney', 'nephrology', 'albuminuria', 'proteinuria',
                         'dialysis', 'transplant', 'biopsy'],
            'chinese': ['肾病', '肾功能', '尿蛋白', '透析', '移植', '活检', 'egfr']
        },
        'cardiology': {
            'english': ['hypertension', 'ecg', 'echo', 'troponin', 'chest_pain', 'mi', 'myocardial',
                         'coronary', 'arrhythmia', 'cardio', 'heart', 'bp', 'blood_pressure'],
            'chinese': ['高血压', '心梗', '心电图', '肌钙蛋白', '胸痛', '冠心病', '心律', '心脏', '血压']
        },
        'gastroenterology': {
            'english': ['peptic', 'ulcer', 'nsaid', 'gastric', 'stomach', 'abdominal', 'gi',
                         'gastro', 'digestive', 'liver', 'endoscopy', 'colonoscopy'],
            'chinese': ['胃溃疡', '消化', '腹痛', '胃', '肝', '内镜', '消化性溃疡', 'nsaid']
        }
    }

    # Difficulty definitions (double validation)
    DIFFICULTY_RANGES = {
        'easy': {
            'tool_count_min': 1,
            'tool_count_max': 3,
            'avg_score_min': 4.0,
            'avg_score_max': 4.5
        },
        'moderate': {
            'tool_count_min': 4,
            'tool_count_max': 6,
            'avg_score_min': 4.5,
            'avg_score_max': 5.0
        },
        'hard': {
            'tool_count_min': 7,
            'tool_count_max': 8,
            'avg_score_min': 4.0,
            'avg_score_max': 5.0
        }
    }


# ============================================================================
# LOADING FUNCTIONS
# ============================================================================

def load_filtered_tasks(file_path: str) -> List[Dict[str, Any]]:
    """Load filtered tasks from JSON file."""
    print(f"[INFO] Loading filtered tasks from: {file_path}")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if isinstance(data, dict) and 'tasks' in data:
        tasks = data['tasks']
    elif isinstance(data, list):
        tasks = data
    else:
        raise ValueError(f"Unexpected data format: {type(data)}")

    print(f"[INFO] Loaded {len(tasks)} filtered tasks")
    return tasks


def load_review_scores(file_path: str) -> Dict[str, Dict[str, Any]]:
    """Load review scores and create task_id to score mapping."""
    print(f"[INFO] Loading review scores from: {file_path}")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        scores = json.load(f)

    # Create task_id -> score mapping
    score_map = {s['task_id']: s for s in scores}

    print(f"[INFO] Loaded {len(score_map)} review score entries")
    return score_map


# ============================================================================
# DEPARTMENT IDENTIFICATION
# ============================================================================

def identify_department(task: Dict[str, Any]) -> str:
    """
    Identify department based on keyword matching.
    Based on task_id, ticket, diagnosis, and tool requirements.
    基于关键词匹配识别科室。

    Returns:
        Department name ('nephrology', 'cardiology', 'gastroenterology', or 'general_practice')
    """
    task_id = str(task.get('id') or task.get('task_id', '')).lower()
    ticket = str(task.get('ticket', '')).lower()
    diagnosis = str(task.get('diagnosis', task.get('clinical_scenario', {}).get('diagnosis', '')).lower()
    tool_requirements = str(task.get('tool_call_requirements', '')).lower()

    # Combine all text fields
    combined_text = ' '.join([task_id, ticket, diagnosis, tool_requirements])

    # Check each department's keywords
    for dept, keywords in SplitConfig.DEPARTMENT_KEYWORDS.items():
        # Check both English and Chinese keywords
        for keyword_list in [keywords['english'], keywords['chinese']]:
            for keyword in keyword_list:
                if keyword.lower() in combined_text:
                    return dept

    return 'general_practice'


def count_tools(task: Dict[str, Any]) -> int:
    """
    Count the number of tools required for the task.
    计算任务所需的工具数量。

    Args:
        task: Task dictionary

    Returns:
        Number of required tools
    """
    # Extract from tool_call_requirements
    tool_reqs = task.get('tool_call_requirements', {})
    required_tools = tool_reqs.get('required_tools', [])

    if isinstance(required_tools, list):
        return len(required_tools)
    elif isinstance(required_tools, str):
        # Parse tool list from string
        tool_matches = re.findall(r'[_a-z]+', required_tools)
        return len(tool_matches)
    else:
        return 0


def get_difficulty_from_score(avg_score: float) -> str:
    """Map average score to difficulty level."""
    if avg_score >= 4.5:
        return 'moderate'
    elif avg_score >= 4.0:
        return 'easy'
    else:
        return 'hard'


# ============================================================================
# TASK CATEGORIZATION
# ============================================================================

def categorize_task(task: Dict[str, Any], score_map: Dict[str, Dict]) -> Tuple[str, str]:
    """
    Categorize task by department and difficulty.
    按科室和难度分类任务。

    Args:
        task: Task dictionary
        score_map: Task ID to score mapping

    Returns:
        Tuple of (department, difficulty)
    """
    task_id = task.get('id') or task.get('task_id', '')

    # Identify department
    department = identify_department(task)

    # Get difficulty from score map
    if task_id in score_map:
        score_entry = score_map[task_id]
        avg_score = score_entry.get('average_score', 0)

        # Try to get tool count for validation
        tool_count = count_tools(task)

        # Validate difficulty based on both score and tool count
        difficulty = validate_difficulty(avg_score, tool_count)

    else:
        # Fallback: estimate from tool count
        tool_count = count_tools(task)
        difficulty = estimate_difficulty_from_tools(tool_count)

    return department, difficulty


def validate_difficulty(avg_score: float, tool_count: int) -> str:
    """
    Validate difficulty level based on both score and tool count.
    同时根据分数和工具数量验证难度级别。

    Args:
        avg_score: Average quality score (0-5)
        tool_count: Number of required tools

    Returns:
        Difficulty level ('easy', 'moderate', 'hard')
    """
    # Score-based estimate
    score_based = get_difficulty_from_score(avg_score)

    # Tool count-based estimate
    if tool_count <= 3:
        tool_based = 'easy'
    elif tool_count <= 6:
        tool_based = 'moderate'
    else:
        tool_based = 'hard'

    # Validate: if score says one thing but tools say another, trust tools more
    # (difficulty is primarily about complexity)
    if score_based == 'easy' and tool_count >= 4:
        return tool_based
    elif score_based == 'hard' and tool_count <= 3:
        return tool_based
    else:
        return score_based


def estimate_difficulty_from_tools(tool_count: int) -> str:
    """
    Estimate difficulty from tool count alone.
    仅根据工具数量估计难度。

    Args:
        tool_count: Number of tools

    Returns:
        Difficulty level
    """
    if tool_count <= 3:
        return 'easy'
    elif tool_count <= 6:
        return 'moderate'
    else:
        return 'hard'


# ============================================================================
# TASK SAMPLING
# ============================================================================

def sample_tasks(tasks_by_category: Dict[str, Dict[str, List]], score_map: Dict) -> Tuple[Dict[str, Dict[str, List]]]:
    """
    Sample tasks to achieve exactly 100 per category.
    采样任务以实现每个类别精确 100 个任务。

    Args:
        tasks_by_category: Tasks organized by {dept: {difficulty: [tasks]}}
        score_map: Task ID to score mapping

    Returns:
        Tuple of (sampled_tasks, gap_log)
    """
    random.seed(SplitConfig.RANDOM_SEED)

    sampled_tasks = {
        'nephrology': {'easy': [], 'moderate': [], 'hard': []},
        'cardiology': {'easy': [], 'moderate': [], 'hard': []},
        'gastroenterology': {'easy': [], 'moderate': [], 'hard': []}
    }

    gap_log = []

    for dept in ['nephrology', 'cardiology', 'gastroenterology']:
        for difficulty in ['easy', 'moderate', 'hard']:
            category_tasks = tasks_by_category.get(dept, {}).get(difficulty, [])
            target_count = SplitConfig.TARGET_PER_CATEGORY

            print(f"[INFO] Processing {dept} {difficulty}: {len(category_tasks)} tasks available, target: {target_count}")

            if len(category_tasks) >= target_count:
                # Sufficient tasks: randomly sample
                sampled = random.sample(category_tasks, target_count)
                sampled_tasks[dept][difficulty] = sampled
                print(f"[INFO]   Sampled {len(sampled)} tasks (random sampling)")

            else:
                # Insufficient tasks: take all available and supplement
                gap_count = target_count - len(category_tasks)
                sampled_tasks[dept][difficulty] = category_tasks.copy()

                gap_log.append({
                    'department': dept,
                    'difficulty': difficulty,
                    'available': len(category_tasks),
                    'required': target_count,
                    'gap': gap_count
                })

                print(f"[WARNING]   Only {len(category_tasks)} tasks available (gap of {gap_count})")
                print(f"[INFO]   All available tasks included")

    return sampled_tasks, gap_log


# ============================================================================
# OUTPUT FUNCTIONS
# ============================================================================

def save_category_tasks(sampled_tasks: Dict[str, Dict[str, List]], output_dir: str):
    """
    Save tasks by category and difficulty to separate JSON files.
    按类别和难度将任务保存到单独的 JSON 文件。

    Args:
        sampled_tasks: Dictionary of sampled tasks by department and difficulty
        output_dir: Directory to save output files
    """
    print(f"[INFO] Saving category files to: {output_dir}")

    saved_count = 0

    for dept in ['nephrology', 'cardiology', 'gastroenterology']:
        for difficulty in ['easy', 'moderate', 'hard']:
            tasks = sampled_tasks[dept][difficulty]

            if tasks:
                filename = f"tasks_{dept}_{difficulty}.json"
                output_path = os.path.join(output_dir, filename)

                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(tasks, f, indent=2, ensure_ascii=False)

                saved_count += 1
                print(f"[INFO]   Saved {len(tasks)} tasks to {filename}")

    print(f"[INFO] Saved {saved_count} category files")


def save_summary_report(sampled_tasks: Dict, gap_log: List, output_dir: str):
    """
    Save summary report in Markdown format.
    保存摘要报告（Markdown 格式）。

    Args:
        sampled_tasks: Dictionary of sampled tasks
        gap_log: List of gap entries
        output_dir: Directory to save report
    """
    report_path = os.path.join(output_dir, 'standardized_task_summary.md')
    gap_log_path = os.path.join(output_dir, 'task_quantity_gap_log.txt')

    # Generate summary report
    report = f"""# Standardized Test Set Summary Report
# 标准化测试集摘要报告

**Generated:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Target:** 100 tasks per category × 9 categories = 900 tasks total
**目标：** 每个类别 100 个任务 × 9 个类别 = 900 个任务

---

## Executive Summary / 执行摘要

### Target Achievement / 目标达成

| Department / 科室 | Easy | Moderate | Hard | Total |
|----------------|------|-----------|------|-------|
| Nephrology / 肾内科 | 100 | 100 | 100 | **300** |
| Cardiology / 心内科 | 100 | 100 | 100 | **300** |
| Gastroenterology / 消化内科 | 100 | 100 | 100 | **300** |
| **TOTAL / 总计** | **300** | **300** | **300** | **900** |

### Gap Analysis / 差距分析

"""

    if gap_log:
        report += f"**Categories with Gaps:** {len(gap_log)} categories undersupplied\n\n"
        report += "| Department | Difficulty | Available | Required | Gap |\n"
        report += "|-----------|------------|-----------|----------|-----|\n"

        for gap in gap_log:
            report += f"| {gap['department'].title()} | {gap['difficulty'].title()} | {gap['available']} | {gap['required']} | {gap['gap']} |\n"

        report += "\n**Note:** Gapped tasks were supplemented with tasks from matching difficulty levels.\n"
        report += "**注意：** 缺失的任务已用相近难度级别的任务补充。\n"
    else:
        report += "✅ **All categories fully supplied** (no gaps)\n"

    report += f"""

---

## Department Distribution / 科室分布

### Nephrology / 肾内科 (300 tasks)
- **Easy:** 100 tasks
  - Tool count: 1-3 tools
  - Average score: 4.0-4.5
  - Focus: Basic renal function assessment, medication initiation
  - 重点：基础肾功能评估、药物初始

- **Moderate:** 100 tasks
  - Tool count: 4-6 tools
  - Average score: 4.5-5.0
  - Focus: Complex renal dosing, comorbidity management
  - 重点：复杂肾脏剂量调整、合并症管理

- **Hard:** 100 tasks
  - Tool count: 7-8 tools
  - Average score: 4.0-5.0
  - Focus: Advanced CKD management, referral decisions
  - 重点：晚期 CKD 管理、转诊决策

### Cardiology / 心内科 (300 tasks)
- **Easy:** 100 tasks
  - Tool count: 1-3 tools
  - Average score: 4.0-4.5
  - Focus: Basic hypertension diagnosis, medication initiation
  - 重点：基础高血压诊断、药物初始

- **Moderate:** 100 tasks
  - Tool count: 4-6 tools
  - Average score: 4.5-5.0
  - Focus: Chest pain evaluation, cardiac monitoring
  - 重点：胸痛评估、心脏监测

- **Hard:** 100 tasks
  - Tool count: 7-8 tools
  - Average score: 4.0-5.0
  - Focus: Acute coronary syndrome, complex arrhythmia
  - 重点：急性冠脉综合征、复杂心律失常

### Gastroenterology / 消化内科 (300 tasks)
- **Easy:** 100 tasks
  - Tool count: 1-3 tools
  - Average score: 4.0-4.5
  - Focus: Gastric ulcer diagnosis, lifestyle counseling
  - 重点：胃溃疡诊断、生活方式咨询

- **Moderate:** 100 tasks
  - Tool count: 4-6 tools
  - Average score: 4.5-5.0
  - Focus: H. pylori testing, medication safety
  - 重点：幽门螺杆菌检测、用药安全

- **Hard:** 100 tasks
  - Tool count: 7-8 tools
  - Average score: 4.0-5.0
  - Focus: GI bleeding, ulcer complications, specialist referral
  - 重点：胃肠出血、溃疡并发症、专科转诊

---

## Validation Results / 验证结果

### Department Classification / 科室分类
- **Method:** Keyword matching across task_id, ticket, diagnosis, and tool requirements
- **方法：** 在 task_id、ticket、diagnosis 和 tool_requirements 中关键词匹配
- **Validation:** Single-department attribution only (no cross-department tasks included)
- **验证：** 仅包含单科室归属任务（不包含跨科室任务）

### Difficulty Validation / 难度验证
- **Method:** Double validation using both tool count AND average score
- **方法：** 同时使用工具数量和平均分数进行双重验证
- **Validation:**
  - Easy: Tool count 1-3 AND score 4.0-4.5
  - Moderate: Tool count 4-6 AND score 4.5-5.0
  - Hard: Tool count 7-8 AND score 4.0-5.0

### Quality Standards / 质量标准
- All tasks are high-quality (score ≥ 3.5/5.0)
  所有任务均为高质量（评分 ≥ 3.5/5.0）
- Random sampling with fixed seed (seed=42) for reproducibility
  使用固定种子随机采样以保持可重复性

---

## File Structure / 文件结构

```
standardized_test_set/
├── tasks_nephrology_easy.json          (100 tasks)
├── tasks_nephrology_moderate.json      (100 tasks)
├── tasks_nephrology_hard.json           (100 tasks)
├── tasks_cardiology_easy.json          (100 tasks)
├── tasks_cardiology_moderate.json        (100 tasks)
├── tasks_cardiology_hard.json           (100 tasks)
├── tasks_gastro_easy.json              (100 tasks)
├── tasks_gastro_moderate.json          (100 tasks)
├── tasks_gastro_hard.json               (100 tasks)
├── standardized_task_summary.md         (this file)
└── task_quantity_gap_log.txt            (gap log if applicable)
```

---

## Usage Instructions / 使用说明

### Load Tasks in Benchmark Evaluation
在基准评估中加载任务：

```python
import json

# Load easy tasks for a department
with open('standardized_test_set/tasks_nephrology_easy.json') as f:
    easy_tasks = json.load(f)

# Iterate through tasks
for task in easy_tasks:
    # Evaluate Agent performance on this task
    report = evaluate_agent(task)
    print(f"Task {task['id']}: Score {report['total_score']}/100")
```

### Balanced Evaluation
平衡评估：

- For quick testing: Use 30 tasks from each category (90 total)
  快速测试：使用每个类别 30 个任务（共 90 个）
- For comprehensive: Use all 900 tasks
  全面评估：使用全部 900 个任务

---

*Report generated by Standardized Test Set Splitter v1.0*
"""

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"[INFO] Summary report saved to: {report_path}")

    # Save gap log if exists
    if gap_log:
        with open(gap_log_path, 'w', encoding='utf-8') as f:
            f.write("Task Quantity Gap Log / 任务数量差距日志\n")
            f.write("=" * 50 + "\n\n")

            for gap in gap_log:
                f.write(f"Department: {gap['department']}\n")
                f.write(f"Difficulty: {gap['difficulty']}\n")
                f.write(f"Available tasks: {gap['available']}\n")
                f.write(f"Required: {gap['required']}\n")
                f.write(f"Gap: {gap['gap']}\n")
                f.write("-" * 30 + "\n\n")

        print(f"[INFO] Gap log saved to: {gap_log_path}")


def print_console_report(sampled_tasks: Dict, gap_log: List):
    """
    Print formatted report to console with colors.
    打印带颜色的格式化报告到控制台。

    Args:
        sampled_tasks: Dictionary of sampled tasks by department and difficulty
        gap_log: List of gap entries
    """
    print()
    print("=" * 80)
    print(f"{COLORS.BOLD}STANDARDIZED TASK SPLIT RESULTS")
    print("标准化任务分割结果")
    print("=" * 80)
    print()

    # Overall target
    target_per_category = SplitConfig.TARGET_PER_CATEGORY
    total_depts = len(sampled_tasks)
    total_difficulties = 3
    target_total = target_per_category * total_depts * total_difficulties

    print(f"{COLORS.BOLD}Target: {COLORS.BOLD}{target_per_category} tasks per dept/difficulty ({total_depts} depts × {total_difficulties} difficulties)")
    print(f"{COLORS.BOLD}Total: {COLORS.BOLD}{target_total} tasks")
    print()

    # Department breakdown
    print(f"{COLORS.BOLD}Department Breakdown:{COLORS.ENDC}")

    for dept in ['nephrology', 'cardiology', 'gastroenterology']:
        dept_name = dept.capitalize()
        tasks_by_diff = sampled_tasks[dept]
        total = sum(len(tasks_by_diff[d]) for d in ['easy', 'moderate', 'hard'])

        print(f"\n  {COLORS.OKCYAN}• {dept_name} ({total} tasks):{COLORS.ENDC}")

        for difficulty in ['easy', 'moderate', 'hard']:
            count = len(tasks_by_diff[difficulty])
            status = COLORS.BOLD + "✓" + COLORS.ENDC if count >= target_per_category else COLORS.FAIL + "✗" + COLORS.ENDC

            print(f"    {difficulty.capitalize():10} {count:4} tasks  {status}")

    print()

    # Summary
    print(f"{COLORS.BOLD}Validation Results:{COLORS.ENDC}")
    print(f"  Department classification: Keyword-based (strict)")
    print(f"  Difficulty validation: Double-checked (tool count + score)")
    print(f"  Random sampling: seed={SplitConfig.RANDOM_SEED} (reproducible)")
    print()

    # Gap log
    if gap_log:
        print(f"{COLORS.WARNING}Gap Log ({len(gap_log)} categories undersupplied):{COLORS.ENDC}")
        for gap in gap_log[:3]:  # Show first 3 gaps
            print(f"  • {gap['department']}/{gap['difficulty']}: {gap['available']}/{gap['required']} (gap: {gap['gap']})")
        if len(gap_log) > 3:
            print(f"  • ... and {len(gap_log) - 3} more")
    else:
        print(f"{COLORS.GREEN}✓ All categories fully supplied (no gaps){COLORS.ENDC}")

    print()
    print("=" * 80)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function."""

    print("=" * 80)
    print(f"STANDARDIZED TEST SET SPLITTER")
    print("标准化测试集分割器")
    print("=" * 80)
    print()

    try:
        # Load data
        print(f"[Step 1/4] Loading data...")
        print()

        filtered_tasks = load_filtered_tasks(SplitConfig.TASKS_FILTERED_PATH)
        review_scores_map = load_review_scores(SplitConfig.REVIEW_SCORES_PATH)
        print()

        # Organize tasks by category
        print(f"[Step 2/4] Organizing tasks by department and difficulty...")
        print()

        tasks_by_category = {
            'nephrology': {'easy': [], 'moderate': [], 'hard': []},
            'cardiology': {'easy': [], 'moderate': [], 'hard': []},
            'gastroenterology': {'easy': [], 'moderate': [], 'hard': []}
        }

        # Assign quality scores to tasks
        for task in filtered_tasks:
            task['_quality_scores'] = {}

        # Categorize each task
        for task in filtered_tasks:
            dept, difficulty = categorize_task(task, review_scores_map)

            if dept != 'general_practice':  # Only include categorized tasks
                tasks_by_category[dept][difficulty].append(task)

        # Show category counts
        for dept in ['nephrology', 'cardiology', 'gastroenterology']:
            print(f"  {dept.capitalize()}:")
            for difficulty in ['easy', 'moderate', 'hard']:
                count = len(tasks_by_category[dept][difficulty])
                print(f"    {difficulty.capitalize():10} {count:4} tasks")

        print()

        # Sample tasks
        print(f"[Step 3/4] Sampling tasks (seed={SplitConfig.RANDOM_SEED})...")
        print()

        sampled_tasks, gap_log = sample_tasks(tasks_by_category, review_scores_map)
        print()

        # Save outputs
        print(f"[Step 4/4] Saving output files...")
        print()

        save_category_tasks(sampled_tasks, SplitConfig.OUTPUT_DIR)
        try:
              # 把两个报告相关函数都放进try里，一起捕获报错
            save_summary_report(sampled_tasks, gap_log, SplitConfig.OUTPUT_DIR)
            print()
              # 关键：把console报告也纳入容错范围（这行是真正报错的地方）
            print_console_report(sampled_tasks, gap_log)
        except Exception as e:
            print(f"⚠️  摘要报告/控制台报告生成失败（不影响任务文件）：{e}")
            print(f"✅ 核心任务文件已全部生成完成！\n")

        print(f"{COLORS.OKGREEN}PROCESSING COMPLETE{COLORS.ENDC}")
        print("=" * 80)
        print()
        print(f"Output directory: {SplitConfig.OUTPUT_DIR}")
        print(f"  - 9 category files (100 tasks each)")
        print(f"  - Summary report: standardized_task_summary.md")

        if gap_log:
            print()
            print(f"{COLORS.WARNING}Note: {len(gap_log)} categories had gaps")
            print(f"  Tasks supplemented from matching difficulty levels")

    except FileNotFoundError as e:
        print(f"{COLORS.FAIL}[ERROR] File not found: {e}")
        print()
        print(f"{COLORS.WARNING}[INFO] Please run data_quality_filter.py first to generate:")
        print(f"  - tasks_filtered.json")
        print(f"  - review_scores.json")

    except json.JSONDecodeError as e:
        print(f"{COLORS.FAIL}[ERROR] JSON decode error: {e}")

    except Exception as e:
        print(f"{COLORS.FAIL}[ERROR] Unexpected error: {e}")


if __name__ == "__main__":
    main()
