#!/usr/bin/env python3
"""Verify the three temporal decision environment criteria."""
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
    # CHECK_INTERACTION required when comorbidities exist
    if task["clinical"].get("comorbidities"):
        traj.append({"t": t, "action": actions["CHECK_INTERACTION"]["id"],
                      "observation": {"interactions": "none"}, "reward": None, "done": False}); t += 1
    traj.append({"t": t, "action": actions["PRESCRIBE"]["id"],
                  "observation": {"drug": drug}, "reward": None, "done": False}); t += 1
    traj.append({"t": t, "action": actions["EDUCATE"]["id"],
                  "observation": {"agent_message": "You have %s." % diagnosis}, "reward": None, "done": False}); t += 1
    traj.append({"t": t, "action": actions["END"]["id"],
                  "observation": {"done": True}, "reward": None, "done": True})
    return traj


# CRITERION 1: Delaying diagnosis must reduce score
r_fast = ev.evaluate(build_traj(path_a, "type 2 diabetes", extra_wasted=0))
r_slow = ev.evaluate(build_traj(path_a, "type 2 diabetes", extra_wasted=8))

print("=" * 60)
print("CRITERION 1: Delaying diagnosis reduces score")
print("=" * 60)
print("  Fast agent (optimal turns):  %.4f (%d turns)" % (r_fast["total"], r_fast["turns"]))
print("  Slow agent (8 wasted turns): %.4f (%d turns)" % (r_slow["total"], r_slow["turns"]))
print("  Gap: %+.4f" % (r_fast["total"] - r_slow["total"]))
c1 = r_fast["total"] > r_slow["total"]
print("  PASS: %s" % c1)

# CRITERION 2: Cannot recover from wrong early path
r_optimal = ev.evaluate(build_traj(path_a, "type 2 diabetes"))
r_wrong = ev.evaluate(build_traj(path_b + path_a, "type 2 diabetes"))

print()
print("=" * 60)
print("CRITERION 2: Cannot recover from wrong early path")
print("=" * 60)
print("  Path A symptoms: %s" % path_a)
print("  Path B symptoms: %s" % path_b)
print("  Optimal (path A only): %.4f" % r_optimal["total"])
print("  Wrong-recovery (B→A):  %.4f" % r_wrong["total"])
print("  Process optimal:  %.4f" % r_optimal["components"]["process"])
print("  Process recovery: %.4f" % r_wrong["components"]["process"])
c2 = r_wrong["total"] < r_optimal["total"] - 0.1
print("  PASS: %s (recovery score %.3f < optimal %.3f - 0.1)" % (
    c2, r_wrong["total"], r_optimal["total"]))

# CRITERION 3: Heuristic agent score (from discrimination eval)
print()
print("=" * 60)
print("CRITERION 3: Heuristic agent <= 0.75")
print("=" * 60)
print("  See discrimination_eval.py output above")

print()
print("=" * 60)
print("SUMMARY")
print("=" * 60)
all_pass = c1 and c2
print("  Delay reduces score:     %s" % ("PASS" if c1 else "FAIL"))
print("  Wrong path irrecoverable: %s" % ("PASS" if c2 else "FAIL"))
print("  Heuristic <= 0.75:        see discrimination_eval.py")
print()
if all_pass:
    print("TEMPORAL CRITERIA VERIFIED")
else:
    print("CRITERIA NOT MET")
sys.exit(0 if all_pass else 1)
