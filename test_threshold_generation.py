#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试追问阈值规则生成"""
import sys
import json
sys.path.insert(0, 'DataQualityFiltering')

from modules.inquiry_threshold_validator import InquiryThresholdValidator

# 设置UTF-8编码输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("="*60)
print("测试追问阈值规则生成")
print("="*60)

# 创建validator
config = {}
validator = InquiryThresholdValidator(config)

# 测试任务
test_task = {
    'id': 'test_1',
    'scenario_type': 'INFORMATION_QUERY',
    'ticket': '高血压患者能吃党参吗？'
}

print("\n输入任务:")
print(json.dumps(test_task, ensure_ascii=False, indent=2))

# 生成规则
print("\n开始生成规则...")
try:
    rules = validator.generate_threshold_rules(test_task)
    print("\n生成的规则:")
    print(json.dumps(rules, ensure_ascii=False, indent=2))
    print(f"\n规则包含 {len(rules)} 个字段")
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
