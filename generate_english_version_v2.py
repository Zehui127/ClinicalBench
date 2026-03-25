#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate English version of tasks_realistic_v3.json - Improved version
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List

# Comprehensive medical translation dictionary
MEDICAL_DICT = {
    # Departments
    "内科": "Internal Medicine",
    "外科": "Surgery",
    "妇产科": "Obstetrics & Gynecology",
    "儿科": "Pediatrics",
    "肿瘤科": "Oncology",
    "男科": "Andrology",
    "心血管科": "Cardiology",
    "消化科": "Gastroenterology",
    "呼吸科": "Pulmonology",
    "神经科": "Neurology",
    "内分泌科": "Endocrinology",
    "肾内科": "Nephrology",

    # Symptoms & Conditions
    "高血压": "hypertension",
    "糖尿病": "diabetes",
    "心脏病": "heart disease",
    "冠心病": "coronary heart disease",
    "感冒": "common cold",
    "发烧": "fever",
    "咳嗽": "cough",
    "头痛": "headache",
    "头晕": "dizziness",
    "胃痛": "stomach pain",
    "腹痛": "abdominal pain",
    "失眠": "insomnia",
    "便秘": "constipation",
    "腹泻": "diarrhea",
    "恶心": "nausea",
    "呕吐": "vomiting",
    "乏力": "fatigue",
    "胸闷": "chest tightness",
    "气短": "shortness of breath",
    "心悸": "palpitations",
    "背痛": "back pain",
    "关节痛": "joint pain",

    # Medications & Supplements
    "党参": "Codonopsis pilosula",
    "降压药": "antihypertensive medication",
    "药": "medication",
    "中药": "traditional Chinese medicine",
    "西药": "western medicine",

    # Common words & phrases
    "患者": "patient",
    "医生": "doctor",
    "症状": "symptoms",
    "病": "disease/illness",
    "痛": "pain",
    "能吃": "can take",
    "可以吃": "can take",
    "不能吃": "cannot take",
    "可以": "can",
    "不能": "cannot",
    "有没有": "is there",
    "有没有": "do you have",
    "什么": "what",
    "怎么": "how",
    "为什么": "why",
    "多久": "how long",
    "严重": "severe",
    "严重程度": "severity",
    "加重": "worsen",
    "缓解": "relieve/improve",
    "建议": "recommend/suggest",
    "治疗": "treatment",
    "检查": "examination/test",
    "诊断": "diagnosis",
    "吃药": "take medication",
    "服用": "take/consume",
    "过敏": "allergy",
    "副作用": "side effects",
    "注意": "note/attention",
    "需要注意": "need to pay attention",
    "禁忌": "contraindication",
    "禁忌症": "contraindications",

    # Time expressions
    "这两天": "recently/these past few days",
    "这几天": "these past few days",
    "最近": "recently/lately",
    "一直": "always/continuously",
    "有时候": "sometimes",
    "经常": "often/frequently",
    "偶尔": "occasionally",
    "每天": "every day",
    "每次": "each time",

    # People & relationships
    "我": "I",
    "我的": "my",
    "您": "you (polite)",
    "你好": "hello",
    "您好": "hello (polite)",
    "女婿": "son-in-law",
    "家人": "family",
    "孩子": "child",

    # Questions
    "吗": "? (question particle)",
    "呢": "? (question particle)",
    "吧": "? (suggestion particle)",

    # Scenario types
    "信息查询": "Information Query",
    "症状咨询": "Symptom Consultation",
    "诊断建议": "Diagnosis Advice",
    "治疗咨询": "Treatment Consultation",
    "用药咨询": "Medication Consultation",
    "复查咨询": "Follow-up Consultation",
    "健康咨询": "Health Consultation",
    "预防咨询": "Prevention Consultation",
}

# Specific sentence patterns for better translation
SENTENCE_PATTERNS = [
    # Question patterns
    (r"高血压患者能吃(.+)吗\？", r"Can hypertension patients take \1?"),
    (r"我有高血压，?(.+)", r"I have hypertension. \1"),
    (r"我有(.+)，?(.+)", r"I have \1. \2"),
    (r"(.+)能吃(.+)吗\？", r"Can \1 take \2?"),
    (r"医生，?(.+)", r"Doctor, \1"),
    (r"你好，?(.+)", r"Hello, \1"),
    (r"您好，?(.+)", r"Hello, \1"),

    # Common phrases
    (r"这两天(.+)", r"\1 recently"),
    (r"最近(.+)", r"\1 lately"),
    (r"给我拿了些(.+)", r"brought me some \1"),
    (r"泡水喝", r"for tea"),
    (r"记不清名字了", r"but I can't remember the name"),
    (r"医生开了什么(.+)，但我记不清名字了", r"The doctor prescribed \1, but I can't remember the name"),

    # Medical advice
    (r"建议(.+)", r"Recommend \1"),
    (r"需要注意(.+)", r"Need to pay attention to \1"),
    (r"避免(.+)", r"Avoid \1"),
    (r"如果出现(.+)，立即建议就医", r"If \1 occurs, seek immediate medical attention"),
    (r"在没有充分检查依据时，不能给出确定性诊断", r"Cannot provide definitive diagnosis without sufficient examination"),
    (r"使用'可能'、'疑似'、'需要排除'等词汇", r"Use terms like 'possibly', 'suspected', 'needs to be ruled out'"),

    # Inquiry questions
    (r"这个问题持续多久了\？", r"How long has this problem been going on?"),
    (r"严重程度如何\？有没有加重或缓解\？", r"How severe is it? Has it gotten worse or better?"),
    (r"目前吃什么药\？", r"What medications are you currently taking?"),
    (r"有没有药物过敏史\？", r"Do you have any history of drug allergies?"),

    # Notes and descriptions
    (r"判断病情发展阶段", r"Determine the stage of disease development"),
    (r"评估病情严重性", r"Assess disease severity"),
    (r"避免药物相互作用", r"Avoid drug interactions"),
    (r"避免过敏反应", r"Avoid allergic reactions"),
    (r"识别危险信号并给出紧急建议", r"Identify danger signs and provide emergency advice"),
    (r"Response should address patient's concern", r"Response should address patient's concern"),
    (r"Real Chinese medical dialogue from (.+)\.", r"Real medical dialogue from \1."),
}


