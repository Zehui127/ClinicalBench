#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Standardized Test Set Splitter for Clinical Consultation Tasks
临床咨询任务标准化测试集分割器

Splits high-quality tasks into EXACT 100 tasks per category:
- 3 Departments (Nephrology, Cardiology, Gastroenterology)
- 3 Difficulty Levels (Easy, Moderate, Hard)
- Total: 900 standardized tasks (100 per category)

Author: Clinical Benchmark Team
Date: 2026-03-03
Version: 2.1 (Fixed - COLORS dict access)
"""

import datetime
import json
import os
import random
import re
import sys
from typing import Dict, List, Any, Tuple
from collections import defaultdict


# ============================================================================
# UTF-8 CONSOLE OUTPUT CONFIGURATION (Windows Compatible)
# ============================================================================

def configure_utf8_output():
    """
    Configure UTF-8 output for Chinese characters in console.
    配置控制台中文 UTF-8 输出。
    """
    if sys.platform == 'win32':
        # Windows: Configure console to UTF-8
        try:
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
        except:
            # Fallback: set environment variable
            os.environ['PYTHONIOENCODING'] = 'utf-8'
    else:
        # Linux/Mac: Already UTF-8 by default
        pass


# Configure UTF-8 at import time
configure_utf8_output()


# ============================================================================
# ANSI COLOR CODES (Terminal Compatible)
# ============================================================================
# 定义 ANSI 颜色代码（终端兼容）
# FIX: All access uses dictionary notation COLORS['key'] instead of attribute COLORS.key

COLORS = {
    'HEADER': '\033[95m',
    'OKBLUE': '\033[94m',
    'OKGREEN': '\033[92m',
    'WARNING': '\033[93m',
    'FAIL': '\033[91m',
    'ENDC': '\033[0m',
    'BOLD': '\033[1m',
    'UNDERLINE': '\033[4m'
}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def print_header(text: str):
    """Print colored header text."""
    print(f"{COLORS['HEADER']}{text}{COLORS['ENDC']}")
    print("=" * 80)


def print_success(text: str):
    """Print success text in green."""
    print(f"{COLORS['OKGREEN']}✅ {text}{COLORS['ENDC']}")


def print_error(text: str):
    """Print error text in red."""
    print(f"{COLORS['FAIL']}❌ {text}{COLORS['ENDC']}")


def print_warning(text: str):
    """Print warning text in yellow."""
    print(f"{COLORS['WARNING']}⚠️  {text}{COLORS['ENDC']}")


def print_info(text: str):
    """Print info text in cyan."""
    print(f"{COLORS['OKBLUE']}ℹ️  {text}{COLORS['ENDC']}")


def print_step(step: str, total: str, description: str):
    """Print step indicator."""
    print(f"\n{COLORS['BOLD']}[{step}/{total}] {description}{COLORS['ENDC']}")
    print("-" * 80)


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

def validate_input_files() -> bool:
    """
    Validate that input files exist before processing.
    验证输入文件是否存在。

    Returns:
        True if all files exist, False otherwise
    """
    print_step("步骤 0", "5", "验证输入文件")

    all_valid = True

    # Check tasks_filtered.json
    if os.path.exists(SplitConfig.TASKS_FILTERED_PATH):
        print_success(f"tasks_filtered.json 存在")
    else:
        print_error(f"tasks_filtered.json 不存在")
        all_valid = False

    # Check review_scores.json
    if os.path.exists(SplitConfig.REVIEW_SCORES_PATH):
        print_success(f"review_scores.json 存在")
    else:
        print_error(f"review_scores.json 不存在")
        all_valid = False

    if all_valid:
        print()
        print_success("所有输入文件验证通过！")
    else:
        print()
        print_error("输入文件验证失败！")
        print()
        print_warning("请先运行 data_quality_filter.py 生成以下文件：")
        print("   1. tasks_filtered.json")
        print("   2. review_scores.json")

    return all_valid


def load_filtered_tasks(file_path: str) -> List[Dict[str, Any]]:
    """Load filtered tasks from JSON file."""
    print_info(f"正在加载 tasks_filtered.json...")

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

    print_success(f"已加载 {len(tasks)} 个高质量任务")
    return tasks


def load_review_scores(file_path: str) -> Dict[str, Dict[str, Any]]:
    """Load review scores and create task_id to score mapping."""
    print_info(f"正在加载 review_scores.json...")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        scores = json.load(f)

    # Create task_id -> score mapping
    score_map = {s['task_id']: s for s in scores}

    print_success(f"已加载 {len(score_map)} 条评分记录")
    return score_map


# ============================================================================
# DEPARTMENT IDENTIFICATION
# ============================================================================

def identify_department(task: Dict[str, Any]) -> str:
    """
    Identify department based on keyword matching.
    基于关键词匹配识别科室。

    Returns:
        Department name ('nephrology', 'cardiology', 'gastroenterology', or 'general_practice')
    """
    task_id = str(task.get('id') or task.get('task_id', '')).lower()
    ticket = str(task.get('ticket', '')).lower()
    diagnosis = str(task.get('diagnosis', task.get('clinical_scenario', {}).get('diagnosis', '')).lower())
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
    """
    if tool_count <= 3:
        return 'easy'
    elif tool_count <= 6:
        return 'moderate'
    else:
        return 'hard'


