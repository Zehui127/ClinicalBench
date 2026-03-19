#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查增强后的Tasks"""
import json
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

departments = ['内科', '外科', '妇产科', '儿科', '肿瘤科', '男科']

print("="*60)
print("检查所有科室的增强Tasks")
print("="*60)

for dept in departments:
    filename = f'DataQualityFiltering/test_outputs/enhanced_tasks_{dept}.json'
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)

            if not data:
                print(f"\n{dept}: 文件为空")
                continue

            # 检查第一个任务
            task = data[0]
            has_threshold = 'inquiry_threshold_validation' in task
            threshold_data = task.get('inquiry_threshold_validation', {})

            print(f"\n{dept}:")
            print(f"  总任务数: {len(data)}")
            print(f"  包含追问阈值规则: {'是' if has_threshold else '否'}")

            if threshold_data:
                scenario = threshold_data.get('scenario_type', 'N/A')
                risk = threshold_data.get('risk_level', 'N/A')
                min_questions = threshold_data.get('threshold_config', {}).get('min_questions_before_advice', 'N/A')
                print(f"  场景类型: {scenario}")
                print(f"  风险等级: {risk}")
                print(f"  最小问题数: {min_questions}")
    except Exception as e:
        print(f"\n{dept}: 错误 - {e}")

print("\n" + "="*60)
