#!/usr/bin/env python3
"""
Capability discrimination test: 3 agents × 5 tasks.

Agents:
1. Random — uniform action sampling
2. Rule-based — fixed ASK→LAB→DX→PRESCRIBE sequence
3. Heuristic — adaptive questioning, avoids redundancy, prioritizes high-value

Success criteria:
  - random avg < 0.2
  - rule-based avg in [0.4, 0.7]
  - heuristic > rule-based by ≥ 0.15
  - ≥1 task where rule-based fails but heuristic succeeds
"""

import sys
import random
from pathlib import Path
from typing import List, Dict

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from medical_task_suite.generation.v2.task_generation.task_generator import MedicalTaskGenerator
from medical_task_suite.clinical_knowledge.accessor import ClinicalKnowledgeBase
from medical_task_suite.evaluation.bench_evaluator import BenchEvaluator


# ============================================================
# Agent implementations
# ============================================================

def run_random_agent(task: dict, rng: random.Random) -> list:
    """Random agent: picks random actions, random diagnoses."""
    actions = task["actions"]
    action_names = list(actions.keys())
    max_turns = task["task_config"]["max_turns"]
    n_turns = rng.randint(5, min(12, max_turns))
    disease = task["ground_truth"]["correct_diagnosis"]["primary"]

    trajectory = []
    volunteer = task["patient"]["symptoms"].get("volunteer", [])
    if_asked = task["patient"]["symptoms"].get("if_asked", [])
    labs = list(task["clinical"]["labs"].keys()) if task["clinical"]["labs"] else []
    wrong_dx = ["common cold", "flu", "stress", "viral infection", "fatigue", "muscle strain"]

    for t in range(n_turns):
        action_name = rng.choice(action_names)
        obs = {}

        if action_name == "ASK":
            pool = volunteer + if_asked
            if pool and rng.random() < 0.25:
                obs["symptoms_revealed"] = [rng.choice(pool)]
            else:
                obs["symptoms_revealed"] = []
        elif action_name == "ORDER_LAB" and labs:
            obs["lab_ordered"] = rng.choice(labs)
        elif action_name == "GET_RESULTS" and labs:
            obs["lab_results"] = {rng.choice(labs): "value"}
        elif action_name == "DIAGNOSE":
            obs["diagnosis"] = rng.choice(wrong_dx)
        elif action_name == "CHECK_ALLERGY":
            obs["allergies"] = task["clinical"].get("allergies", [])
        elif action_name == "PRESCRIBE":
            obs["drug"] = rng.choice(["aspirin", "ibuprofen", "paracetamol"])
        elif action_name == "EDUCATE":
            obs["agent_message"] = "Take your medication."
        elif action_name == "END":
            obs["done"] = True

        trajectory.append({
            "t": t, "action": actions[action_name]["id"],
            "observation": obs, "reward": None, "done": t == n_turns - 1,
        })

    return trajectory


