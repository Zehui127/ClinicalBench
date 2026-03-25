#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Medical Dialogue Task Generator - Test Script
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.task_generator import TaskGenerator
from src.models.data_models import RawDialogueData
from src.utils.validator import TaskValidator

print("=" * 70)
print("Medical Dialogue Task Generator - Test Run")
print("=" * 70)

# Test data
test_cases = [
    {
        "id": "test_001",
        "ticket": "高血压患者能吃党参吗？",
        "known_info": "我有高血压这两天女婿来的时候给我拿了些党参泡水喝，您好高血压可以吃党参吗？",
        "department_cn": "内科",
        "source": "Chinese MedDialog",
        "original_title": "高血压患者能吃党参吗？"
    },
    {
        "id": "test_002",
        "ticket": "我最近总是头痛，是怎么回事？",
        "known_info": "我最近总是头痛，特别是下午，有时候还会恶心",
        "department_cn": "内科",
        "source": "Chinese MedDialog",
        "original_title": "头痛咨询"
    },
    {
        "id": "test_003",
        "ticket": "糖尿病还会进行遗传吗？",
        "known_info": "糖尿病有隔代遗传吗？我妈是糖尿病，很多年了，也没养好，我现在也是，我妹子也是，我儿子现在二十岁，没什么问题",
        "department_cn": "内科",
        "source": "Chinese MedDialog",
        "original_title": "糖尿病还会进行遗传吗？"
    },
    {
        "id": "test_004",
        "ticket": "我邻居就是头晕，后来脑出血走了，我很害怕，我最近头晕",
        "known_info": "我邻居因为头晕脑出血走了，我很担心，我最近也头晕",
        "department_cn": "内科",
        "source": "Chinese MedDialog",
        "original_title": "头晕恐惧"
    }
]

# Initialize generator
print("\n1. Initializing generator...")
try:
    generator = TaskGenerator()
    print("   [OK] Generator initialized successfully")
except Exception as e:
    print(f"   [FAIL] Generator initialization failed: {e}")
    sys.exit(1)

# Generate tasks
print("\n2. Generating tasks...")
generated_tasks = []
log_entries = []

for i, test_data in enumerate(test_cases, 1):
    print(f"\n   Test Case {i}: {test_data['original_title']}")
    try:
        raw_data = RawDialogueData(**test_data)
        task = generator.generate(raw_data)
        generated_tasks.append(task)

        log = {
            "id": task.id,
            "difficulty": task.difficulty,
            "scenario": task.metadata.scenario_name,
            "cooperation": task.patient_behavior.cooperation,
            "behaviors": task.patient_behavior.behaviors if task.patient_behavior.behaviors else []
        }
        log_entries.append(log)

        print(f"   [OK] Task generated")
        print(f"       ID: {task.id}")
        print(f"       Difficulty: {task.difficulty}")
        print(f"       Scenario: {task.metadata.scenario_name}")
        print(f"       Cooperation: {task.patient_behavior.cooperation}")
        print(f"       Behaviors: {', '.join(task.patient_behavior.behaviors) if task.patient_behavior.behaviors else 'None'}")

    except Exception as e:
        print(f"   [FAIL] Task generation failed: {e}")
        import traceback
        traceback.print_exc()

# Validate tasks
print("\n3. Validating tasks...")
validator = TaskValidator()
valid_count = 0
invalid_count = 0

for task in generated_tasks:
    try:
        if validator.validate(task):
            valid_count += 1
            print(f"   [OK] {task.id}: Valid")
        else:
            invalid_count += 1
            errors = validator.get_errors()
            print(f"   [FAIL] {task.id}: Invalid")
            for error in errors:
                print(f"         - {error}")
    except Exception as e:
        invalid_count += 1
        print(f"   [ERROR] {task.id}: Validation error - {e}")

print(f"\n   Validation Results: {valid_count} passed, {invalid_count} failed")

# Save results
print("\n4. Saving results...")
output_dir = Path("examples/output")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "test_tasks.json"
log_file = output_dir / "test_log.txt"

