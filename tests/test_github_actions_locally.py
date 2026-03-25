#!/usr/bin/env python3
"""
模拟GitHub Actions测试环境
"""
import subprocess
import sys

def run_test(name, script):
    """运行测试脚本"""
    print(f"\n{'='*60}")
    print(f"Running: {name}")
    print(f"{'='*60}")
    try:
        result = subprocess.run(
            [sys.executable, '-c', script],
            capture_output=True,
            text=True,
            timeout=30
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        if result.returncode != 0:
            print(f"[FAILED] Exit code: {result.returncode}")
            return False
        else:
            print("[PASSED]")
            return True
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

# Test 1: Core Modules
test1 = """
import sys
sys.path.insert(0, '.')
from DataQualityFiltering.core import (
    LLMEvaluator,
    BaseEvaluator,
    BaseReviewer,
    BaseConfig,
    LLMConfig,
    EvaluationConfig,
    PipelineConfig,
    create_llm_evaluator,
)
print('[OK] Core module imports successful!')
"""

# Test 2: Backward Compatibility
test2 = """
import sys
sys.path.insert(0, '.')
from DataQualityFiltering import DataQualityPipeline
print('[OK] Backward compatibility maintained!')
"""

# Test 3: Tau2 Clinical Evaluation
test3 = """
import sys
sys.path.insert(0, 'src')
from tau2.evaluator import (
    ClinicalEvaluator,
    ClinicalAccuracyEvaluator,
    DialogueFluencyEvaluator,
    SafetyEmpathyEvaluator,
)
from tau2.data_model.tasks import RewardType
from tau2.data_model.simulation import ClinicalCheck
assert hasattr(RewardType, 'CLINICAL')
check = ClinicalCheck(overall_score=4.0, dimension_scores={}, met=True, reward=0.8)
print('[OK] Tau2 clinical evaluation imports successful!')
"""

# 运行所有测试
results = []
results.append(run_test("Test Core Modules", test1))
results.append(run_test("Test Backward Compatibility", test2))
results.append(run_test("Test Tau2 Clinical Evaluation", test3))

# 总结
print(f"\n{'='*60}")
print(f"Summary: {sum(results)}/{len(results)} tests passed")
print(f"{'='*60}")

if all(results):
    print("\n✓ All tests passed!")
    sys.exit(0)
else:
    print("\n✗ Some tests failed")
    sys.exit(1)