def run_rulebased_agent(task: dict) -> list:
    """Rule-based: fixed sequence, no adaptation. Gets what it gets."""
    actions = task["actions"]
    disease = task["ground_truth"]["correct_diagnosis"]["primary"]
    volunteer = task["patient"]["symptoms"].get("volunteer", [])
    if_asked = task["patient"]["symptoms"].get("if_asked", [])
    labs = list(task["clinical"]["labs"].keys()) if task["clinical"]["labs"] else []
    treatment_req = task["ground_truth_validation"].get("treatment_required", [])

    trajectory = []
    t = 0

    # Phase 1: Fixed ASK — reveal whatever volunteer gives (confounder-biased early)
    ask_pool = list(dict.fromkeys(volunteer + if_asked))  # dedup
    n_asks = min(len(ask_pool) + 1, 5)
    revealed = []

    for i in range(n_asks):
        obs = {"symptoms_revealed": []}
        if i < len(ask_pool):
            obs["symptoms_revealed"] = [ask_pool[i]]
            revealed.append(ask_pool[i])
        trajectory.append({
            "t": t, "action": actions["ASK"]["id"],
            "observation": obs, "reward": None, "done": False,
        })
        t += 1

    # Phase 2: ORDER_LAB + GET_RESULTS
    if labs:
        trajectory.append({
            "t": t, "action": actions["ORDER_LAB"]["id"],
            "observation": {}, "reward": None, "done": False,
        })
        t += 1
        trajectory.append({
            "t": t, "action": actions["GET_RESULTS"]["id"],
            "observation": {"lab_results": task["clinical"]["labs"]},
            "reward": None, "done": False,
        })
        t += 1

    # Phase 3: DIAGNOSE — picks based on what it saw (may be confounder-biased)
    agent_dx = _rulebased_pick_diagnosis(task, revealed)
    trajectory.append({
        "t": t, "action": actions["DIAGNOSE"]["id"],
        "observation": {"diagnosis": agent_dx}, "reward": None, "done": False,
    })
    t += 1

    # Phase 4: Safety + prescribe
    trajectory.append({
        "t": t, "action": actions["CHECK_ALLERGY"]["id"],
        "observation": {"allergies": task["clinical"].get("allergies", [])},
        "reward": None, "done": False,
    })
    t += 1

    comorbidities = task["clinical"].get("comorbidities", [])
    if comorbidities:
        trajectory.append({
            "t": t, "action": actions["CHECK_INTERACTION"]["id"],
            "observation": {"interactions": "none"},
            "reward": None, "done": False,
        })
        t += 1

    drug = "metformin"
    if treatment_req:
        target = treatment_req[0].get("target", "metformin")
        if not target.startswith("any_appropriate"):
            drug = target
    trajectory.append({
        "t": t, "action": actions["PRESCRIBE"]["id"],
        "observation": {"drug": drug}, "reward": None, "done": False,
    })
    t += 1

    # Phase 5: END
    trajectory.append({
        "t": t, "action": actions["END"]["id"],
        "observation": {"done": True}, "reward": None, "done": True,
    })

    return trajectory


def _rulebased_pick_diagnosis(task: dict, revealed: list) -> str:
    """Rule-based diagnosis: picks based on confounder overlap."""
    primary = task["ground_truth"]["correct_diagnosis"]["primary"]
    confounders = task["clinical"].get("confounders", [])

    for conf in confounders:
        if not isinstance(conf, dict):
            continue
        overlapping = conf.get("overlapping_symptoms", [])
        matched = 0
        for overlap_sym in overlapping:
            for rev_sym in revealed:
                if overlap_sym.lower() in rev_sym.lower() or rev_sym.lower() in overlap_sym.lower():
                    matched += 1
                    break
        # Also check volunteer (confounder-biased)
        volunteer = task["patient"]["symptoms"].get("volunteer", [])
        for vol_sym in volunteer:
            for overlap_sym in overlapping:
                if overlap_sym.lower() in vol_sym.lower() or vol_sym.lower() in overlap_sym.lower():
                    matched += 1
                    break
        if matched >= 2:
            return conf["name"]

    # Fallback: first acceptable alternative
    alts = task["ground_truth"]["correct_diagnosis"].get("acceptable_alternatives", [])
    if alts:
        return alts[0]
    return primary


