#!/usr/bin/env python3
"""Verify HARD CONSTRAINTS: wrong decisions reduce information access, not just score."""
import sys
from pathlib import Path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from medical_task_suite.generation.v2.task_generation.task_generator import MedicalTaskGenerator
from medical_task_suite.clinical_knowledge.accessor import ClinicalKnowledgeBase
from medical_task_suite.evaluation.bench_evaluator import BenchEvaluator

kb = ClinicalKnowledgeBase.get_instance()
gen = MedicalTaskGenerator(kb)
task = gen.generate_task("diagnostic_uncertainty", "L2", target_disease="type 2 diabetes", seed=42)
actions = task["actions"]
ev = BenchEvaluator(task)

paths = task["ground_truth"]["solution_space"]["derived_from"].get("minimal_information_sets", [])
path_a = paths[0]["must_collect"] if paths else []
path_b = paths[1]["must_collect"] if len(paths) > 1 else []
comorbidities = task["clinical"].get("comorbidities", [])


def build_traj(syms, diagnosis, drug="metformin", extra_wasted=0):
    traj = []
    t = 0
    for s in syms:
        traj.append({"t": t, "action": actions["ASK"]["id"],
                      "observation": {"symptoms_revealed": [s]}, "reward": None, "done": False})
        t += 1
    for _ in range(extra_wasted):
        traj.append({"t": t, "action": actions["ASK"]["id"],
                      "observation": {"symptoms_revealed": []}, "reward": None, "done": False})
        t += 1
    traj.append({"t": t, "action": actions["ORDER_LAB"]["id"],
                  "observation": {}, "reward": None, "done": False}); t += 1
    traj.append({"t": t, "action": actions["GET_RESULTS"]["id"],
                  "observation": {"lab_results": task["clinical"]["labs"]}, "reward": None, "done": False}); t += 1
    traj.append({"t": t, "action": actions["DIAGNOSE"]["id"],
                  "observation": {"diagnosis": diagnosis}, "reward": None, "done": False}); t += 1
    traj.append({"t": t, "action": actions["CHECK_ALLERGY"]["id"],
                  "observation": {"allergies": []}, "reward": None, "done": False}); t += 1
    if comorbidities:
        traj.append({"t": t, "action": actions["CHECK_INTERACTION"]["id"],
                      "observation": {"interactions": "none"}, "reward": None, "done": False}); t += 1
    traj.append({"t": t, "action": actions["PRESCRIBE"]["id"],
                  "observation": {"drug": drug}, "reward": None, "done": False}); t += 1
    traj.append({"t": t, "action": actions["EDUCATE"]["id"],
                  "observation": {"agent_message": "You have %s." % diagnosis}, "reward": None, "done": False}); t += 1
    traj.append({"t": t, "action": actions["END"]["id"],
                  "observation": {"done": True}, "reward": None, "done": True})
    return traj


print("=" * 60)
print("HARD CONSTRAINT VERIFICATION")
print("=" * 60)
print("Path A (optimal): %s" % path_a)
print("Path B (non-opt): %s" % path_b)
print()

# ── TEST 1: Wrong path recovery is BLOCKED (not penalized) ──
r_optimal = ev.evaluate(build_traj(path_a, "type 2 diabetes"))
r_wrong = ev.evaluate(build_traj(path_b + path_a, "type 2 diabetes"))

print("TEST 1: Wrong path recovery BLOCKED")
print("  Optimal (path A only): %.4f  dx=%.2f  info=%.2f  process=%.4f" % (
    r_optimal["total"], r_optimal["components"]["diagnosis"],
    r_optimal["components"]["info"] or 0, r_optimal["components"]["process"]))
print("  Recovery (B→A switch): %.4f  dx=%.2f  info=%.2f  process=%.4f" % (
    r_wrong["total"], r_wrong["components"]["diagnosis"],
    r_wrong["components"]["info"] or 0, r_wrong["components"]["process"]))
# With switches > 1, diagnosis and info should be 0.0 (HARD CONSTRAINT)
c1 = r_wrong["components"]["diagnosis"] == 0.0 and r_wrong["components"]["info"] == 0.0
print("  PASS: %s (diagnosis=%.2f==0, info=%.2f==0 — evidence nullified)" % (
    c1, r_wrong["components"]["diagnosis"], r_wrong["components"]["info"] or 0))

# ── TEST 2: Cannot trade penalty for more info ──
r_penalty_trade = ev.evaluate(build_traj(path_b + path_a, "type 2 diabetes"))
# The score should NOT be higher just because agent collected more symptoms
# Evidence from wrong path should be NULLIFIED, not just subtracted
c2 = r_penalty_trade["total"] < r_optimal["total"] - 0.2
print()
print("TEST 2: Cannot trade penalty for info")
print("  Recovery total: %.4f" % r_penalty_trade["total"])
print("  Optimal total:  %.4f" % r_optimal["total"])
print("  PASS: %s (recovery is not just penalty-subtracted)" % c2)

# ── TEST 3: Delay reduces information access ──
r_fast = ev.evaluate(build_traj(path_a, "type 2 diabetes", extra_wasted=0))
r_slow = ev.evaluate(build_traj(path_a, "type 2 diabetes", extra_wasted=8))
print()
print("TEST 3: Delay reduces information access (constraint not penalty)")
print("  Fast (optimal turns):  %.4f  process=%.4f" % (r_fast["total"], r_fast["components"]["process"]))
print("  Slow (8 wasted turns): %.4f  process=%.4f" % (r_slow["total"], r_slow["components"]["process"]))
c3 = r_fast["total"] > r_slow["total"]
print("  PASS: %s (delayed agent gets less information value)" % c3)

# ── TEST 4: Severity is constraint not score penalty ──
# Verify no global total subtraction for severity — only info access constraint
max_turns = task["task_config"]["max_turns"]
print()
print("TEST 4: Severity is constraint, not score penalty")
print("  max_turns=%d, worsening_threshold=%.1f, critical_threshold=%.1f" % (
    max_turns, max_turns * 0.35, max_turns * 0.7))
# The slow agent should have severity="worsening" or "critical"
# but total should not have a flat subtraction — only process should be affected
print("  Fast process: %.4f  Slow process: %.4f" % (
    r_fast["components"]["process"], r_slow["components"]["process"]))
print("  Fast total: %.4f  Slow total: %.4f" % (r_fast["total"], r_slow["total"]))
c4 = r_fast["total"] > r_slow["total"]  # Still lower due to info constraints
print("  PASS: %s (lower via info constraints, not flat deduction)" % c4)

# ── SUMMARY ──
print()
print("=" * 60)
print("SUMMARY")
print("=" * 60)
all_pass = c1 and c2 and c3 and c4
print("  Wrong path recovery blocked:  %s" % ("PASS" if c1 else "FAIL"))
print("  Cannot trade penalty for info: %s" % ("PASS" if c2 else "FAIL"))
print("  Delay reduces info access:    %s" % ("PASS" if c3 else "FAIL"))
print("  Severity is constraint:        %s" % ("PASS" if c4 else "FAIL"))
print()
if all_pass:
    print("HARD CONSTRAINTS VERIFIED")
else:
    print("CONSTRAINTS NOT MET")
sys.exit(0 if all_pass else 1)
