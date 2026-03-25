#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate English version of tasks_realistic_v3.json
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List

# Translation dictionary
TRANSLATIONS = {
    # Departments
    "内科": "Internal Medicine",
    "外科": "Surgery",
    "妇产科": "Obstetrics and Gynecology",
    "儿科": "Pediatrics",
    "肿瘤科": "Oncology",
    "男科": "Andrology",

    # Medical conditions
    "高血压": "hypertension",
    "糖尿病": "diabetes",
    "心脏病": "heart disease",
    "感冒": "cold",
    "发烧": "fever",
    "咳嗽": "cough",
    "头痛": "headache",
    "头晕": "dizziness",
    "胃痛": "stomach pain",
    "腹痛": "abdominal pain",
    "失眠": "insomnia",
    "乏力": "fatigue",

    # Medications
    "党参": "Codonopsis",
    "降压药": "antihypertensive drugs",
    "药": "medication",

    # Common words
    "医生": "doctor",
    "患者": "patient",
    "症状": "symptoms",
    "能吃": "take",
    "不能吃": "cannot take",
    "建议": "recommend",
    "注意": "note",
    "治疗": "treatment",
    "检查": "examination",
    "诊断": "diagnosis",
    "过敏": "allergy",
    "副作用": "side effects",

    # Scenarios
    "信息查询": "Information Query",
    "症状咨询": "Symptom Consultation",
    "诊断建议": "Diagnosis Advice",
    "治疗咨询": "Treatment Consultation",
    "用药咨询": "Medication Consultation",
    "复查咨询": "Follow-up Consultation",

    # Questions
    "这个问题持续多久了？": "How long has this problem been going on?",
    "严重程度如何？有没有加重或缓解？": "How severe is it? Has it gotten worse or better?",
    "目前吃什么药？": "What medications are you currently taking?",
    "有没有药物过敏史？": "Do you have any history of drug allergies?",

    # Descriptions
    "判断病情发展阶段": "Determine the stage of disease development",
    "评估病情严重性": "Assess disease severity",
    "避免药物相互作用": "Avoid drug interactions",
    "避免过敏反应": "Avoid allergic reactions",
    "识别危险信号并给出紧急建议": "Identify danger signs and provide emergency advice",
    "在没有充分检查依据时，不能给出确定性诊断": "Cannot provide definitive diagnosis without sufficient examination",
    "使用'可能'、'疑似'、'需要排除'等词汇": "Use terms like 'possibly', 'suspected', 'needs to be ruled out'",
    "如果出现胸痛、呼吸困难、严重头痛等症状，立即建议就医": "If chest pain, difficulty breathing, severe headache or other symptoms occur, seek immediate medical attention",
    "Response should address patient's concern": "Response should address patient's concern",
    "Real Chinese medical dialogue from": "Real medical dialogue from",
    "Source: Chinese MedDialog Dataset.": "Source: Chinese MedDialog Dataset.",
    "Medical consultation -": "Medical consultation -",
    "You are a patient seeking medical advice.": "You are a patient seeking medical advice.",
    "Your concern:": "Your concern:",
    "Your question to the doctor:": "Your question to the doctor:",
    "Please engage in a natural conversation with the doctor about your health concern.": "Please engage in a natural conversation with the doctor about your health concern.",

    # Common phrases
    "我有": "I have",
    "您好": "Hello",
    "你好": "Hello",
    "这两天": "recently",
    "给我拿了些": "brought me some",
    "泡水喝": "for tea",
    "记不清名字了": "cannot remember the name",
}

# Specific phrase replacements
PHRASE_REPLACEMENTS = [
    (r"我有高血压，?(.+)", r"I have hypertension. \1"),
    (r"医生开了什么降压药，但我记不清名字了。?(.+)", r"The doctor prescribed antihypertensive drugs, but I cannot remember the name. \1"),
    (r"高血压患者能吃党参吗？", r"Can hypertension patients take Codonopsis?"),
    (r"医生，?(.+)", r"Doctor, \1"),
]


def translate_chinese_text(text: str) -> str:
    """Translate Chinese text to English."""
    if not isinstance(text, str):
        return text

    # Check if contains Chinese
    if not re.search(r'[\u4e00-\u9fff]', text):
        return text

    result = text

    # Apply phrase replacements first
    for pattern, replacement in PHRASE_REPLACEMENTS:
        result = re.sub(pattern, replacement, result)

    # Apply word replacements (longest first)
    for cn, en in sorted(TRANSLATIONS.items(), key=lambda x: -len(x[0])):
        result = result.replace(cn, en)

    # Clean up
    result = result.replace("  ", " ").strip()

    return result


def translate_value(value: Any) -> Any:
    """Recursively translate a value."""
    if isinstance(value, str):
        return translate_chinese_text(value)
    elif isinstance(value, dict):
        return {k: translate_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [translate_value(item) for item in value]
    else:
        return value


def translate_task(task: Dict[str, Any], index: int) -> Dict[str, Any]:
    """Translate a single task."""
    translated = {}

    for key, value in task.items():
        if key == "metadata" and isinstance(value, dict):
            # Special handling for metadata
            metadata = translate_value(value)
            # Add English department
            if "department_cn" in metadata:
                dept_cn = metadata["department_cn"]
                if dept_cn in TRANSLATIONS:
                    metadata["department_en"] = TRANSLATIONS[dept_cn]
            translated[key] = metadata
        else:
            translated[key] = translate_value(value)

    return translated


def main():
    """Main function."""
    input_file = Path("data/tau2/domains/clinical/chinese_internal_medicine/tasks_realistic_v3.json")
    output_file = Path("data/tau2/domains/clinical/chinese_internal_medicine/tasks_realistic_v3_en.json")

    print("=" * 70)
    print("Translate tasks_realistic_v3.json to English")
    print("=" * 70)
    print()

    # Load tasks
    print(f"Loading: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        tasks = json.load(f)

    print(f"Tasks to translate: {len(tasks)}")
    print()

    # Translate
    print("Translating...")
    translated_tasks = []
    for i, task in enumerate(tasks):
        if (i + 1) % 100 == 0:
            print(f"  {i + 1}/{len(tasks)}")
        translated_tasks.append(translate_task(task, i))

    print(f"  {len(tasks)}/{len(tasks)}")
    print()

    # Save
    print(f"Saving: {output_file}")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(translated_tasks, f, ensure_ascii=False, indent=2)

    file_size_mb = output_file.stat().st_size / (1024 * 1024)

    # Check quality
    with open(output_file, 'r', encoding='utf-8') as f:
        content = f.read()
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', content)

    print()
    print("=" * 70)
    print("Translation Complete!")
    print("=" * 70)
    print(f"Tasks: {len(translated_tasks)}")
    print(f"File size: {file_size_mb:.2f} MB")
    print(f"Remaining Chinese characters: {len(chinese_chars)}")

    if len(chinese_chars) > 0:
        unique_chinese = set(chinese_chars)
        print(f"Unique Chinese characters: {len(unique_chinese)}")
        print(f"Sample: {''.join(list(unique_chinese)[:20])}")

    print()
    print("Output file:", output_file)
    print("Original file:", input_file)

    return 0


if __name__ == "__main__":
    exit(main())
