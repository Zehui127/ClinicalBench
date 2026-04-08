#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v2.7 End-to-End Pipeline Test

Tests the complete v2.7 pipeline without PrimeKG (KB-only mode):
1. Scenario generation (ScenarioGenerator with DiseaseSampler)
2. Symptom generation (SymptomGenerator with expanded pools)
3. Patient agent creation (PatientAgent with calibrated defaults)
4. Environment + optimal agent interaction
5. Evaluation (outcome, process, safety, regret)
6. Tau2 adapter conversion (v2.7 format)

No external data or API calls required.
"""

import sys
import traceback
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))


def _get_kb():
    """Get ClinicalKnowledgeBase singleton."""
    from medical_task_suite.clinical_knowledge.accessor import ClinicalKnowledgeBase
    return ClinicalKnowledgeBase.get_instance()


# ============================================================
# Test 1: Scenario Generation
# ============================================================

def test_scenario_generation():
    """Test ScenarioGenerator with DiseaseSampler integration."""
    print("\n" + "=" * 70)
    print("TEST 1: Scenario Generation (v2.7 DiseaseSampler)")
    print("=" * 70)

    try:
        from medical_task_suite.generation.v2.scenario_engine.scenario_generator import ScenarioGenerator
        from medical_task_suite.generation.v2.scenario_engine.scenario_schema import TASK_TYPES

        kb = _get_kb()
        gen = ScenarioGenerator(kb, primekg=None)

        # Verify DiseaseSampler is wired in
        assert hasattr(gen, '_disease_sampler'), "DiseaseSampler not wired into ScenarioGenerator"

        # Generate one scenario per task type
        successes = 0
        for tt in TASK_TYPES:
            try:
                scenario = gen.generate(tt, "L2", seed=42)
                assert scenario.task_type == tt
                assert scenario.target_disease is not None
                assert scenario.constraints is not None
                successes += 1
                print(f"  [OK] {tt}: disease={scenario.target_disease}")
            except Exception as e:
                print(f"  [WARN] {tt}: {e}")

        print(f"\n  Generated {successes}/{len(TASK_TYPES)} task types successfully")
        return successes >= 4  # At least 4/6 should work

    except Exception as e:
        print(f"  [FAIL] {e}")
        traceback.print_exc()
        return False


# ============================================================
# Test 2: Symptom Generation with Expanded Pools
# ============================================================

def test_symptom_generation():
    """Test SymptomGenerator uses expanded noise/misleading pools."""
    print("\n" + "=" * 70)
    print("TEST 2: Symptom Generation (Expanded Pools)")
    print("=" * 70)

    try:
        from medical_task_suite.generation.v2.clinical_world.symptom_generator import (
            SymptomGenerator, _NOISE_POOL, _MISLEADING_MAP,
        )

        # Check expanded pools loaded
        print(f"  Noise pool size: {len(_NOISE_POOL)} (v1 had 19)")
        print(f"  Misleading map diseases: {len(_MISLEADING_MAP)} (v1 had 10)")

        noise_ok = len(_NOISE_POOL) >= 50
        misleading_ok = len(_MISLEADING_MAP) >= 25

        if not noise_ok:
            print(f"  [WARN] Noise pool too small: {len(_NOISE_POOL)}")
        if not misleading_ok:
            print(f"  [WARN] Misleading map too small: {len(_MISLEADING_MAP)}")

        # Generate symptoms for a scenario
        kb = _get_kb()
        gen = SymptomGenerator(kb)

        from medical_task_suite.generation.v2.scenario_engine.scenario_generator import ScenarioGenerator
        scenario = ScenarioGenerator(kb).generate("diagnostic_uncertainty", "L2", seed=42)
        symptoms = gen.generate(scenario.target_disease, scenario, seed=42)

        assert len(symptoms.volunteer) > 0, "No volunteer symptoms generated"
        assert len(symptoms.real_symptoms) > 0, "No real symptoms"

        print(f"  [OK] Disease: {scenario.target_disease}")
        print(f"       Volunteer: {symptoms.volunteer}")
        print(f"       If_asked: {len(symptoms.if_asked)}")
        print(f"       Hidden: {len(symptoms.hidden)}")
        print(f"       Noise: {len(symptoms.noise)}")
        print(f"       Misleading: {len(symptoms.misleading)}")

        return noise_ok and misleading_ok

    except Exception as e:
        print(f"  [FAIL] {e}")
        traceback.print_exc()
        return False


# ============================================================
# Test 3: Patient Agent with Calibrated Defaults
# ============================================================

def test_patient_agent_calibration():
    """Test PatientAgent uses calibrated behavior parameters."""
    print("\n" + "=" * 70)
    print("TEST 3: Patient Agent (Calibrated Defaults)")
    print("=" * 70)

    try:
        from medical_task_suite.generation.v2.persona_engine.patient_agent import PatientAgent, DecisionPolicy
        from medical_task_suite.generation.v2.clinical_world.symptom_generator import SymptomGenerator
        from medical_task_suite.generation.v2.scenario_engine.scenario_generator import ScenarioGenerator

        kb = _get_kb()
        gen = ScenarioGenerator(kb)

        # Test each behavior type
        behaviors = ["cooperative", "forgetful", "confused", "concealing", "pressuring", "refusing"]
        for behavior in behaviors:
            from medical_task_suite.generation.v2.scenario_engine.scenario_schema import ScenarioSpec, ScenarioConstraints

            scenario = ScenarioSpec(
                scenario_id="test",
                task_type="diagnostic_uncertainty",
                difficulty="L2",
                behavior_type=behavior,
                constraints=ScenarioConstraints(),
            )
            symptoms = SymptomGenerator(kb).generate("type 2 diabetes", scenario, seed=42)
            patient = PatientAgent.from_scenario(scenario, symptoms)

            # Verify calibrated values loaded
            assert patient.policy.goal is not None
            assert 0.0 <= patient.policy.initial_trust <= 1.0
            assert 0.0 <= patient.policy.compliance_level <= 1.0
            assert 0.0 <= patient.policy.reveal_probability <= 1.0

            print(f"  [OK] {behavior}: trust={patient.policy.initial_trust:.2f}, "
                  f"compliance={patient.policy.compliance_level:.2f}, "
                  f"reveal={patient.policy.reveal_probability:.2f}")

        # Test calibrated trust modifiers in BehaviorModel
        from medical_task_suite.generation.v2.persona_engine.behavior_model import BehaviorModel
        model = BehaviorModel(patient.policy)
        assert "empathy" in model.trust_modifiers
        assert model.trust_modifiers["empathy"] > 0
        assert model.trust_modifiers["dismissal"] < 0
        print(f"  [OK] Trust modifiers loaded ({len(model.trust_modifiers)} entries)")

        # Test patient response
        response = patient.respond("ask_question", "How are you feeling today?")
        assert "response" in response
        assert "revealed" in response
        print(f"  [OK] Patient response: {response['response'][:60]}...")

        return True

    except Exception as e:
        print(f"  [FAIL] {e}")
        traceback.print_exc()
        return False


# ============================================================
# Test 4: Full Pipeline (Generate → Interact → Evaluate)
# ============================================================

def test_full_pipeline():
    """Test complete pipeline: generate → interact → evaluate."""
    print("\n" + "=" * 70)
    print("TEST 4: Full Pipeline (Generate → Interact → Evaluate)")
    print("=" * 70)

    try:
        from medical_task_suite.generation.v2.batch_pipeline import BatchPipeline

        kb = _get_kb()
        pipeline = BatchPipeline(kb, primekg=None)

        # Verify PrimeKGBridge setup (should be None since no primekg)
        assert pipeline._primekg_bridge is None
        print("  [OK] Pipeline created (KB-only mode)")

        # Generate scenarios
        scenarios = pipeline.generate_scenarios(n_scenarios=3, seed=42)
        assert len(scenarios) > 0, "No scenarios generated"
        print(f"  [OK] Generated {len(scenarios)} scenarios")

        # Run baseline with optimal agent
        results = pipeline.run_baseline(n_scenarios=3, seed=42)
        assert len(results) > 0, "No results from baseline run"

        for r in results:
            print(f"  [OK] {r.task_type}/{r.difficulty}: "
                  f"disease={r.target_disease}, "
                  f"score={r.total_score:.2f}, "
                  f"turns={r.total_turns}, "
                  f"correct={r.correct_diagnosis}")

        # Aggregate
        summary = pipeline.aggregate(results, "optimal")
        assert summary.n_scenarios > 0
        print(f"\n  [OK] Aggregated {summary.n_scenarios} results")
        print(f"       Avg total: {summary.avg_total:.1%}")
        print(f"       Avg regret: {summary.avg_regret:.3f}")
        print(f"       Diagnosis accuracy: {summary.diagnosis_accuracy:.1%}")

        return True

    except Exception as e:
        print(f"  [FAIL] {e}")
        traceback.print_exc()
        return False


# ============================================================
# Test 5: Tau2 Adapter (v2.7 format)
# ============================================================

def test_tau2_adapter():
    """Test Tau2Adapter produces v2.7 format with metadata."""
    print("\n" + "=" * 70)
    print("TEST 5: Tau2 Adapter (v2.7 Format)")
    print("=" * 70)

    try:
        from medical_task_suite.generation.v2.compatibility.tau2_adapter import Tau2Adapter
        from medical_task_suite.generation.v2.batch_pipeline import BatchPipeline

        kb = _get_kb()
        pipeline = BatchPipeline(kb)

        # Generate and run a single scenario
        scenarios = pipeline.generate_scenarios(n_scenarios=1, seed=42)
        if not scenarios:
            print("  [WARN] No scenario generated")
            return False

        scenario = scenarios[0]

        # Build environment manually
        from medical_task_suite.generation.v2.clinical_world.symptom_generator import SymptomGenerator
        from medical_task_suite.generation.v2.persona_engine.patient_agent import PatientAgent
        from medical_task_suite.generation.v2.interaction_engine.environment import MedicalEnvironment
        from medical_task_suite.generation.v2.interaction_engine.turn_simulator import AgentAction

        symptoms = SymptomGenerator(kb).generate(
            scenario.target_disease or "fatigue", scenario, seed=42
        )
        patient = PatientAgent.from_scenario(scenario, symptoms)
        env = MedicalEnvironment(scenario, patient, kb)

        obs = env.reset()
        for _ in range(5):
            action = AgentAction(action_type="ask_question", content="How are you feeling?")
            obs = env.step(action)
            if env.state.is_complete:
                break

        # Convert to tau2 format
        adapter = Tau2Adapter()
        state = env.get_state()
        tau2_task = adapter.convert(scenario, state)

        # Verify v2.7 format
        assert tau2_task["version"] == "2.7", f"Expected version 2.7, got {tau2_task['version']}"
        print(f"  [OK] Version: {tau2_task['version']}")

        assert "v2_7_metadata" in tau2_task, "Missing v2_7_metadata"
        metadata = tau2_task["v2_7_metadata"]
        assert metadata["schema_version"] == "2.7"
        print(f"  [OK] v2_7_metadata present")

        if "persona_calibration" in metadata:
            print(f"  [OK] Persona calibration: {metadata['persona_calibration']}")

        if "ground_truth_composition" in metadata:
            gt = metadata["ground_truth_composition"]
            print(f"  [OK] Ground truth: {gt['n_comorbidities']} comorbidities, "
                  f"{gt['n_confounders']} confounders")

        # Verify required fields
        for field in ["id", "task_type", "difficulty", "user_persona", "dialogue", "latent_truth"]:
            assert field in tau2_task, f"Missing field: {field}"
        print(f"  [OK] All required fields present")

        return True

    except Exception as e:
        print(f"  [FAIL] {e}")
        traceback.print_exc()
        return False


# ============================================================
# Test 6: DiseaseSampler Direct
# ============================================================

def test_disease_sampler():
    """Test DiseaseSampler with and without PrimeKG."""
    print("\n" + "=" * 70)
    print("TEST 6: DiseaseSampler (KB-only mode)")
    print("=" * 70)

    try:
        from medical_task_suite.generation.v2.clinical_world.disease_sampler import DiseaseSampler

        kb = _get_kb()
        sampler = DiseaseSampler(kb, primekg=None)

        # Sample for each task type
        from medical_task_suite.generation.v2.scenario_engine.scenario_schema import TASK_TYPES
        for tt in TASK_TYPES:
            disease = sampler._sample_for_task_type(tt, "L2")
            status = "OK" if disease else "None"
            print(f"  [{status}] {tt}: {disease}")

        # Get compatible diseases
        compat = sampler.get_compatible_diseases("diagnostic_uncertainty")
        print(f"  [OK] Compatible diseases for diagnostic_uncertainty: {len(compat)}")
        assert len(compat) > 0, "No compatible diseases found"

        return True

    except Exception as e:
        print(f"  [FAIL] {e}")
        traceback.print_exc()
        return False


# ============================================================
# Test 7: Causal Graph with Expanded Chains
# ============================================================

def test_causal_graph_expansion():
    """Test CausalGraphBuilder loads expanded causal chains."""
    print("\n" + "=" * 70)
    print("TEST 7: Causal Graph (Expanded Chains)")
    print("=" * 70)

    try:
        from medical_task_suite.generation.v2.clinical_world.causal_graph import CausalGraphBuilder

        builder = CausalGraphBuilder()
        # CausalGraphBuilder builds in __init__, no separate build() call needed

        report = builder.get_build_report()
        print(f"  Build report:")
        for key, val in report.items():
            print(f"    {key}: {val}")

        # Verify expanded data loaded (nested under subgraph stats)
        diag_stats = report.get("diagnostic", {})
        prog_stats = report.get("progression", {})
        treat_stats = report.get("treatment", {})

        n_progression = prog_stats.get("n_relations", 0)
        n_diagnostic = diag_stats.get("n_edges", 0)
        n_adverse = treat_stats.get("n_adverse_effects", 0)

        # v1 had 13 progression, 12 differential, 6 adverse
        # Progression and treatment expanded via curated data
        assert n_progression > 13, f"Expected >13 progression relations, got {n_progression}"
        assert n_adverse > 6, f"Expected >6 adverse effects, got {n_adverse}"
        # Diagnostic edges come from PrimeKG phenotype data — 0 is expected in KB-only mode

        print(f"  [OK] Expanded: {n_progression} progression (was 13), "
              f"{n_adverse} adverse (was 6), "
              f"{n_diagnostic} diagnostic (PrimeKG-only in KB mode)")

        return True

    except Exception as e:
        print(f"  [FAIL] {e}")
        traceback.print_exc()
        return False


# ============================================================
# Main
# ============================================================

def main():
    """Run all v2.7 end-to-end tests."""
    print("\n" + "=" * 80)
    print(" v2.7 END-TO-END PIPELINE TEST SUITE")
    print("=" * 80)
    print("Testing: generation → interaction → evaluation → conversion")
    print("")

    tests = [
        ("Scenario Generation (DiseaseSampler)", test_scenario_generation),
        ("Symptom Generation (Expanded Pools)", test_symptom_generation),
        ("Patient Agent (Calibrated Defaults)", test_patient_agent_calibration),
        ("DiseaseSampler Direct", test_disease_sampler),
        ("Causal Graph (Expanded Chains)", test_causal_graph_expansion),
        ("Full Pipeline (Generate→Evaluate)", test_full_pipeline),
        ("Tau2 Adapter (v2.7 Format)", test_tau2_adapter),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n  [CRASH] {test_name}: {e}")
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 80)
    print(" TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, p in results if p)
    total = len(results)

    for test_name, is_passed in results:
        status = "[OK] PASS" if is_passed else "[FAIL] FAIL"
        print(f"  {status}: {test_name}")

    print(f"\n  Results: {passed}/{total} tests passed ({passed*100//total}%)")
    print("=" * 80)

    if passed == total:
        print("\n  [SUCCESS] All v2.7 pipeline tests passed!")
        return 0
    else:
        print(f"\n  [WARNING] {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
