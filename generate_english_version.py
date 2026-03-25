#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate English version of tasks_realistic_v3.json
"""

import json
import re
from pathlib import Path
from typing import Dict, Any

# Medical terminology translation dictionary
MEDICAL_TERMS = {
    # Departments
    "内科": "Internal Medicine",
    "外科": "Surgery",
    "妇产科": "Obstetrics & Gynecology",
    "儿科": "Pediatrics",
    "肿瘤科": "Oncology",
    "男科": "Andrology",

    # Scenario types
    "信息查询": "Information Query",
    "症状咨询": "Symptom Consultation",
    "诊断建议": "Diagnosis Advice",
    "治疗咨询": "Treatment Consultation",
    "用药咨询": "Medication Consultation",
    "复查咨询": "Follow-up Consultation",

    # Common medical terms
    "高血压": "hypertension",
    "糖尿病": "diabetes",
    "心脏病": "heart disease",
    "感冒": "common cold",
    "发烧": "fever",
    "咳嗽": "cough",
    "头痛": "headache",
    "胃痛": "stomach pain",
    "失眠": "insomnia",
}

# Priority translations
PRIORITY_MAP = {
    "high": "high",
    "medium": "medium",
    "low": "low",
}

# Severity translations
SEVERITY_MAP = {
    "critical": "critical",
    "high": "high",
    "medium": "medium",
    "low": "low",
}


def translate_chinese_to_en(text: str, context: str = "") -> str:
    """
    Translate Chinese text to English with context awareness.

    This is a simplified translation. For production, use a proper translation API.
    """
    if not text or not isinstance(text, str):
        return text

    # Check if text contains Chinese characters
    if not re.search(r'[\u4e00-\u9fff]', text):
        return text

    # Apply medical term translations
    result = text
    for cn, en in MEDICAL_TERMS.items():
        result = result.replace(cn, en)

    # Common phrases
    phrases = {
        "高血压患者能吃党参吗？": "Can hypertension patients take Codonopsis pilosula?",
        "我有高血压": "I have hypertension",
        "这两天": "recently",
        "女婿来的时候给我拿了些": "my son-in-law brought me some",
        "您好": "Hello",
        "医生": "doctor",
        "这个问题持续多久了？": "How long has this problem been going on?",
        "严重程度如何？有没有加重或缓解？": "How severe is it? Has it gotten worse or better?",
        "目前吃什么药？": "What medications are you currently taking?",
        "有没有药物过敏史？": "Do you have any history of drug allergies?",
        "在没有充分检查依据时，不能给出确定性诊断": "Cannot give definitive diagnosis without sufficient examination evidence",
        "使用'可能'、'疑似'、'需要排除'等词汇": "Use terms like 'possibly', 'suspected', 'needs to be ruled out'",
        "如果出现胸痛、呼吸困难、严重头痛等症状，立即建议就医": "If chest pain, difficulty breathing, severe headache or other symptoms occur, immediately seek medical attention",
        "识别危险信号并给出紧急建议": "Identify danger signs and provide emergency advice",
        "判断病情发展阶段": "Determine the stage of disease development",
        "评估病情严重性": "Assess disease severity",
        "避免药物相互作用": "Avoid drug interactions",
        "避免过敏反应": "Avoid allergic reactions",
        "Real Chinese medical dialogue from": "Real medical dialogue from",
        "Source: Chinese MedDialog Dataset.": "Source: Chinese MedDialog Dataset.",
        "Medical consultation -": "Medical consultation -",
        "You are a patient seeking medical advice.": "You are a patient seeking medical advice.",
        "Your concern:": "Your concern:",
        "Your question to the doctor:": "Your question to the doctor:",
        "Please engage in a natural conversation with the doctor about your health concern.": "Please engage in a natural conversation with the doctor about your health concern.",
        "Response should address patient's concern": "Response should address patient's concern",
    }

    for cn, en in phrases.items():
        result = result.replace(cn, en)

    return result


def translate_task(task: Dict[str, Any], task_idx: int) -> Dict[str, Any]:
    """Translate a single task from Chinese to English."""
    translated = task.copy()

    # Translate description
    if "description" in translated:
        desc = translated["description"].copy()
        if "purpose" in desc:
            desc["purpose"] = translate_chinese_to_en(desc["purpose"], "purpose")
        if "notes" in desc:
            desc["notes"] = translate_chinese_to_en(desc["notes"], "notes")
        translated["description"] = desc

    # Translate user_scenario
    if "user_scenario" in translated:
        user_scenario = translated["user_scenario"].copy()
        if "persona" in user_scenario:
            user_scenario["persona"] = translate_chinese_to_en(user_scenario["persona"], "persona")

        if "instructions" in user_scenario:
            instructions = user_scenario["instructions"].copy()
            instructions["domain"] = "internal_medicine"  # Keep domain in English
            instructions["reason_for_call"] = translate_chinese_to_en(
                instructions.get("reason_for_call", ""), "reason_for_call"
            )
            instructions["known_info"] = translate_chinese_to_en(
                instructions.get("known_info", ""), "known_info"
            )
            instructions["task_instructions"] = translate_chinese_to_en(
                instructions.get("task_instructions", ""), "task_instructions"
            )
            if "original_known_info" in instructions:
                instructions["original_known_info"] = translate_chinese_to_en(
                    instructions["original_known_info"], "original_known_info"
                )
            user_scenario["instructions"] = instructions

        translated["user_scenario"] = user_scenario

    # Translate ticket
    if "ticket" in translated:
        translated["ticket"] = translate_chinese_to_en(translated["ticket"], "ticket")

    # Translate evaluation_criteria
    if "evaluation_criteria" in translated:
        eval_criteria = translated["evaluation_criteria"].copy()
        if "actions" in eval_criteria:
            actions = []
            for action in eval_criteria["actions"]:
                translated_action = action.copy()
                if "arguments" in translated_action and "should_address" in translated_action["arguments"]:
                    translated_action["arguments"]["should_address"] = translate_chinese_to_en(
                        translated_action["arguments"]["should_address"], "should_address"
                    )
                actions.append(translated_action)
            eval_criteria["actions"] = actions

        if "communication_checks" in eval_criteria:
            checks = []
            for check in eval_criteria["communication_checks"]:
                translated_check = check.copy()
                if "criteria" in translated_check:
                    translated_check["criteria"] = translate_chinese_to_en(
                        translated_check["criteria"], "criteria"
                    )
                checks.append(translated_check)
            eval_criteria["communication_checks"] = checks

        translated["evaluation_criteria"] = eval_criteria

    # Translate metadata
    if "metadata" in translated:
        metadata = translated["metadata"].copy()
        metadata["source"] = "Chinese MedDialog"  # Keep source
        metadata["department_cn"] = metadata.get("department_cn", "内科")  # Keep original for reference
        metadata["department_en"] = "Internal Medicine"  # Add English
        metadata["original_title"] = translate_chinese_to_en(
            metadata.get("original_title", ""), "original_title"
        )

        # Translate scenario_name
        if "scenario_name" in metadata:
            metadata["scenario_name"] = translate_chinese_to_en(
                metadata["scenario_name"], "scenario_name"
            )

        # Translate inquiry_requirements
        if "inquiry_requirements" in metadata:
            inquiry_req = metadata["inquiry_requirements"].copy()
            for category in inquiry_req:
                for field, details in inquiry_req[category].items():
                    if isinstance(details, dict):
                        if "question" in details:
                            details["question"] = translate_chinese_to_en(details["question"], "question")
                        if "reason" in details:
                            details["reason"] = translate_chinese_to_en(details["reason"], "reason")

            metadata["inquiry_requirements"] = inquiry_req

        # Translate safety_rules
        if "safety_rules" in metadata:
            safety_rules = []
            for rule in metadata["safety_rules"]:
                translated_rule = rule.copy()
                if "description" in translated_rule:
                    translated_rule["description"] = translate_chinese_to_en(
                        translated_rule["description"], "description"
                    )
                if "action" in translated_rule:
                    translated_rule["action"] = translate_chinese_to_en(
                        translated_rule["action"], "action"
                    )
                safety_rules.append(translated_rule)

            metadata["safety_rules"] = safety_rules

        translated["metadata"] = metadata

    return translated


def generate_english_version(
    input_file: Path,
    output_file: Path,
    max_tasks: int = None
):
    """Generate English version of tasks JSON file."""

    print(f"Reading from: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        tasks = json.load(f)

    total_tasks = len(tasks)
    if max_tasks:
        tasks = tasks[:max_tasks]
        print(f"Processing first {max_tasks} of {total_tasks} tasks")
    else:
        print(f"Processing all {total_tasks} tasks")

    print("\nTranslating tasks to English...")
    translated_tasks = []

    for i, task in enumerate(tasks):
        if (i + 1) % 50 == 0:
            print(f"  Progress: {i + 1}/{len(tasks)}")

        translated_task = translate_task(task, i)
        translated_tasks.append(translated_task)

    print(f"  Completed: {len(translated_tasks)}/{len(tasks)}")

    # Write output
    print(f"\nWriting to: {output_file}")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(translated_tasks, f, ensure_ascii=False, indent=2)

    file_size_mb = output_file.stat().st_size / (1024 * 1024)
    print(f"✅ Success! Generated {len(translated_tasks)} translated tasks")
    print(f"   File size: {file_size_mb:.2f} MB")

    return translated_tasks


def main():
    """Main function."""
    input_file = Path(
        "data/tau2/domains/clinical/chinese_internal_medicine/tasks_realistic_v3.json"
    )
    output_file = Path(
        "data/tau2/domains/clinical/chinese_internal_medicine/tasks_realistic_v3_en.json"
    )

    print("=" * 70)
    print("Generate English Version of tasks_realistic_v3.json")
    print("=" * 70)
    print()

    try:
        generate_english_version(input_file, output_file)

        print()
        print("=" * 70)
        print("Translation Complete!")
        print("=" * 70)
        print()
        print("Input:  ", input_file)
        print("Output: ", output_file)
        print()
        print("✅ Both Chinese and English versions are now available.")

    except FileNotFoundError as e:
        print(f"❌ Error: Input file not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in input file: {e}")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