def contains_chinese(text: str) -> bool:
    """Check if text contains Chinese characters."""
    return bool(re.search(r'[\u4e00-\u9fff]', text))


def translate_text(text: str, max_passes: int = 3) -> str:
    """
    Translate Chinese text to English using multiple strategies.

    Args:
        text: Input text that may contain Chinese
        max_passes: Maximum number of translation passes

    Returns:
        Translated text
    """
    if not text or not isinstance(text, str):
        return text

    if not contains_chinese(text):
        return text

    result = text

    # Multiple translation passes for better coverage
    for _ in range(max_passes):
        previous_result = result

        # Step 1: Apply medical dictionary replacements
        for cn, en in sorted(MEDICAL_DICT.items(), key=lambda x: len(x[0]), reverse=True):
            result = result.replace(cn, en)

        # Step 2: Apply sentence pattern replacements
        for pattern, replacement in SENTENCE_PATTERNS:
            result = re.sub(pattern, replacement, result)

        # If no changes made, we're done
        if result == previous_result:
            break

    # Clean up common artifacts
    result = re.sub(r'\?+', '?', result)  # Multiple question marks
    result = re.sub(r'，+', ',', result)  # Multiple commas
    result = re.sub(r'。+', '.', result)  # Multiple periods
    result = re.sub(r'\s+', ' ', result)  # Multiple spaces
    result = result.strip()

    return result


def translate_dict_recursively(obj: Any, context: str = "") -> Any:
    """
    Recursively translate all Chinese text in a nested dictionary/list structure.
    """
    if isinstance(obj, dict):
        translated = {}
        for key, value in obj.items():
            # Translate the value
            new_context = f"{context}.{key}" if context else key

            if isinstance(value, str):
                translated[key] = translate_text(value, new_context)
            elif isinstance(value, (dict, list)):
                translated[key] = translate_dict_recursively(value, new_context)
            else:
                translated[key] = value
        return translated

    elif isinstance(obj, list):
        return [translate_dict_recursively(item, context) for item in obj]

    else:
        return obj


def smart_translate_task(task: Dict[str, Any], task_idx: int) -> Dict[str, Any]:
    """
    Smart translation of a task with context awareness.
    """
    # Create a deep copy to avoid modifying original
    import copy
    translated_task = copy.deepcopy(task)

    # Translate entire structure recursively
    translated_task = translate_dict_recursively(translated_task, f"task_{task_idx}")

    # Ensure English department field is added
    if "metadata" in translated_task and "department_cn" in translated_task["metadata"]:
        dept_cn = translated_task["metadata"]["department_cn"]
        dept_en = MEDICAL_DICT.get(dept_cn, dept_cn)
        translated_task["metadata"]["department_en"] = dept_en

    return translated_task


def generate_english_version_v2(
    input_file: Path,
    output_file: Path,
    max_tasks: int = None
):
    """Generate improved English version of tasks JSON file."""

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

        translated_task = smart_translate_task(task, i)
        translated_tasks.append(translated_task)

    print(f"  Completed: {len(translated_tasks)}/{len(tasks)}")

    # Write output
    print(f"\nWriting to: {output_file}")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(translated_tasks, f, ensure_ascii=False, indent=2)

    file_size_mb = output_file.stat().st_size / (1024 * 1024)

    # Check for remaining Chinese characters
    with open(output_file, 'r', encoding='utf-8') as f:
        content = f.read()
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', content)
        chinese_count = len(chinese_chars)

    print(f"\nFile generated successfully!")
    print(f"  Tasks: {len(translated_tasks)}")
    print(f"  Size: {file_size_mb:.2f} MB")
    print(f"  Remaining Chinese characters: {chinese_count}")

    if chinese_count > 0:
        # Show some examples of remaining Chinese
        sample_matches = re.findall(r'.{0,20}[\u4e00-\u9fff].{0,20}', content)[:10]
        print(f"\n  Sample remaining Chinese text:")
        for match in sample_matches:
            print(f"    - {match}")

    return translated_tasks, chinese_count


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
        translated_tasks, chinese_count = generate_english_version_v2(input_file, output_file)

        print()
        print("=" * 70)
        print("Translation Complete!")
        print("=" * 70)
        print()
        print("Input:  ", input_file)
        print("Output: ", output_file)
        print()

        if chinese_count < 100:
            print("Status: Excellent translation (>99% English)")
        elif chinese_count < 500:
            print("Status: Good translation (>95% English)")
        elif chinese_count < 2000:
            print("Status: Acceptable translation (>90% English)")
        else:
            print("Status: Needs review - some Chinese text remains")

        print()
        print("Both Chinese and English versions are now available.")

    except FileNotFoundError as e:
        print(f"Error: Input file not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in input file: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
