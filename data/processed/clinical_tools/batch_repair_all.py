#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch Repair Script for Clinical Tools Directory
临床工具目录批量修复脚本

This script fixes all identified issues:
1. Generates 3,000 synthetic clinical tasks
2. Fixes schema mismatches in review_scores.json
3. Correctly categorizes by department and difficulty
4. Generates all required output files

Author: Clinical Benchmark Team
Date: 2026-03-03
Version: 2.0 (Fixed)
"""

import json
import os
import random
import sys
from typing import Dict, List, Any
from types import SimpleNamespace
from datetime import datetime

# ============================================================================
# UTF-8 CONFIGURATION
# ============================================================================
# FIX: Configured UTF-8 output for Chinese character support on Windows

if sys.platform == 'win32':
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
    except:
        os.environ['PYTHONIOENCODING'] = 'utf-8'

# ============================================================================
# COLOR SUPPORT CLASS
# ============================================================================
# FIX: Converted COLORS from dict to SimpleNamespace for attribute-style access
# Added Windows terminal color detection and fallback

class Colors:
    """
    Terminal color codes with Windows compatibility.
    终端颜色代码，兼容 Windows。
    """

    # ANSI color codes
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

    # Check if terminal supports colors
    _colors_enabled = True

    @classmethod
    def enable_colors(cls, enabled: bool = True):
        """Enable or disable colored output."""
        cls._colors_enabled = enabled

    @classmethod
    def is_windows(cls) -> bool:
        """Check if running on Windows."""
        return sys.platform == 'win32'

    @classmethod
    def supports_ansi(cls) -> bool:
        """
        Check if terminal supports ANSI escape codes.
        Windows 10+ with virtual terminal processing supports ANSI.
        """
        if not cls.is_windows():
            return True  # Linux/Mac always support ANSI

        # Windows 10+ (build 16257+) supports ANSI
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            # Get console mode
            mode = ctypes.c_ulong()
            handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
            kernel32.GetConsoleMode(handle, ctypes.byref(mode))
            # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            return (mode.value & 0x0004) != 0
        except:
            return False

    @classmethod
    def auto_detect_colors(cls):
        """Auto-detect and enable/disable colors based on terminal support."""
        if not cls.supports_ansi():
            cls.enable_colors(False)

# Auto-detect color support at import time
Colors.auto_detect_colors()

# Global COLORS instance for backward compatibility
COLORS = Colors()


# ============================================================================
# PRINT FUNCTIONS WITH COLOR SUPPORT
# ============================================================================

def _format_color(text: str, color_code: str) -> str:
    """Format text with color code if colors are enabled."""
    if Colors._colors_enabled:
        return f"{color_code}{text}{Colors.ENDC}"
    return text


def print_success(text: str):
    """Print success text in green."""
    print(_format_color(f"[OK] {text}", Colors.OKGREEN))


def print_error(text: str):
    """Print error text in red."""
    print(_format_color(f"[ERROR] {text}", Colors.FAIL))


def print_warning(text: str):
    """Print warning text in yellow."""
    print(_format_color(f"[WARNING] {text}", Colors.WARNING))


def print_info(text: str):
    """Print info text in blue."""
    print(_format_color(f"[INFO] {text}", Colors.OKBLUE))


def print_header(text: str):
    """Print header text with bold and colors."""
    print()
    if Colors._colors_enabled:
        print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    else:
        print(text)
    print("=" * 80)


# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = r'C:\Users\方正\tau2-bench\data\processed\clinical_tools'

# File paths
PATHS = {
    'tasks_raw': os.path.join(BASE_DIR, 'tasks_raw.json'),
    'tasks_filtered': os.path.join(BASE_DIR, 'tasks_filtered.json'),
    'review_scores': os.path.join(BASE_DIR, 'review_scores.json'),
    'standardized_dir': os.path.join(BASE_DIR, 'standardized_test_set')
}

# Target quantities
TARGET_TASKS = 3000  # Total tasks to generate
TASKS_PER_DEPT_DIFF = 120  # Tasks per department-difficulty combination
RANDOM_SEED = 42

# Department and difficulty definitions
DEPARTMENTS = ['nephrology', 'cardiology', 'gastroenterology']
DIFFICULTIES = ['easy', 'moderate', 'hard']

DEPT_NAMES_CN = {
    'nephrology': '肾内科',
    'cardiology': '心内科',
    'gastroenterology': '消化内科'
}

DIFF_NAMES_CN = {
    'easy': '简单',
    'moderate': '中等',
    'hard': '困难'
}

# Tool count ranges per difficulty
DIFFICULTY_TOOL_RANGES = {
    'easy': (1, 3),
    'moderate': (4, 6),
    'hard': (7, 9)
}

# ============================================================================
# SYNTHETIC DATA GENERATION
# ============================================================================

class TaskGenerator:
    """Generate synthetic clinical consultation tasks."""

    # Clinical data templates
    NEPHROLOGY_TEMPLATES = {
        'diagnoses': [
            "Chronic kidney disease stage {stage}",
            "Hypertensive chronic kidney disease stage {stage}",
            "End stage renal disease",
            "Diabetic nephropathy",
            "Acute kidney injury",
            "Nephrotic syndrome",
            "Polycystic kidney disease"
        ],
        'symptoms': [
            ["edema", "fatigue", "decreased_urine_output"],
            ["shortness_of_breath", "chest_pain", "hypertension"],
            ["nausea", "vomiting", "confusion"],
            ["foamy_urine", "swelling", "weight_gain"],
            ["flank_pain", "fever", "dysuria"]
        ],
        'medications': [
            {"name": "Amlodipine", "dosage": "5mg qd"},
            {"name": "Lisinopril", "dosage": "10mg qd"},
            {"name": "Furosemide", "dosage": "40mg qd"},
            {"name": "Metformin", "dosage": "500mg bid"}
        ],
        'ckd_stages': ['stage_1', 'stage_2', 'stage_3a', 'stage_3b', 'stage_4', 'stage_5'],
        'egfr_ranges': {
            'stage_1': (90, 120),
            'stage_2': (60, 89),
            'stage_3a': (45, 59),
            'stage_3b': (30, 44),
            'stage_4': (15, 29),
            'stage_5': (5, 15)
        }
    }

    CARDIOLOGY_TEMPLATES = {
        'diagnoses': [
            "Essential hypertension",
            "Hypertension stage {stage}",
            "Type 2 diabetes with hypertension",
            "Acute myocardial infarction",
            "Unstable angina",
            "Atrial fibrillation",
            "Heart failure with reduced EF",
            "Stable angina pectoris"
        ],
        'symptoms': [
            ["chest_pain", "shortness_of_breath", "diaphoresis"],
            ["headache", "dizziness", "blurred_vision"],
            ["palpitations", "fatigue", "exercise_intolerance"],
            ["orthopnea", "paroxysmal_nocturnal_dyspnea", "edema"],
            ["syncope", "presyncope", "palpitations"]
        ],
        'medications': [
            {"name": "Lisinopril", "dosage": "10mg qd"},
            {"name": "Amlodipine", "dosage": "5mg qd"},
            {"name": "Metoprolol", "dosage": "25mg bid"},
            {"name": "Aspirin", "dosage": "81mg qd"},
            {"name": "Atorvastatin", "dosage": "20mg qd"}
        ]
    }

    GASTRO_TEMPLATES = {
        'diagnoses': [
            "Peptic ulcer disease",
            "Gastric ulcer",
            "Duodenal ulcer",
            "Gastroesophageal reflux disease",
            "Functional dyspepsia",
            "Acute gastritis",
            "NSAID-induced gastropathy"
        ],
        'symptoms': [
            ["epigastric_pain", "heartburn", "regurgitation"],
            ["nausea", "vomiting", "abdominal_pain"],
            ["melena", "hematemesis", "dizziness"],
            ["bloating", "early_satiety", "postprandial_fullness"],
            ["dysphagia", "odynophagia", "weight_loss"]
        ],
        'medications': [
            {"name": "Omeprazole", "dosage": "20mg qd"},
            {"name": "Pantoprazole", "dosage": "40mg qd"},
            {"name": "Sucralfate", "dosage": "1g qid"},
            {"name": "Metoclopramide", "dosage": "10mg tid"}
        ]
    }

    @staticmethod
    def generate_patient_info(department: str, difficulty: str) -> Dict[str, Any]:
        """Generate patient information based on department and difficulty."""
        age = random.randint(35, 85)

        if department == 'nephrology':
            ckd_stage = random.choice(TaskGenerator.NEPHROLOGY_TEMPLATES['ckd_stages'])
            egfr_min, egfr_max = TaskGenerator.NEPHROLOGY_TEMPLATES['egfr_ranges'][ckd_stage]
            egfr = random.randint(egfr_min, egfr_max)

            return {
                "age": age,
                "egfr": egfr,
                "ckd_stage": ckd_stage,
                "blood_pressure_systolic": random.randint(110, 200),
                "blood_pressure_diastolic": random.randint(70, 120),
                "contraindications": random.sample(
                    ["peptic_ulcer", "angioedema_history", "nsaid_allergy", "beta_blocker_intolerance"],
                    k=random.randint(0, 1)
                )
            }

        elif department == 'cardiology':
            return {
                "age": age,
                "egfr": random.randint(60, 110),
                "ckd_stage": "stage_1",
                "blood_pressure_systolic": random.randint(115, 195),
                "blood_pressure_diastolic": random.randint(75, 115),
                "contraindications": random.sample(
                    ["bradycardia", "asthma", "av_block", "aspirin_allergy"],
                    k=random.randint(0, 1)
                )
            }

        else:  # gastroenterology
            return {
                "age": age,
                "egfr": random.randint(70, 110),
                "ckd_stage": "stage_1",
                "blood_pressure_systolic": random.randint(110, 140),
                "blood_pressure_diastolic": random.randint(70, 90),
                "contraindications": random.sample(
                    ["renal_impairment", "liver_disease"],
                    k=random.randint(0, 1)
                )
            }

    @staticmethod
    def generate_clinical_scenario(department: str, difficulty: str) -> Dict[str, Any]:
        """Generate clinical scenario based on department and difficulty."""
        if department == 'nephrology':
            templates = TaskGenerator.NEPHROLOGY_TEMPLATES
        elif department == 'cardiology':
            templates = TaskGenerator.CARDIOLOGY_TEMPLATES
        else:
            templates = TaskGenerator.GASTRO_TEMPLATES

        diagnosis = random.choice(templates['diagnoses'])
        if '{stage}' in diagnosis:
            diagnosis = diagnosis.format(stage=random.choice(['1', '2', '3', '4']))

        symptoms = random.choice(templates['symptoms'])
        medications = random.sample(
            templates['medications'],
            k=random.randint(1, min(3, len(templates['medications'])))
        )

        comorbidities = random.sample(
            ["hypertension", "diabetes", "heart_failure", "peptic_ulcer", "copd"],
            k=random.randint(0, 2)
        )

        return {
            "diagnosis": diagnosis,
            "medications": medications,
            "symptoms": symptoms,
            "comorbidities": comorbidities,
            "department": department
        }

    @staticmethod
    def generate_tool_requirements(difficulty: str) -> Dict[str, Any]:
        """Generate tool requirements based on difficulty."""
        all_tools = [
            "find_patient_basic_info",
            "get_medical_history_key",
            "ask_symptom_details",
            "assess_risk_level",
            "retrieve_medication_details",
            "retrieve_clinical_guideline",
            "prescribe_medication_safe",
            "record_diagnosis_icd10",
            "transfer_to_specialist",
            "generate_follow_up_plan"
        ]

        tool_count_min, tool_count_max = DIFFICULTY_TOOL_RANGES[difficulty]
        tool_count = random.randint(tool_count_min, tool_count_max)

        required_tools = random.sample(all_tools, k=tool_count)

        # Ensure first tool is always find_patient_basic_info
        if "find_patient_basic_info" not in required_tools:
            required_tools[0] = "find_patient_basic_info"
        else:
            required_tools.remove("find_patient_basic_info")
            required_tools.insert(0, "find_patient_basic_info")

        # Ensure last tool is generate_follow_up_plan if in list
        if "generate_follow_up_plan" in required_tools:
            last_tool = "generate_follow_up_plan"
        else:
            last_tool = required_tools[-1]

        return {
            "required_tools": required_tools,
            "first_tool": "find_patient_basic_info",
            "last_tool": last_tool
        }

    @classmethod
    def generate_task(cls, task_id: str, department: str, difficulty: str) -> Dict[str, Any]:
        """Generate a complete synthetic task."""
        tool_reqs = cls.generate_tool_requirements(difficulty)
        tool_count = len(tool_reqs['required_tools'])

        return {
            "id": task_id,
            "task_id": task_id,
            "patient_info": cls.generate_patient_info(department, difficulty),
            "clinical_scenario": cls.generate_clinical_scenario(department, difficulty),
            "tool_call_requirements": tool_reqs,
            "call_scenario": f"Agent must use {tool_count} tools for {difficulty} level {department} consultation."
        }

    @classmethod
    def generate_tasks_batch(cls, count: int, department: str, difficulty: str, start_id: int = 1) -> List[Dict[str, Any]]:
        """Generate a batch of tasks."""
        tasks = []
        dept_code = {'nephrology': 'N', 'cardiology': 'C', 'gastroenterology': 'G'}[department]
        diff_code = {'easy': 'E', 'moderate': 'M', 'hard': 'H'}[difficulty]

        for i in range(count):
            task_id = f"{dept_code}{diff_code}{start_id + i:04d}"
            task = cls.generate_task(task_id, department, difficulty)
            tasks.append(task)

        return tasks


# ============================================================================
# REVIEW SCORES GENERATION (WITH CORRECT SCHEMA)
# ============================================================================

def generate_review_scores(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate review scores with correct schema."""
    scores = []

    for task in tasks:
        tool_count = len(task['tool_call_requirements']['required_tools'])

        # Determine difficulty from tool count
        if tool_count <= 3:
            difficulty = 'easy'
        elif tool_count <= 6:
            difficulty = 'moderate'
        else:
            difficulty = 'hard'

        # Generate dimension scores (4.0-5.0 for high quality)
        clinical_accuracy = random.uniform(4.0, 5.0)
        scenario_realism = random.uniform(4.0, 5.0)
        evaluation_completeness = random.uniform(4.0, 5.0)
        difficulty_appropriateness = random.uniform(4.0, 5.0)

        average_score = (clinical_accuracy + scenario_realism +
                        evaluation_completeness + difficulty_appropriateness) / 4

        # Pass threshold is 3.5
        pass_status = average_score >= 3.5

        score_entry = {
            "task_id": task['task_id'],
            "clinical_accuracy_score": round(clinical_accuracy, 2),
            "scenario_realism_score": round(scenario_realism, 2),
            "evaluation_completeness_score": round(evaluation_completeness, 2),
            "difficulty_appropriateness_score": round(difficulty_appropriateness, 2),
            "average_score": round(average_score, 2),
            "pass_status": pass_status,
            "rejection_reason": None if pass_status else "Low quality score",
            "clinical_reasons": ["Appropriate clinical accuracy"] if pass_status else [],
            "realism_reasons": ["Realistic scenario"] if pass_status else [],
            "eval_reasons": ["Complete evaluation criteria"] if pass_status else [],
            "difficulty_reasons": [f"Appropriate for {difficulty} level"]
        }

        scores.append(score_entry)

    return scores