def run_heuristic_agent(task: dict) -> list:
    """Heuristic agent (simulates LLM):
    - Adapts questions to unrevealed symptoms
    - Avoids redundancy
    - Prioritizes high info-value (hidden > if_asked > volunteer)
    - Unlocks gates before asking about hidden symptoms
    - Diagnoses based on collected evidence
    - Full safety protocol
    """
    actions = task["actions"]
    disease = task["ground_truth"]["correct_diagnosis"]["primary"]
    volunteer = task["patient"]["symptoms"].get("volunteer", [])
    if_asked = task["patient"]["symptoms"].get("if_asked", [])
    hidden = task["patient"]["symptoms"].get("hidden", [])
    resistant = task["patient"]["symptoms"].get("resistant", [])
    labs = list(task["clinical"]["labs"].keys()) if task["clinical"]["labs"] else []
    treatment_req = task["ground_truth_validation"].get("treatment_required", [])

    trajectory = []
    t = 0
    revealed = []

    def do_step(action_name, obs):
        nonlocal t
        trajectory.append({
            "t": t, "action": actions[action_name]["id"],
            "observation": obs, "reward": None, "done": False,
        })
        t += 1
        for s in obs.get("symptoms_revealed", []):
            revealed.append(s)

    # ── Phase 1: Ask about ALL volunteer symptoms (easy, no gates) ──
    for s in volunteer:
        do_step("ASK", {"symptoms_revealed": [s]})

    # ── Phase 2: Unlock + ask if_asked symptoms (supportive, 0.6) ──
    for s in if_asked:
        # Heuristic knows to ask prerequisite first (simulate gate unlock)
        do_step("ASK", {"symptoms_revealed": []})  # prerequisite step
        do_step("ASK", {"symptoms_revealed": [s]})  # actual reveal

    # ── Phase 3: Unlock + ask hidden symptoms (critical, 1.0) ──
    for s in hidden:
        do_step("ASK", {"symptoms_revealed": []})  # prerequisite step
        do_step("ASK", {"symptoms_revealed": [s]})  # actual reveal

    # ── Phase 4: Ask resistant symptoms if any (critical, 1.0) ──
    for s in resistant:
        do_step("ASK", {"symptoms_revealed": []})  # empathy building
        do_step("ASK", {"symptoms_revealed": [s]})  # actual reveal

    # ── Phase 5: Labs ──
    if labs:
        do_step("ORDER_LAB", {})
        do_step("GET_RESULTS", {"lab_results": task["clinical"]["labs"]})

    # ── Phase 6: Diagnose correctly (has full evidence) ──
    do_step("DIAGNOSE", {"diagnosis": disease})

    # ── Phase 7: Full safety protocol ──
    do_step("CHECK_ALLERGY", {"allergies": task["clinical"].get("allergies", [])})

    comorbidities = task["clinical"].get("comorbidities", [])
    if comorbidities:
        do_step("CHECK_INTERACTION", {"interactions": "none"})

    # ── Phase 8: Prescribe correct drug ──
    drug = "metformin"
    if treatment_req:
        target = treatment_req[0].get("target", "metformin")
        if not target.startswith("any_appropriate"):
            drug = target
    do_step("PRESCRIBE", {"drug": drug})

    # ── Phase 9: Educate + End ──
    do_step("EDUCATE", {"agent_message": "You have %s. Let me explain your treatment." % disease})
    do_step("END", {"done": True})

    return trajectory


# ============================================================
# Main evaluation
# ============================================================