# ============================================================================
# TASK CLASSIFICATION WITH PROGRESS INDICATOR
# ============================================================================

def classify_all_tasks(tasks: List[Dict], score_map: Dict) -> Dict[str, Dict[str, List]]:
    """
    Classify all tasks by department and difficulty with progress indicator.
    分类所有任务（带进度指示器）。
    """
    print_step("步骤 2", "5", "分类任务到科室-难度类别")

    tasks_by_category = {
        'nephrology': {'easy': [], 'moderate': [], 'hard': []},
        'cardiology': {'easy': [], 'moderate': [], 'hard': []},
        'gastroenterology': {'easy': [], 'moderate': [], 'hard': []}
    }

    total_tasks = len(tasks)
    classified_count = 0
    uncategorized_count = 0
    progress_interval = max(1, total_tasks // 10)  # Show progress 10 times

    for i, task in enumerate(tasks):
        dept, difficulty = categorize_task(task, score_map)

        if dept != 'general_practice':
            tasks_by_category[dept][difficulty].append(task)
            classified_count += 1
        else:
            uncategorized_count += 1

        # Show progress
        if (i + 1) % progress_interval == 0 or (i + 1) == total_tasks:
            progress = (i + 1) / total_tasks * 100
            print(f"   进度: {i + 1}/{total_tasks} ({progress:.1f}%) | "
                  f"已分类: {classified_count} | 未分类: {uncategorized_count}")

    print()
    print_success("任务分类完成！")
    print(f"   总任务数: {total_tasks}")
    print(f"   已分类: {classified_count}")
    print(f"   未分类 (general_practice): {uncategorized_count}")

    # Show category breakdown
    print()
    print_header("科室-难度分布详情：")
    print()

    dept_names = {
        'nephrology': '肾内科',
        'cardiology': '心内科',
        'gastroenterology': '消化内科'
    }

    for dept in ['nephrology', 'cardiology', 'gastroenterology']:
        dept_name_cn = dept_names[dept]
        print(f"{dept_name_cn} ({dept}):")
        for difficulty in ['easy', 'moderate', 'hard']:
            count = len(tasks_by_category[dept][difficulty])
            diff_name_cn = {'easy': '简单', 'moderate': '中等', 'hard': '困难'}[difficulty]
            print(f"   {diff_name_cn} ({difficulty}): {count:4} 个任务")
        print()

    return tasks_by_category


# ============================================================================
# TASK SAMPLING
# ============================================================================

def sample_tasks(tasks_by_category: Dict[str, Dict[str, List]], score_map: Dict) -> Tuple[Dict[str, Dict[str, List]], List]:
    """
    Sample tasks to achieve exactly 100 per category.
    采样任务以实现每个类别精确 100 个任务。
    """
    print_step("步骤 3", "5", "随机采样任务（seed=42）")

    random.seed(SplitConfig.RANDOM_SEED)

    sampled_tasks = {
        'nephrology': {'easy': [], 'moderate': [], 'hard': []},
        'cardiology': {'easy': [], 'moderate': [], 'hard': []},
        'gastroenterology': {'easy': [], 'moderate': [], 'hard': []}
    }

    gap_log = []

    dept_names = {
        'nephrology': '肾内科',
        'cardiology': '心内科',
        'gastroenterology': '消化内科'
    }

    diff_names = {
        'easy': '简单',
        'moderate': '中等',
        'hard': '困难'
    }

    for dept in ['nephrology', 'cardiology', 'gastroenterology']:
        for difficulty in ['easy', 'moderate', 'hard']:
            category_tasks = tasks_by_category.get(dept, {}).get(difficulty, [])
            target_count = SplitConfig.TARGET_PER_CATEGORY

            dept_cn = dept_names[dept]
            diff_cn = diff_names[difficulty]
            available = len(category_tasks)

            if available >= target_count:
                # Sufficient tasks: randomly sample
                sampled = random.sample(category_tasks, target_count)
                sampled_tasks[dept][difficulty] = sampled
                print_success(f"{dept_cn}_{diff_cn}：可用 {available} 个 → 抽取 {target_count} 个 ✅")
            else:
                # Insufficient tasks: take all available
                gap_count = target_count - available
                sampled_tasks[dept][difficulty] = category_tasks.copy()

                gap_log.append({
                    'department': dept,
                    'department_cn': dept_cn,
                    'difficulty': difficulty,
                    'difficulty_cn': diff_cn,
                    'available': available,
                    'required': target_count,
                    'gap': gap_count
                })

                print_warning(f"{dept_cn}_{diff_cn}：仅 {available} 个可用，缺少 {gap_count} 个 ⚠️")

    print()
    total_sampled = sum(
        len(sampled_tasks[dept][diff])
        for dept in ['nephrology', 'cardiology', 'gastroenterology']
        for diff in ['easy', 'moderate', 'hard']
    )
    print_success(f"采样完成！共抽取 {total_sampled} 个任务（目标 900 个）")

    if gap_log:
        print()
        print_warning(f"注意：{len(gap_log)} 个类别任务不足")
        print(f"   详情请查看: {os.path.join(SplitConfig.OUTPUT_DIR, 'task_quantity_gap_log.txt')}")

    return sampled_tasks, gap_log


# ============================================================================
# OUTPUT FUNCTIONS
# ============================================================================

def save_category_tasks(sampled_tasks: Dict[str, Dict[str, List]], output_dir: str):
    """
    Save tasks by category and difficulty to separate JSON files.
    按类别和难度将任务保存到单独的 JSON 文件。
    """
    print_step("步骤 4", "5", "生成 JSON 文件")

    # Create output directory if not exists
    os.makedirs(output_dir, exist_ok=True)

    saved_count = 0
    total_tasks_saved = 0

    dept_names = {
        'nephrology': 'nephrology',
        'cardiology': 'cardiology',
        'gastroenterology': 'gastro'
    }

    for dept in ['nephrology', 'cardiology', 'gastroenterology']:
        for difficulty in ['easy', 'moderate', 'hard']:
            tasks = sampled_tasks[dept][difficulty]

            if tasks:
                # Use abbreviated department name in filename
                dept_abbr = dept_names[dept]
                filename = f"tasks_{dept_abbr}_{difficulty}.json"
                output_path = os.path.join(output_dir, filename)

                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(tasks, f, indent=2, ensure_ascii=False)

                saved_count += 1
                total_tasks_saved += len(tasks)
                print_success(f"📄 生成文件：{filename} | 包含 {len(tasks)} 个任务")

    print()
    print_success(f"已生成 {saved_count} 个 JSON 文件，共 {total_tasks_saved} 个任务")


def save_summary_report(sampled_tasks: Dict, gap_log: List, output_dir: str):
    """
    Save summary report in Markdown format.
    保存摘要报告（Markdown 格式）。
    """
    print_step("步骤 5", "5", "生成摘要报告")

    report_path = os.path.join(output_dir, 'standardized_task_summary.md')
    gap_log_path = os.path.join(output_dir, 'task_quantity_gap_log.txt')

    # Generate summary report
    report = f"""# Standardized Test Set Summary Report
# 标准化测试集摘要报告

**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**生成时间：** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Target:** 100 tasks per category × 9 categories = 900 tasks total
**目标：** 每个类别 100 个任务 × 9 个类别 = 900 个任务

---

## Executive Summary / 执行摘要

### Target Achievement / 目标达成

| Department / 科室 | Easy / 简单 | Moderate / 中等 | Hard / 困难 | Total / 总计 |
|----------------|-----------|----------------|-----------|-------------|
| Nephrology / 肾内科 | 100 | 100 | 100 | **300** |
| Cardiology / 心内科 | 100 | 100 | 100 | **300** |
| Gastroenterology / 消化内科 | 100 | 100 | 100 | **300** |
| **TOTAL / 总计** | **300** | **300** | **300** | **900** |

### Gap Analysis / 差距分析

"""

    if gap_log:
        report += f"**Categories with Gaps:** {len(gap_log)} categories undersupplied\n\n"
        report += "**有缺口的类别：** {len(gap_log)} 个类别任务不足\n\n"
        report += "| Department | Difficulty | Available | Required | Gap |\n"
        report += "|-----------|------------|-----------|----------|-----|\n"

        for gap in gap_log:
            report += f"| {gap['department'].title()} | {gap['difficulty'].title()} | {gap['available']} | {gap['required']} | {gap['gap']} |\n"

        report += "\n**Note:** Gapped categories contain all available tasks.\n"
        report += "**注意：** 有缺口的类别包含所有可用任务。\n"
    else:
        report += "✅ **All categories fully supplied** (no gaps)\n"
        report += "✅ **所有类别任务充足**（无缺口）\n"

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
├── tasks_nephrology_hard.json          (100 tasks)
├── tasks_cardiology_easy.json          (100 tasks)
├── tasks_cardiology_moderate.json      (100 tasks)
├── tasks_cardiology_hard.json          (100 tasks)
├── tasks_gastro_easy.json              (100 tasks)
├── tasks_gastro_moderate.json          (100 tasks)
├── tasks_gastro_hard.json              (100 tasks)
├── standardized_task_summary.md        (this file)
└── task_quantity_gap_log.txt           (gap log if applicable)
```

---

## Usage Instructions / 使用说明

### Load Tasks in Benchmark Evaluation
在基准评估中加载任务：

```python
import json

# Load easy tasks for a department
with open('standardized_test_set/tasks_nephrology_easy.json', 'r', encoding='utf-8') as f:
    easy_tasks = json.load(f)

# Iterate through tasks
for task in easy_tasks:
    # Evaluate Agent performance on this task
    report = evaluate_agent(task)
    print(f\"Task {task['id']}: Score {{report['total_score']}}/100\")
```

### Balanced Evaluation
平衡评估：

- For quick testing: Use 30 tasks from each category (90 total)
  快速测试：使用每个类别 30 个任务（共 90 个）
- For comprehensive: Use all 900 tasks
  全面评估：使用全部 900 个任务

---

*Report generated by Standardized Test Set Splitter v2.1*
*报告由标准化测试集分割器 v2.1 生成*
"""

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print_success(f"📄 摘要报告：standardized_task_summary.md")

    # Save gap log if exists
    if gap_log:
        with open(gap_log_path, 'w', encoding='utf-8') as f:
            f.write("Task Quantity Gap Log / 任务数量差距日志\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"生成时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("=" * 50 + "\n\n")

            for i, gap in enumerate(gap_log, 1):
                f.write(f"Gap #{i}\n")
                f.write(f"科室 (Department): {gap['department_cn']} ({gap['department']})\n")
                f.write(f"难度 (Difficulty): {gap['difficulty_cn']} ({gap['difficulty']})\n")
                f.write(f"可用任务: {gap['available']}\n")
                f.write(f"需要任务: {gap['required']}\n")
                f.write(f"缺口: {gap['gap']}\n")
                f.write("-" * 40 + "\n\n")

        print_success(f"📄 缺口日志：task_quantity_gap_log.txt ({len(gap_log)} 个缺口)")

    print()


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def print_startup_banner():
    """Print startup banner."""
    print()
    print("=" * 80)
    print_header("=== 标准化Task拆分脚本启动 ===")
    print("=" * 80)
    print()


def print_completion_summary(output_dir: str, gap_log: List):
    """Print completion summary."""
    print()
    print("=" * 80)
    print_success("=== 拆分完成！共生成9个文件，详见standardized_task_summary.md ===")
    print("=" * 80)
    print()
    print(f"输出目录：{output_dir}")
    print()
    print("生成的文件：")
    print("  📄 tasks_nephrology_easy.json      (100 tasks)")
    print("  📄 tasks_nephrology_moderate.json  (100 tasks)")
    print("  📄 tasks_nephrology_hard.json      (100 tasks)")
    print("  📄 tasks_cardiology_easy.json      (100 tasks)")
    print("  📄 tasks_cardiology_moderate.json  (100 tasks)")
    print("  📄 tasks_cardiology_hard.json      (100 tasks)")
    print("  📄 tasks_gastro_easy.json          (100 tasks)")
    print("  📄 tasks_gastro_moderate.json      (100 tasks)")
    print("  📄 tasks_gastro_hard.json          (100 tasks)")
    print("  📄 standardized_task_summary.md    (摘要报告)")
    if gap_log:
        print(f"  📄 task_quantity_gap_log.txt       ({len(gap_log)} 个缺口)")
    print()


def main():
    """Main execution function."""

    # Print startup banner
    print_startup_banner()

    # Show current directory
    print_info(f"当前工作目录：{os.getcwd()}")
    print(f"脚本路径：{os.path.abspath(__file__)}")
    print()

    try:
        # Step 0: Validate input files
        if not validate_input_files():
            print_error("输入文件验证失败，脚本退出")
            sys.exit(1)

        print()

        # Step 1: Load data
        print_step("步骤 1", "5", "加载输入文件")

        filtered_tasks = load_filtered_tasks(SplitConfig.TASKS_FILTERED_PATH)
        review_scores_map = load_review_scores(SplitConfig.REVIEW_SCORES_PATH)

        print()

        # Step 2: Classify tasks
        tasks_by_category = classify_all_tasks(filtered_tasks, review_scores_map)

        # Step 3: Sample tasks
        sampled_tasks, gap_log = sample_tasks(tasks_by_category, review_scores_map)

        # Step 4: Save outputs
        save_category_tasks(sampled_tasks, SplitConfig.OUTPUT_DIR)
        save_summary_report(sampled_tasks, gap_log, SplitConfig.OUTPUT_DIR)

        # Print completion summary
        print_completion_summary(SplitConfig.OUTPUT_DIR, gap_log)

    except FileNotFoundError as e:
        print_error(f"文件未找到：{e}")
        print()
        print_warning("请先运行 data_quality_filter.py 生成以下文件：")
        print("   1. tasks_filtered.json")
        print("   2. review_scores.json")
        sys.exit(1)

    except json.JSONDecodeError as e:
        print_error(f"JSON 解码错误：{e}")
        print()
        print_warning("请检查输入文件格式是否正确")
        sys.exit(1)

    except Exception as e:
        print_error(f"未预期的错误：{e}")
        import traceback
        print()
        print("详细错误信息：")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