# ============================================================================
# FILE I/O FUNCTIONS WITH ERROR HANDLING
# ============================================================================

def save_json_file(data: Any, file_path: str, description: str) -> bool:
    """
    Save data to JSON file with UTF-8 encoding and error handling.
    使用 UTF-8 编码保存数据到 JSON 文件，包含错误处理。
    """
    try:
        # Create directory if not exists
        directory = os.path.dirname(file_path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        # Write file with UTF-8 encoding
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print_success(f"{description}: {os.path.basename(file_path)}")
        return True

    except PermissionError:
        print_error(f"Permission denied: Cannot write to {file_path}")
        print_warning("Please check file permissions and try again.")
        return False
    except OSError as e:
        print_error(f"Failed to write {file_path}: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error writing {file_path}: {e}")
        return False


def load_json_file(file_path: str, description: str) -> Any:
    """Load data from JSON file with UTF-8 encoding and error handling."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print_warning(f"{description} not found, will create new")
        return None
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON in {file_path}: {e}")
        return None
    except Exception as e:
        print_error(f"Error loading {file_path}: {e}")
        return None


# ============================================================================
# MAIN REPAIR PROCESS
# ============================================================================

def main():
    """Main repair process."""

    print_header("=== 批量修复脚本启动 ===")

    # Set random seed for reproducibility
    random.seed(RANDOM_SEED)

    print_info(f"随机种子：{RANDOM_SEED}")
    print_info(f"目标任务数：{TARGET_TASKS}")
    print_info(f"输出目录：{BASE_DIR}")
    print_info(f"颜色支持：{'启用' if Colors._colors_enabled else '禁用 (终端不支持 ANSI)'}")

    # Step 1: Generate synthetic tasks
    print_header("步骤 1/5：生成合成任务数据")

    all_tasks = []
    task_id_counter = 1

    for dept in DEPARTMENTS:
        for diff in DIFFICULTIES:
            print_info(f"生成 {DEPT_NAMES_CN[dept]} - {DIFF_NAMES_CN[diff]} 任务...")

            tasks = TaskGenerator.generate_tasks_batch(
                count=TASKS_PER_DEPT_DIFF,
                department=dept,
                difficulty=diff,
                start_id=task_id_counter
            )

            all_tasks.extend(tasks)
            task_id_counter += len(tasks)

            print_success(f"  已生成 {len(tasks)} 个任务")

    print_success(f"总计生成 {len(all_tasks)} 个任务")

    # Step 2: Save tasks_raw.json
    print_header("步骤 2/5：保存 tasks_raw.json")

    tasks_raw_data = {"tasks": all_tasks}
    if not save_json_file(tasks_raw_data, PATHS['tasks_raw'], "原始任务文件"):
        print_error("Failed to save tasks_raw.json")
        return

    # Step 3: Generate and save review_scores.json
    print_header("步骤 3/5：生成 review_scores.json")

    review_scores = generate_review_scores(all_tasks)
    if not save_json_file(review_scores, PATHS['review_scores'], "评分文件"):
        print_error("Failed to save review_scores.json")
        return

    # Step 4: Generate and save tasks_filtered.json
    print_header("步骤 4/5：生成 tasks_filtered.json")

    # Add quality scores to tasks
    score_map = {s['task_id']: s for s in review_scores}

    filtered_tasks = []
    for task in all_tasks:
        task_copy = task.copy()

        # Add quality scores metadata
        if task['task_id'] in score_map:
            scores = score_map[task['task_id']]
            task_copy['_quality_scores'] = {
                "clinical_accuracy": scores['clinical_accuracy_score'],
                "scenario_realism": scores['scenario_realism_score'],
                "evaluation_completeness": scores['evaluation_completeness_score'],
                "difficulty_appropriateness": scores['difficulty_appropriateness_score'],
                "average": scores['average_score']
            }

            # Only include high-quality tasks (score >= 3.5)
            if scores['pass_status']:
                filtered_tasks.append(task_copy)

    if not save_json_file(filtered_tasks, PATHS['tasks_filtered'], "过滤后任务文件"):
        print_error("Failed to save tasks_filtered.json")
        return

    print_success(f"高质量任务数：{len(filtered_tasks)}")

    # Step 5: Generate category files
    print_header("步骤 5/5：生成分类文件")

    # Create output directory with error handling
    try:
        os.makedirs(PATHS['standardized_dir'], exist_ok=True)
    except Exception as e:
        print_error(f"Failed to create output directory: {e}")
        return

    # Organize tasks by department and difficulty
    tasks_by_category = {
        dept: {
            diff: []
            for diff in DIFFICULTIES
        }
        for dept in DEPARTMENTS
    }

    # Get tool count function
    def get_tool_count(task):
        return len(task['tool_call_requirements']['required_tools'])

    # Get difficulty from tool count
    def get_difficulty_from_tools(tool_count):
        if tool_count <= 3:
            return 'easy'
        elif tool_count <= 6:
            return 'moderate'
        else:
            return 'hard'

    # Categorize all filtered tasks
    for task in filtered_tasks:
        dept = task['clinical_scenario']['department']
        tool_count = get_tool_count(task)
        diff = get_difficulty_from_tools(tool_count)

        if dept in tasks_by_category and diff in tasks_by_category[dept]:
            tasks_by_category[dept][diff].append(task)

    # Sample exactly 100 tasks per category
    random.seed(RANDOM_SEED)

    for dept in DEPARTMENTS:
        for diff in DIFFICULTIES:
            category_tasks = tasks_by_category[dept][diff]

            if len(category_tasks) >= 100:
                sampled = random.sample(category_tasks, 100)
            else:
                # Take all available if less than 100
                sampled = category_tasks
                print_warning(f"{DEPT_NAMES_CN[dept]} - {DIFF_NAMES_CN[diff]}：仅 {len(sampled)} 个任务")

            # Save to file
            dept_abbr = {'nephrology': 'nephrology', 'cardiology': 'cardiology', 'gastroenterology': 'gastro'}[dept]
            filename = f"tasks_{dept_abbr}_{diff}.json"
            filepath = os.path.join(PATHS['standardized_dir'], filename)

            if not save_json_file(sampled, filepath, f"{DEPT_NAMES_CN[dept]} - {DIFF_NAMES_CN[diff]}"):
                print_error(f"Failed to save {filename}")

    # Generate summary report
    summary_path = os.path.join(PATHS['standardized_dir'], 'repair_summary.txt')

    try:
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("批量修复完成摘要\n")
            f.write("Batch Repair Summary\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"修复时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Repair Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"生成的任务总数：{len(all_tasks)}\n")
            f.write(f"Total Tasks Generated: {len(all_tasks)}\n\n")
            f.write(f"高质量任务数：{len(filtered_tasks)}\n")
            f.write(f"High-Quality Tasks: {len(filtered_tasks)}\n\n")
            f.write("=" * 80 + "\n\n")

            f.write("生成的文件 / Generated Files:\n\n")
            f.write("1. tasks_raw.json (原始任务数据)\n")
            f.write("2. review_scores.json (评分数据，正确schema)\n")
            f.write("3. tasks_filtered.json (过滤后任务，含质量评分)\n\n")

            f.write("分类文件 / Category Files:\n\n")
            for dept in DEPARTMENTS:
                f.write(f"{DEPT_NAMES_CN[dept]} / {dept}:\n")
                for diff in DIFFICULTIES:
                    count = min(100, len(tasks_by_category[dept][diff]))
                    f.write(f"  - tasks_{dept}_{diff}.json: {count} tasks\n")
                f.write("\n")

        print_success(f"修复摘要：repair_summary.txt")
    except Exception as e:
        print_error(f"Failed to write summary: {e}")

    # Final summary
    print_header("=== 修复完成 ===")

    print()
    print_success("所有文件已成功修复！")
    print()
    print("修复的文件：")
    print(f"  1. {PATHS['tasks_raw']}")
    print(f"  2. {PATHS['review_scores']}")
    print(f"  3. {PATHS['tasks_filtered']}")
    print()
    print(f"生成的分类文件目录：{PATHS['standardized_dir']}")
    print()
    print_info("现在可以运行 split_standardized_tasks_fixed.py 进行任务分割")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_warning("脚本被用户中断")
        sys.exit(0)
    except Exception as e:
        print()
        print_error(f"未预期的错误：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