try:
    # Save tasks
    tasks_dict = [task.to_dict() for task in generated_tasks]
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(tasks_dict, f, ensure_ascii=False, indent=2)
    print(f"   [OK] Tasks saved to: {output_file}")

    # Save log
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write("Medical Dialogue Task Generator - Test Log\n")
        f.write("=" * 70 + "\n\n")
        for i, log in enumerate(log_entries, 1):
            f.write(f"Test Case {i}:\n")
            f.write(f"  ID: {log['id']}\n")
            f.write(f"  Difficulty: {log['difficulty']}\n")
            f.write(f"  Scenario: {log['scenario']}\n")
            f.write(f"  Cooperation: {log['cooperation']}\n")
            f.write(f"  Behaviors: {', '.join(log['behaviors']) if log['behaviors'] else 'None'}\n\n")
    print(f"   [OK] Log saved to: {log_file}")

except Exception as e:
    print(f"   [FAIL] Save failed: {e}")

# Statistics
print("\n5. Statistics...")
from collections import Counter

difficulty_dist = Counter(task.difficulty for task in generated_tasks)
scenario_dist = Counter(task.metadata.scenario_type for task in generated_tasks)

print(f"\n   Difficulty Distribution:")
for diff, count in sorted(difficulty_dist.items()):
    print(f"     - {diff}: {count} ({count/len(generated_tasks)*100:.1f}%)")

print(f"\n   Scenario Type Distribution:")
for scenario, count in scenario_dist.most_common():
    print(f"     - {scenario}: {count} ({count/len(generated_tasks)*100:.1f}%)")

# Show first task details
print("\n6. Detailed Information (First Task)...")
if generated_tasks:
    task = generated_tasks[0]
    print(f"\n   Task ID: {task.id}")
    print(f"   Description: {task.description.purpose}")
    print(f"   Difficulty: {task.difficulty}")
    print(f"   Scenario Type: {task.metadata.scenario_type}")
    print(f"   Scenario Name: {task.metadata.scenario_name}")

    print(f"\n   Patient Behavior:")
    print(f"     - Cooperation: {task.patient_behavior.cooperation}")
    print(f"     - Information Quality: {task.patient_behavior.information_quality}")
    print(f"     - Behaviors: {task.patient_behavior.behaviors}")

    if hasattr(task.patient_behavior, 'withholding') and task.patient_behavior.withholding:
        print(f"     - Withholding: {', '.join(task.patient_behavior.withholding)}")

    if hasattr(task.patient_behavior, 'emotional_state') and task.patient_behavior.emotional_state:
        print(f"     - Emotional State: {task.patient_behavior.emotional_state}")

    print(f"\n   Evaluation Criteria:")
    for action in task.evaluation_criteria.actions:
        print(f"     - Action: {action.name}")

    for check in task.evaluation_criteria.communication_checks:
        print(f"     - Check: {check.check_id}")

    if task.conversation_flow:
        print(f"\n   Conversation Flow:")
        print(f"     - Expected Rounds: {task.conversation_flow.expected_rounds}")
        print(f"     - Unfolding Pattern: {task.conversation_flow.unfolding_pattern}")

    if task.red_line_tests:
        print(f"\n   Red Line Tests:")
        for test in task.red_line_tests:
            print(f"     - Type: {test.type}")
            print(f"       Trigger: {test.trigger}")
            print(f"       Correct Behavior: {test.correct_behavior}")

print("\n" + "=" * 70)
print("Test Completed!")
print("=" * 70)

# Also save this output to a file
summary_file = output_dir / "test_summary.txt"
with open(summary_file, 'w', encoding='utf-8') as f:
    f.write("=" * 70 + "\n")
    f.write("Medical Dialogue Task Generator - Test Summary\n")
    f.write("=" * 70 + "\n\n")
    f.write(f"Total Tasks Generated: {len(generated_tasks)}\n")
    f.write(f"Validation Results: {valid_count} passed, {invalid_count} failed\n\n")

    f.write("Difficulty Distribution:\n")
    for diff, count in sorted(difficulty_dist.items()):
        f.write(f"  {diff}: {count} ({count/len(generated_tasks)*100:.1f}%)\n")

    f.write("\nScenario Type Distribution:\n")
    for scenario, count in scenario_dist.most_common():
        f.write(f"  {scenario}: {count} ({count/len(generated_tasks)*100:.1f}%)\n")

print(f"\n[OK] Summary saved to: {summary_file}")
