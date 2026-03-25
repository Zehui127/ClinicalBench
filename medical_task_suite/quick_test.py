"""
Quick Test Suite for Medical Task Suite
Tests core functionality with correct API usage
"""

import sys
from datetime import datetime

print("=" * 80)
print("MEDICAL TASK SUITE - QUICK TEST")
print("=" * 80)
print(f"Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

tests_passed = 0
tests_failed = 0

def run_test(test_name, test_func):
    """Run a test function and track results."""
    global tests_passed, tests_failed
    print(f"\n[TEST] {test_name}")
    print("-" * 80)
    try:
        test_func()
        print(f"[PASS] {test_name}")
        tests_passed += 1
        return True
    except Exception as e:
        print(f"[FAIL] {test_name}")
        print(f"   Error: {str(e)}")
        tests_failed += 1
        import traceback
        traceback.print_exc()
        return False

# ============================================================================
# TEST 1: Module Registry
# ============================================================================
def test_module_registry():
    """Test that all 13 modules are registered."""
    from modules import MODULE_REGISTRY

    assert len(MODULE_REGISTRY) == 13, f"Expected 13 modules, got {len(MODULE_REGISTRY)}"
    print(f"  [OK] All 13 modules registered")

    # Check priorities
    priorities = {}
    for module_id, info in MODULE_REGISTRY.items():
        priorities[info['priority']] = priorities.get(info['priority'], 0) + 1

    print(f"  [OK] P0: {priorities.get('P0', 0)}, P1: {priorities.get('P1', 0)}, " +
          f"P2: {priorities.get('P2', 0)}, P3: {priorities.get('P3', 0)}")

run_test("Module Registry", test_module_registry)

# ============================================================================
# TEST 2: Create Module
# ============================================================================
def test_create_module():
    """Test creating a module."""
    from modules import create_lab_test_inquiry_module

    module = create_lab_test_inquiry_module()
    assert module.config.module_id == "module_01"
    print(f"  [OK] Module 01 created")

run_test("Create Module", test_create_module)

# ============================================================================
# TEST 3: Generate Requirements
# ============================================================================
def test_generate_requirements():
    """Test generating task requirements."""
    from modules import create_lab_test_inquiry_module

    module = create_lab_test_inquiry_module()
    req = module.generate_task_requirements(
        difficulty='L2',
        patient_behavior='forgetful',
        context={'symptoms': ['chest pain']}
    )

    assert 'difficulty' in req
    assert req['difficulty'] == 'L2'
    print(f"  [OK] Requirements generated for L2")

run_test("Generate Requirements", test_generate_requirements)

# ============================================================================
# TEST 4: Red Line Detection (Module Level)
# ============================================================================
def test_module_red_line():
    """Test red line detection at module level."""
    from modules import create_lab_test_inquiry_module

    module = create_lab_test_inquiry_module()
    violations = module.check_red_line_violation(
        agent_response="I'll prescribe medication for you",
        task_context={'symptoms': ['chest pain']},
        conversation_history=[{'role': 'patient', 'content': 'I have chest pain'}]
    )

    print(f"  [OK] Red line check completed")
    print(f"  [OK] Violations found: {len(violations)}")

run_test("Module Red Line Detection", test_module_red_line)

# ============================================================================
# TEST 5: Module Integrator
# ============================================================================
def test_module_integrator():
    """Test module integrator."""
    from optimization.core.module_integrator import ModuleIntegrator

    integrator = ModuleIntegrator()
    assert len(integrator.module_definitions) == 13
    print(f"  [OK] ModuleIntegrator initialized")
    print(f"  [OK] Loaded {len(integrator.module_definitions)} module definitions")

run_test("Module Integrator", test_module_integrator)

# ============================================================================
# TEST 6: Red Line Detector
# ============================================================================
def test_red_line_detector():
    """Test RedLineDetector."""
    from evaluation import RedLineDetector

    detector = RedLineDetector()
    print(f"  [OK] RedLineDetector initialized")
    print(f"  [OK] Global rules: {len(detector.rules['global'])}")
    print(f"  [OK] Module rules: {len(detector.rules['module_specific'])}")

run_test("Red Line Detector", test_red_line_detector)

# ============================================================================
# TEST 7: Confidence Scorer
# ============================================================================
def test_confidence_scorer():
    """Test ConfidenceScorer."""
    from evaluation import ConfidenceScorer

    scorer = ConfidenceScorer()
    print(f"  [OK] ConfidenceScorer initialized")
    print(f"  [OK] Weights loaded: {scorer.weights is not None}")

run_test("Confidence Scorer", test_confidence_scorer)

# ============================================================================
# TEST 8: Advanced Features - Temporal Consistency
# ============================================================================
def test_temporal_consistency():
    """Test TemporalConsistencyVerifier."""
    from advanced_features import TemporalConsistencyVerifier

    verifier = TemporalConsistencyVerifier()

    # Add conversation turns
    verifier.add_conversation_turn(
        turn_number=1,
        role='patient',
        content='I am allergic to penicillin',
        extracted_info={'allergies': ['penicillin']}
    )
    verifier.add_conversation_turn(
        turn_number=2,
        role='patient',
        content='I have no allergies',
        extracted_info={'allergies': ['none']}  # Contradiction
    )

    # Verify
    result = verifier.verify_consistency()

    print(f"  [OK] TemporalConsistencyVerifier initialized")
    print(f"  [OK] Verification completed")
    print(f"  [OK] Result keys: {list(result.keys())}")

run_test("Temporal Consistency", test_temporal_consistency)

# ============================================================================
# TEST 9: Advanced Features - Execution Chain
# ============================================================================
def test_execution_chain():
    """Test ExecutionChainAnnotator."""
    from advanced_features import ExecutionChainAnnotator

    annotator = ExecutionChainAnnotator()

    # Annotate with conversation_id
    decision = annotator.annotate_decision_point(
        conversation_id='test_conv_001',
        turn_number=1,
        agent_action="requested_lab_test",
        patient_message="I had lab tests but forget values",
        context={'symptoms': ['chest pain'], 'module_triggered': 'module_01'}
    )

    print(f"  [OK] ExecutionChainAnnotator initialized")
    print(f"  [OK] Decision type: {decision.decision_type}")

run_test("Execution Chain", test_execution_chain)

# ============================================================================
# TEST 10: Advanced Features - Adversarial Test Suite
# ============================================================================
def test_adversarial_suite():
    """Test AdversarialTestSuite."""
    from advanced_features import AdversarialTestSuite

    suite = AdversarialTestSuite()

    print(f"  [OK] AdversarialTestSuite initialized")
    print(f"  [OK] Total test cases: {len(suite.test_cases)}")

    # Get tests by type
    malicious = suite.get_test_cases_by_type('malicious_inducement')
    print(f"  [OK] Malicious inducement tests: {len(malicious)}")

run_test("Adversarial Test Suite", test_adversarial_suite)

# ============================================================================
# TEST 11: Advanced Features - Cross-Session Memory
# ============================================================================
def test_cross_session_memory():
    """Test CrossSessionMemoryManager."""
    from advanced_features import CrossSessionMemoryManager

    memory_manager = CrossSessionMemoryManager()

    # Create a session
    memory_manager.create_session(
        patient_id='P001',
        conversation_id='conv_001',
        initial_context={'diagnosis': 'hypertension', 'medications': ['nifedipine']}
    )

    # Get context - returns dict, not object
    context = memory_manager.get_patient_context('conv_001')

    print(f"  [OK] CrossSessionMemoryManager initialized")
    print(f"  [OK] Session created and retrieved")

run_test("Cross-Session Memory", test_cross_session_memory)

# ============================================================================
# TEST 12: Module Coverage Analyzer
# ============================================================================
def test_module_coverage():
    """Test ModuleCoverageAnalyzer."""
    from evaluation import ModuleCoverageAnalyzer

    analyzer = ModuleCoverageAnalyzer()

    # Create sample tasks
    sample_tasks = [
        {'modules_tested': ['module_01', 'module_04']},
        {'modules_tested': ['module_02', 'module_03']},
        {'modules_tested': ['module_13']},
    ]

    report = analyzer.analyze_dataset_coverage(sample_tasks)

    print(f"  [OK] ModuleCoverageAnalyzer initialized")
    print(f"  [OK] Overall coverage: {report.overall_coverage_percentage:.1f}%")

run_test("Module Coverage Analyzer", test_module_coverage)

# ============================================================================
# TEST 13: Emergency Handling
# ============================================================================
def test_emergency_handling():
    """Test Emergency Handling module."""
    from modules import create_emergency_handling_module

    emergency_module = create_emergency_handling_module()

    violations = emergency_module.check_red_line_violation(
        agent_response="It's probably fine, just rest",
        task_context={'symptoms': ['chest pain', 'shortness of breath']},
        conversation_history=[{'role': 'patient', 'content': 'I have chest pain and cant breathe'}]
    )

    print(f"  [OK] Emergency handling module tested")
    print(f"  [OK] Violations: {len(violations)}")

run_test("Emergency Handling", test_emergency_handling)

# ============================================================================
# SUMMARY
# ============================================================================
print()
print("=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print(f"Total Tests: {tests_passed + tests_failed}")
print(f"Passed: {tests_passed}")
print(f"Failed: {tests_failed}")
print()

if tests_failed == 0:
    print("SUCCESS! All tests passed.")
else:
    print(f"WARNING: {tests_failed} test(s) failed.")

print("=" * 80)
print(f"Test Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

sys.exit(0 if tests_failed == 0 else 1)
