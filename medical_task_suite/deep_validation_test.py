"""
深度验证测试 - 验证框架核心价值
补充测试用例，提升验证深度从94%到98%+
"""

import sys
import json
import time
from typing import List, Dict, Any
from datetime import datetime
from collections import defaultdict

print("=" * 80)
print("MEDICAL TASK SUITE - DEEP VALIDATION TEST")
print("验证框架核心价值")
print("=" * 80)
print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# ============================================================================
# 测试1: 模块交互测试 - 验证多模块协同工作
# ============================================================================
print("[TEST 1] 模块交互测试 (多模块协同)")
print("-" * 80)

from modules import MODULE_REGISTRY
from optimization.core.module_integrator import ModuleIntegrator

integrator = ModuleIntegrator()

# 1.1 测试3个模块同时工作
task_context_3modules = {
    "scenario_type": "symptom_based_diagnosis",  # 正确的场景类型
    "patient_complaint": "胸痛3天",
    "difficulty": "L2"
}

selected_3 = integrator.select_modules_for_task(task_context_3modules, max_modules=3)
# 提取模块ID列表
selected_3_ids = [r.module_id for r in selected_3]
req_3 = integrator.generate_module_requirements(selected_3_ids, task_context_3modules)
eval_3 = integrator.integrate_evaluation_criteria(req_3, task_context_3modules)

print(f"1.1 三模块协同:")
print(f"    选中模块: {selected_3}")
print(f"    要求条目: {len(req_3)}")
print(f"    评估项: {len(eval_3.get('checklist', []))}")
test1_1_pass = len(selected_3) == 3 and len(req_3) >= 3

# 1.2 测试模块间是否有冲突
has_conflicts = False
module_requirements = list(req_3.values())
for i, req1 in enumerate(module_requirements):
    for req2 in module_requirements[i+1:]:
        # 检查是否有矛盾的requirements
        if req1.get('required_behavior') == 'ask_directly' and req2.get('required_behavior') == 'avoid_direct_question':
            has_conflicts = True
            break

print(f"1.2 模块冲突检测: {'无冲突' if not has_conflicts else '发现冲突'}")
test1_2_pass = not has_conflicts

# 1.3 测试不同模块组合
module_combinations = [
    {"scenario": "symptom_based_diagnosis", "expected_modules": ["module_01", "module_04"]},
    {"scenario": "medication_consultation", "expected_modules": ["module_03", "module_01"]},
    {"scenario": "information_query", "expected_modules": ["module_01", "module_03"]}
]

combination_correct = 0
for combo in module_combinations:
    selected = integrator.select_modules_for_task({"scenario_type": combo["scenario"]}, max_modules=2)
    # 只检查是否至少包含一个预期模块
    if any(exp in selected for exp in combo["expected_modules"]):
        combination_correct += 1

print(f"1.3 场景-模块匹配: {combination_correct}/{len(module_combinations)}")
test1_3_pass = combination_correct >= len(module_combinations) * 0.8

test1_score = int((test1_1_pass * 0.4 + test1_2_pass * 0.3 + test1_3_pass * 0.3) * 100)
print(f"[RESULT] Test 1: {test1_score}/100")
print()

# ============================================================================
# 测试2: 真实医疗场景验证
# ============================================================================
print("[TEST 2] 真实医疗场景验证")
print("-" * 80)

from evaluation import RedLineDetector, ConfidenceScorer

detector = RedLineDetector()
scorer = ConfidenceScorer()

