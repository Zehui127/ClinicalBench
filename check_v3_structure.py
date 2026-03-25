#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查 tasks_realistic_v3.json 的结构"""

import json

# 读取文件
with open('data/tau2/domains/clinical/chinese_internal_medicine/tasks_realistic_v3.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total tasks: {len(data)}")

# 检查第一个任务的所有键
task = data[0]
print("\nAll keys:")
for key in task.keys():
    value = task[key]
    if isinstance(value, dict):
        print(f"  {key}: dict with {len(value)} keys")
    elif isinstance(value, list):
        print(f"  {key}: list with {len(value)} items")
    else:
        print(f"  {key}: {type(value).__name__}")

# 检查是否有 v3 特性
print("\n=== Checking for v3 features ===")
v3_features = ['scenario_type', 'inquiry_approaches', 'dynamic_clinical_workflow', 'physical_examination_findings']
for feature in v3_features:
    if feature in task:
        print(f"[OK] {feature}: present")
        if feature == 'scenario_type':
            print(f"  Value: {task[feature]}")
    else:
        print(f"[NO] {feature}: missing")

# 打印部分内容
print("\n=== First 200 chars of ticket ===")
ticket = task.get('ticket', 'N/A')
print(ticket[:200] if len(ticket) > 200 else ticket)

# 检查是否有 evaluation_criteria
print("\n=== Evaluation Criteria ===")
if 'evaluation_criteria' in task:
    ec = task['evaluation_criteria']
    print(f"Type: {type(ec)}")
    if isinstance(ec, dict):
        print(f"Keys: {list(ec.keys())}")