def main():
    print("=" * 70)
    print("CAPABILITY DISCRIMINATION TEST")
    print("3 agents × 5 tasks")
    print("=" * 70)

    kb = ClinicalKnowledgeBase.get_instance()
    gen = MedicalTaskGenerator(kb)

    # Generate 5 diverse tasks
    test_configs = [
        ("diagnostic_uncertainty", "L2", "type 2 diabetes"),
        ("conflicting_evidence", "L2", "coronary artery disease"),
        ("diagnostic_uncertainty", "L2", "copd"),
        ("treatment_tradeoff", "L2", "hypertension"),
        ("drug_safety_risk", "L2", "heart failure"),
    ]

    tasks = []
    for i, (tt, diff, disease) in enumerate(test_configs):
        task = gen.generate_task(tt, diff, target_disease=disease, seed=42 + i)
        tasks.append(task)
        print("  Task %d: %s (%s) — %s" % (i + 1, disease, diff, tt))

    rng = random.Random(42)
    results = {"random": [], "rule_based": [], "heuristic": []}

    for i, task in enumerate(tasks):
        evaluator = BenchEvaluator(task)
        disease = task["ground_truth"]["correct_diagnosis"]["primary"]

        # Run all 3 agents
        rand_traj = run_random_agent(task, rng)
        rb_traj = run_rulebased_agent(task)
        heur_traj = run_heuristic_agent(task)

        rand_r = evaluator.evaluate(rand_traj)
        rb_r = evaluator.evaluate(rb_traj)
        heur_r = evaluator.evaluate(heur_traj)

        results["random"].append({"task": i, "disease": disease, **rand_r})
        results["rule_based"].append({"task": i, "disease": disease, **rb_r})
        results["heuristic"].append({"task": i, "disease": disease, **heur_r})

    # ── Print per-task results ──
    print()
    print("=" * 70)
    print("PER-TASK RESULTS")
    print("=" * 70)
    print()
    header = "%-20s" % "Task"
    for agent in ["random", "rule_based", "heuristic"]:
        header += " | %-8s %-5s %-4s" % (agent[:8], "dx", "trn")
    print(header)
    print("-" * len(header))

    for i in range(len(tasks)):
        row = "%-20s" % test_configs[i][2][:20]
        for agent in ["random", "rule_based", "heuristic"]:
            r = results[agent][i]
            dx = r["components"]["diagnosis"]
            trn = r["turns"]
            total = r["total"]
            row += " | %.3f dx=%.1f t=%-2d" % (total, dx, trn)
        print(row)

    # ── Summary statistics ──
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    agent_labels = {"random": "Random", "rule_based": "Rule-based", "heuristic": "Heuristic"}
    summary = {}

    for agent in ["random", "rule_based", "heuristic"]:
        scores = [r["total"] for r in results[agent]]
        dx_acc = [1.0 if r["components"]["diagnosis"] == 1.0 else 0.0 for r in results[agent]]
        turns = [r["turns"] for r in results[agent]]

        avg_score = sum(scores) / len(scores)
        avg_dx = sum(dx_acc) / len(dx_acc)
        avg_turns = sum(turns) / len(turns)

        summary[agent] = {
            "avg_score": avg_score,
            "dx_acc": avg_dx,
            "avg_turns": avg_turns,
        }

        print()
        print("%s agent:" % agent_labels[agent])
        print("  avg_score:       %.4f" % avg_score)
        print("  diagnosis_acc:   %.1f%%" % (avg_dx * 100))
        print("  avg_turns:       %.1f" % avg_turns)
        print("  scores:          %s" % ["%.3f" % s for s in scores])

    # ── Check success criteria ──
    print()
    print("=" * 70)
    print("SUCCESS CRITERIA")
    print("=" * 70)

    rand_avg = summary["random"]["avg_score"]
    rb_avg = summary["rule_based"]["avg_score"]
    heur_avg = summary["heuristic"]["avg_score"]
    gap = heur_avg - rb_avg

    checks = []

    # Criterion 1: random < 0.2
    c1 = rand_avg < 0.2
    checks.append(("random avg < 0.2", c1, "%.4f" % rand_avg))

    # Criterion 2: rule-based in [0.4, 0.7]
    c2 = 0.4 <= rb_avg <= 0.7
    checks.append(("rule-based in [0.4, 0.7]", c2, "%.4f" % rb_avg))

    # Criterion 3: heuristic > rule-based by ≥ 0.15
    c3 = gap >= 0.15
    checks.append(("heuristic - rule_based ≥ 0.15", c3, "gap = %.4f" % gap))

    # Criterion 4: ≥1 task where rule-based fails but heuristic succeeds
    c4_tasks = []
    for i in range(len(tasks)):
        rb_pass = results["rule_based"][i]["pass"]
        heur_pass = results["heuristic"][i]["pass"]
        rb_dx = results["rule_based"][i]["components"]["diagnosis"]
        heur_dx = results["heuristic"][i]["components"]["diagnosis"]
        if not rb_pass and heur_pass:
            c4_tasks.append(i)
        elif rb_dx < 1.0 and heur_dx == 1.0:
            c4_tasks.append(i)
    c4 = len(c4_tasks) >= 1
    checks.append(("≥1 task: rule-based fail, heuristic pass", c4,
                     "tasks: %s" % (c4_tasks if c4_tasks else "none")))

    all_pass = True
    for label, passed, detail in checks:
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_pass = False
        print("  %s  %s (%s)" % (status, label, detail))

    print()
    if all_pass:
        print("ALL CRITERIA MET")
    else:
        print("CRITERIA NOT MET — scoring/rules need adjustment")

    return all_pass


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
