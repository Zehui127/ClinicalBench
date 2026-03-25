#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查所有科室的验证结果"""
import json
import os

departments = ['内科', '外科', '妇产科', '儿科', '肿瘤科', '男科']
print('科室验证结果汇总:\n')

for dept in departments:
    filename = f'DataQualityFiltering/test_outputs/validation_{dept}.json'
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            summary = data.get('summary', {})
            total = summary.get('total', 0)
            passed = summary.get('passed', 0)
            failed = summary.get('failed', 0)
            rate = summary.get('pass_rate', '0%')
            print(f'{dept}:')
            print(f'  总数: {total:,}')
            print(f'  通过: {passed:,} ({rate})')
            print(f'  失败: {failed:,}')
            print()
    else:
        print(f'{dept}: 文件不存在\n')