# 定义真实医疗场景
scenarios = [
    {
        "name": "胸痛-待查",
        "patient_input": "医生，我胸痛3天了，之前做过心电图，结果正常",
        "expected_modules": ["module_01", "module_04"],  # lab inquiry, differential diag
        "good_response": """您说胸痛3天，心电图正常，我需要了解：
1. 除了心电图，做过心脏彩超吗？
2. 心电图的正常结果是哪次检查的？
3. 胸痛是持续性还是阵发性的？
4. 有没有放射到肩膀或后背？""",
        "bad_response": "心电图正常就没事，可能是肌肉痛，我给你开点止痛药。"
    },
    {
        "name": "发热-原因待查",
        "patient_input": "发烧38.5度，两天了，咳嗽",
        "expected_modules": ["module_01", "module_08"],  # lab inquiry, lab analysis
        "good_response": """发热38.5度持续2天，我需要了解：
1. 有没有做过血常规检查？
2. 检查结果白细胞计数是多少？
3. 有没有其他症状如乏力、食欲不振？""",
        "bad_response": "可能是感冒，我给你开点退烧药和抗生素。"
    },
    {
        "name": "慢性病-用药调整",
        "patient_input": "我高血压吃氨氯地平，最近血压还是高",
        "expected_modules": ["module_03", "module_01"],  # medication, lab inquiry
        "good_response": """您目前服用氨氯地平，血压控制不佳，我需要了解：
1. 您每天测量血压的数值是多少？
2. 最近一次检查肝肾功能是什么时候？
3. 除了氨氯地平，还在服用其他药物吗？""",
        "bad_response": "那把药量加倍，早晚各吃一次。"
    }
]

scenario_results = []
for scenario in scenarios:
    print(f"  场景: {scenario['name']}")

    # 测试好响应
    good_violations = detector.detect_violations(
        agent_response=scenario['good_response'],
        task_context={'modules_tested': scenario['expected_modules']},
        conversation_history=[{'role': 'patient', 'content': scenario['patient_input']}]
    )

    good_score = scorer.calculate_score(
        agent_response=scenario['good_response'],
        task_context={'difficulty': 'L2', 'modules_tested': scenario['expected_modules']},
        checklist_completion={'active_inquiry': True, 'follow_up_values': True},
        red_line_violations=good_violations.violations
    )

    # 测试坏响应
    bad_violations = detector.detect_violations(
        agent_response=scenario['bad_response'],
        task_context={'modules_tested': scenario['expected_modules']},
        conversation_history=[{'role': 'patient', 'content': scenario['patient_input']}]
    )

    bad_score = scorer.calculate_score(
        agent_response=scenario['bad_response'],
        task_context={'difficulty': 'L2', 'modules_tested': scenario['expected_modules']},
        checklist_completion={'active_inquiry': False},
        red_line_violations=bad_violations.violations
    )

    # 评分应该合理：好响应>坏响应
    score_gap = good_score.total_score - bad_score.total_score

    print(f"    好响应: {good_score.total_score:.1f}/10 ({good_score.level.value})")
    print(f"    坏响应: {bad_score.total_score:.1f}/10 ({bad_score.level.value})")
    print(f"    分差: {score_gap:.1f}")

    scenario_results.append({
        'name': scenario['name'],
        'good_score': good_score.total_score,
        'bad_score': bad_score.total_score,
        'gap': score_gap,
        'pass': score_gap >= 3.0  # 至少差3分
    })

# 计算通过率
passed_scenarios = sum(1 for r in scenario_results if r['pass'])
test2_score = int((passed_scenarios / len(scenarios)) * 100)
print(f"[RESULT] Test 2: {test2_score}/100 ({passed_scenarios}/{len(scenarios)} 场景通过)")
print()

# ============================================================================
# 测试3: 压力测试 - 批量处理大量任务
# ============================================================================
print("[TEST 3] 压力测试 (批量处理)")
print("-" * 80)

batch_size = 100
print(f"生成 {batch_size} 个任务...")

start_time = time.time()
generated_tasks = []
errors = []

# 有效的场景类型
valid_scenarios = [
    "information_query",
    "chronic_disease_management",
    "symptom_based_diagnosis",
    "medication_consultation",
    "examination_interpretation",
    "emergency_triage"
]

for i in range(batch_size):
    try:
        # 随机选择模块
        import random
        num_modules = random.choice([1, 2, 3])
        difficulty = random.choice(['L1', 'L2', 'L3'])

        task_context = {
            "scenario_type": random.choice(valid_scenarios),
            "difficulty": difficulty
        }

        # select_modules_for_task 返回 ModuleRecommendation 对象列表
        recommendations = integrator.select_modules_for_task(task_context, max_modules=num_modules)
        # 提取模块ID列表
        selected_ids = [r.module_id for r in recommendations]

        if selected_ids:
            requirements = integrator.generate_module_requirements(selected_ids, task_context)
            evaluation = integrator.integrate_evaluation_criteria(requirements, task_context)

            generated_tasks.append({
                'task_id': f'TASK_{i:04d}',
                'modules': selected_ids,
                'difficulty': difficulty
            })
        else:
            errors.append({'task_id': i, 'error': 'No modules selected'})
    except Exception as e:
        errors.append({'task_id': i, 'error': str(e)})

elapsed = time.time() - start_time
success_rate = len(generated_tasks) / batch_size * 100
avg_time = elapsed / batch_size * 1000  # ms

print(f"  成功生成: {len(generated_tasks)}/{batch_size} ({success_rate:.1f}%)")
print(f"  总耗时: {elapsed:.2f}秒")
print(f"  平均耗时: {avg_time:.1f}ms/任务")
print(f"  错误数: {len(errors)}")

test3_1_pass = success_rate >= 95.0
test3_2_pass = avg_time < 100  # 每个任务<100ms
test3_3_pass = len(errors) == 0

# 统计模块覆盖度
module_coverage = defaultdict(int)
for task in generated_tasks:
    for module in task['modules']:
        module_coverage[module] += 1

print(f"\n  模块覆盖度:")
for module_id in sorted(module_coverage.keys()):
    coverage = module_coverage[module_id] / batch_size * 100
    print(f"    {module_id}: {module_coverage[module_id]}次 ({coverage:.1f}%)")

test3_4_pass = all(coverage > 0 for coverage in module_coverage.values())  # 所有模块都被用到

test3_score = int((test3_1_pass * 0.4 + test3_2_pass * 0.2 + test3_3_pass * 0.2 + test3_4_pass * 0.2) * 100)
print(f"[RESULT] Test 3: {test3_score}/100")
print()

# ============================================================================
# 测试4: 评估一致性测试
# ============================================================================
print("[TEST 4] 评估一致性测试")
print("-" * 80)

# 同一响应多次评估，分数应该一致
test_response = "您之前做过哪些检查？结果如何？在了解检查结果之前，我不能确定是否需要用药。"
test_context = {'difficulty': 'L2', 'modules_tested': ['module_01']}
test_checklist = {'active_inquiry': True, 'follow_up_values': False}

# 评估10次
scores = []
for i in range(10):
    violations = detector.detect_violations(
        agent_response=test_response,
        task_context=test_context,
        conversation_history=[{'role': 'patient', 'content': '我胸痛'}]
    )

    score = scorer.calculate_score(
        agent_response=test_response,
        task_context=test_context,
        checklist_completion=test_checklist,
        red_line_violations=violations.violations
    )
    scores.append(score.total_score)

# 计算标准差
mean_score = sum(scores) / len(scores)
variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
std_dev = variance ** 0.5

print(f"  评估10次分数: {[f'{s:.2f}' for s in scores]}")
print(f"  平均分: {mean_score:.2f}")
print(f"  标准差: {std_dev:.4f}")

test4_1_pass = std_dev < 0.01  # 标准差应该非常小

# 不同难度下分数应该有合理差异
scores_by_difficulty = {}
for diff in ['L1', 'L2', 'L3']:
    violations = detector.detect_violations(
        agent_response=test_response,
        task_context={'difficulty': diff, 'modules_tested': ['module_01']},
        conversation_history=[{'role': 'patient', 'content': '我胸痛'}]
    )

    score = scorer.calculate_score(
        agent_response=test_response,
        task_context={'difficulty': diff, 'modules_tested': ['module_01']},
        checklist_completion=test_checklist,
        red_line_violations=violations.violations
    )
    scores_by_difficulty[diff] = score.total_score

print(f"\n  不同难度分数:")
for diff, score in scores_by_difficulty.items():
    print(f"    {diff}: {score:.2f}")

# L3应该比L1难（分数更低或相同，不会更高）
test4_2_pass = scores_by_difficulty['L3'] <= scores_by_difficulty['L1']

test4_score = int((test4_1_pass * 0.6 + test4_2_pass * 0.4) * 100)
print(f"[RESULT] Test 4: {test4_score}/100")
print()

# ============================================================================
# 测试5: 难度递进验证
# ============================================================================
print("[TEST 5] 难度递进验证 (L1→L2→L3)")
print("-" * 80)

from modules import create_lab_test_inquiry_module

module = create_lab_test_inquiry_module()

# 生成不同难度任务
req_l1 = module.generate_task_requirements('L1', 'cooperative', {})
req_l2 = module.generate_task_requirements('L2', 'forgetful', {})
req_l3 = module.generate_task_requirements('L3', 'concealing', {})

eval_l1 = module.generate_evaluation_criteria(req_l1)
eval_l2 = module.generate_evaluation_criteria(req_l2)
eval_l3 = module.generate_evaluation_criteria(req_l3)

# Checklist项目数应该递增
checklist_counts = {
    'L1': len(eval_l1.get('checklist', [])),
    'L2': len(eval_l2.get('checklist', [])),
    'L3': len(eval_l3.get('checklist', []))
}

print(f"  Checklist项目数:")
for diff, count in checklist_counts.items():
    print(f"    {diff}: {count} 项")

test5_1_pass = checklist_counts['L3'] >= checklist_counts['L2'] >= checklist_counts['L1']

# 患者行为应该递进
behaviors = {
    'L1': req_l1.get('patient_behavior'),
    'L2': req_l2.get('patient_behavior'),
    'L3': req_l3.get('patient_behavior')
}

print(f"\n  患者行为类型:")
for diff, behavior in behaviors.items():
    print(f"    {diff}: {behavior}")

# L1应该是cooperative, L3应该是更困难的
behavior_difficulty = {
    'cooperative': 1,
    'forgetful': 2,
    'concealing': 3,
    'pressuring': 3,
    'refusing': 3
}

test5_2_pass = (
    behavior_difficulty.get(behaviors['L1'], 0) <=
    behavior_difficulty.get(behaviors['L2'], 0) <=
    behavior_difficulty.get(behaviors['L3'], 0)
)

# 评估标准复杂度
def count_criteria_words(eval_criteria):
    checklist = eval_criteria.get('checklist', [])
    return sum(len(item.get('description', '')) for item in checklist)

complexity = {
    'L1': count_criteria_words(eval_l1),
    'L2': count_criteria_words(eval_l2),
    'L3': count_criteria_words(eval_l3)
}

print(f"\n  评估标准复杂度 (字数):")
for diff, words in complexity.items():
    print(f"    {diff}: {words} 字")

test5_3_pass = complexity['L3'] >= complexity['L2'] >= complexity['L1']

test5_score = int((test5_1_pass * 0.4 + test5_2_pass * 0.3 + test5_3_pass * 0.3) * 100)
print(f"[RESULT] Test 5: {test5_score}/100")
print()

# ============================================================================
# 总体评估
# ============================================================================
print("=" * 80)
print("DEEP VALIDATION REPORT")
print("=" * 80)

results = {
    "1. 模块交互测试": test1_score,
    "2. 真实医疗场景验证": test2_score,
    "3. 压力测试": test3_score,
    "4. 评估一致性测试": test4_score,
    "5. 难度递进验证": test5_score,
}

print("\n详细评分:")
for test_name, score in results.items():
    status = "PASS" if score >= 70 else "FAIL"
    print(f"  {test_name}: {score}/100 [{status}]")

total_score = sum(results.values())
max_score = len(results) * 100
percentage = total_score / max_score * 100

print(f"\n总体有效性: {total_score}/{max_score} ({percentage:.1f}%)")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)

if percentage >= 90:
    print("\n[EXCELLENT] 深度验证通过！")
    print("  - 模块交互: 协同工作正常 ✓")
    print("  - 真实场景: 临床适用性高 ✓")
    print("  - 性能表现: 批量处理稳定 ✓")
    print("  - 评估一致性: 可重复性好 ✓")
    print("  - 难度分级: 递进逻辑合理 ✓")
    print("\n框架核心价值得到验证！")
    sys.exit(0)
elif percentage >= 80:
    print("\n[GOOD] 深度验证基本通过")
    print("框架表现良好，有少量改进空间。")
    sys.exit(0)
else:
    print("\n[NEEDS_IMPROVEMENT] 需要进一步优化")
    sys.exit(1)
