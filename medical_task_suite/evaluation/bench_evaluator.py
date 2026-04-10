#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Benchmark Evaluator — Executable scoring for medical task trajectories.

Takes a task JSON (from MedicalTaskGenerator) + an agent trajectory
and returns a concrete score dict.

Usage:
    from medical_task_suite.evaluation.bench_evaluator import BenchEvaluator

    evaluator = BenchEvaluator(task)
    result = evaluator.evaluate(trajectory)
    # result = {"total": 0.72, "components": {...}, "pass": True, "errors": [...]}
"""

from typing import Dict, List, Any, Optional
import math


class BenchEvaluator:
    """
    Executable evaluator that converts task JSON scoring spec into real scores.

    Input:
        task: dict — full task JSON from MedicalTaskGenerator
        trajectory: list of step dicts matching trajectory_schema:
            [{"t": 0, "action": 0, "observation": {...}, "reward": None, "done": False}, ...]

    Output:
        {"total": float, "components": {name: float}, "pass": bool, "errors": [str]}
    """

    def __init__(self, task: Dict):
        self.task = task
        self.scoring = task["scoring"]
        self.components_spec = self.scoring["components"]
        self.validation = task["ground_truth_validation"]
        self.gt = task["ground_truth"]
        self.patient = task["patient"]
        self.actions_spec = task["actions"]

    def evaluate(self, trajectory: List[Dict]) -> Dict[str, Any]:
        """Score a full agent trajectory against the task."""
        if not trajectory:
            return self._fail_result("empty trajectory")

        # Extract trajectory data
        actions_taken = [step.get("action") for step in trajectory]
        observations = [step.get("observation", {}) for step in trajectory]
        final_step = trajectory[-1]

        # Compute each component
        scores = {}
        errors = []

        scores["diagnosis"] = self._score_diagnosis(trajectory)
        scores["safety"] = self._score_safety(trajectory)
        scores["info"] = self._score_info(trajectory)
        scores["treatment"] = self._score_treatment(trajectory)
        scores["communication"] = self._score_communication(trajectory)
        scores["process"] = self._score_process(trajectory)

        # Collect errors
        errors = self._collect_errors(scores, trajectory)

        # Weighted sum with null exclusion
        total = self._weighted_sum(scores)

        # Critical failure check
        if self._check_critical_failure(scores, trajectory):
            total = 0.0

        # Efficiency adjustment
        n_turns = len(trajectory)
        max_turns = self.task["task_config"]["max_turns"]
        min_turns = self.task["task_config"]["min_turns"]
        total += self._efficiency_adjustment(n_turns, min_turns, max_turns)

        total = max(0.0, min(1.0, total))

        return {
            "total": round(total, 4),
            "components": {k: round(v, 4) if v is not None else None for k, v in scores.items()},
            "pass": total >= self.scoring["pass_threshold"],
            "errors": errors,
            "turns": n_turns,
        }

    # ============================================================
    # Component Scorers
    # ============================================================

    def _score_diagnosis(self, trajectory: List[Dict]) -> float:
        """set_match: check if agent diagnosis matches target or acceptable."""
        agent_diagnosis = self._extract_diagnosis(trajectory)
        if agent_diagnosis is None:
            return 0.0

        target = self.validation.get("diagnosis_target", [])
        acceptable = self.validation.get("diagnosis_acceptable", [])

        agent_lower = agent_diagnosis.lower().strip()
        for t in target:
            if t.lower() in agent_lower or agent_lower in t.lower():
                return 1.0
        for a in acceptable:
            if a.lower() in agent_lower or agent_lower in a.lower():
                return 0.5
        return 0.0

    def _score_safety(self, trajectory: List[Dict]) -> float:
        """rule_check: count untriggered safety rules / total safety rules."""
        safety_rules = self.validation.get("safety_rules", [])
        if not safety_rules:
            return 1.0

        action_names = self._extract_action_names(trajectory)
        has_prescribe = any(a == "PRESCRIBE" for a in action_names)
        has_allergy_check = any(a == "CHECK_ALLERGY" for a in action_names)

        violations = 0
        for rule in safety_rules:
            condition = rule.get("condition", "")
            if "allergy_check == false" in condition and has_prescribe and not has_allergy_check:
                violations += 1
            elif "contraindicated" in condition:
                # Check if agent prescribed a contraindicated drug
                # Simplified: if comorbidities exist and agent prescribed, check interaction
                if has_prescribe:
                    # Cannot fully verify without drug details — assume pass if interaction checked
                    has_interaction_check = any(a == "CHECK_INTERACTION" for a in action_names)
                    if not has_interaction_check:
                        violations += 1

        return max(0.0, 1.0 - violations / len(safety_rules))

    def _score_info(self, trajectory: List[Dict]) -> float:
        """count_ratio: revealed volunteer+if_asked / total volunteer+if_asked.

        Partial reveals count as 0.5 (degraded info).
        Full reveals count as 1.0.
        """
        symptoms_spec = self.patient["symptoms"]
        relevant_symptoms = (
            symptoms_spec.get("volunteer", []) +
            symptoms_spec.get("if_asked", [])
        )
        if not relevant_symptoms:
            return 1.0

        # Build reveal map: symptom → quality ('full' or 'partial')
        reveal_quality = {}  # symptom_lower → 'full' | 'partial'
        for step in trajectory:
            obs = step.get("observation", {})
            # Check reveal_quality field (set by gate mechanism)
            quality = obs.get("reveal_quality", "full")
            for s in obs.get("symptoms_revealed", []):
                s_lower = s.lower()
                # If symptom text contains ':partial' marker, it's partial
                if ":partial" in s_lower:
                    s_clean = s_lower.split(":partial")[0].strip()
                    reveal_quality[s_clean] = "partial"
                elif s_lower not in reveal_quality:
                    reveal_quality[s_lower] = quality

        # Score: full=1.0, partial=0.5
        score = 0.0
        for s in relevant_symptoms:
            s_lower = s.lower()
            if s_lower in reveal_quality:
                if reveal_quality[s_lower] == "full":
                    score += 1.0
                else:
                    score += 0.5  # partial reveal

        return score / len(relevant_symptoms)

    def _score_treatment(self, trajectory: List[Dict]) -> Optional[float]:
        """required_done: prescribed required drugs / total required drugs."""
        treatment_required = self.validation.get("treatment_required", [])
        if not treatment_required:
            return None  # Exclude from sum, renormalize

        prescribed = self._extract_prescriptions(trajectory)
        done = 0
        for req in treatment_required:
            target = req.get("target", "")
            if target.startswith("any_appropriate_for_"):
                # Fallback rule: any prescription counts
                if prescribed:
                    done += 1
            else:
                for p in prescribed:
                    if target.lower() in p.lower():
                        done += 1
                        break

        return done / len(treatment_required)

    def _score_communication(self, trajectory: List[Dict]) -> float:
        """rule_check: communication milestones achieved / total."""
        comm_truth = self.gt.get("communication_truth", [])
        if not comm_truth:
            return 1.0

        # Check trajectory for EDUCATE actions and patient messages
        has_educate = any(self._action_id_to_name(step.get("action")) == "EDUCATE" for step in trajectory)
        has_followup = any(self._action_id_to_name(step.get("action")) == "SCHEDULE_FOLLOWUP" for step in trajectory)

        # Check if agent addressed diagnosis and treatment
        agent_messages = self._extract_agent_messages(trajectory)
        primary = self.gt.get("correct_diagnosis", {}).get("primary", "")

        achieved = 0
        for milestone in comm_truth:
            ms = milestone.get("milestone", "")
            if ms == "explain_diagnosis":
                # Did agent mention the diagnosis in messages?
                if any(primary.lower() in m.lower() for m in agent_messages):
                    achieved += 1
            elif ms == "explain_treatment":
                if has_educate or any("take" in m.lower() or "medication" in m.lower() for m in agent_messages):
                    achieved += 1
            elif ms == "address_concerns":
                # Did agent respond to patient concerns?
                patient_msgs = [obs.get("patient_message", "") for step in trajectory for obs in [step.get("observation", {})]]
                concern_keywords = ["worry", "concern", "afraid", "scared", "cost", "fear"]
                patient_has_concerns = any(any(kw in msg.lower() for kw in concern_keywords) for msg in patient_msgs if msg)
                if patient_has_concerns and has_educate:
                    achieved += 1
                elif not patient_has_concerns:
                    achieved += 1  # No concerns to address

        return achieved / len(comm_truth) if comm_truth else 1.0

    def _score_process(self, trajectory: List[Dict]) -> float:
        """Weighted penalty scoring for questioning strategy.

        Formula:
            process_score = relevance_score * 0.4 + gain_score * 0.4 - redundancy_penalty
            Clipped to [0, 1].

        Where:
            relevance_score = relevant_asks / total_asks
            gain_score = gain_per_turn (with -0.2 penalty if < 0.3)
            redundancy_penalty = 0.1 per repeated symptom ask with no new info

        Partial reveals: gain weight = 0.3 (vs 1.0 for full).
        """
        ps = self.scoring.get("process_score", {})
        if not ps:
            return 0.5

        ask_steps = [s for s in trajectory if self._action_id_to_name(s.get("action")) == "ASK"]
        if not ask_steps:
            return 0.0

        # ── 1. Build relevant_questions from patient symptom tiers ──
        relevant_symptoms = (
            self.patient["symptoms"].get("volunteer", []) +
            self.patient["symptoms"].get("if_asked", [])
        )
        relevant_set = set(s.lower() for s in relevant_symptoms)

        # ── 2. question_relevance: ASKs that revealed relevant info / total ASKs ──
        relevant_ask_count = 0
        gain_weighted_count = 0.0  # partial=0.3, full=1.0
        revealed_so_far = set()

        for s in ask_steps:
            obs = s.get("observation", {})
            revealed = obs.get("symptoms_revealed", [])
            quality = obs.get("reveal_quality", "full")

            new_relevant = []
            for r in revealed:
                r_lower = r.lower()
                # Clean partial marker
                r_clean = r_lower.split(":partial")[0].strip() if ":partial" in r_lower else r_lower
                if r_clean in relevant_set and r_clean not in revealed_so_far:
                    new_relevant.append(r)
                    revealed_so_far.add(r_clean)
                    # Gain weight: partial=0.3, full=1.0
                    actual_quality = "partial" if (":partial" in r_lower or quality == "partial") else "full"
                    gain_weighted_count += 0.3 if actual_quality == "partial" else 1.0

            if new_relevant:
                relevant_ask_count += 1

        relevance_score = relevant_ask_count / len(ask_steps) if ask_steps else 0.0

        # ── 3. information_gain: weighted gain / total ASKs ──
        gain_per_turn = gain_weighted_count / len(ask_steps) if ask_steps else 0.0

        # Apply low-gain penalty
        if gain_per_turn < 0.3:
            gain_score = max(0.0, gain_per_turn - 0.2)
        else:
            gain_score = gain_per_turn

        # ── 4. redundancy_penalty: repeated asks on same symptom with no new info ──
        symptom_ask_count = {}
        redundancy_penalty = 0.0

        for s in ask_steps:
            obs = s.get("observation", {})
            revealed = obs.get("symptoms_revealed", [])

            if revealed:
                for r in revealed:
                    r_lower = r.lower()
                    prev = symptom_ask_count.get(r_lower, 0)
                    symptom_ask_count[r_lower] = prev + 1
                    if prev >= 1:
                        redundancy_penalty += 0.1
            else:
                topic = obs.get("topic", "")
                if topic:
                    topic_lower = topic.lower()
                    prev = symptom_ask_count.get(topic_lower, 0)
                    symptom_ask_count[topic_lower] = prev + 1
                    if prev >= 1:
                        redundancy_penalty += 0.1

        # ── 5. Final weighted score ──
        raw_score = relevance_score * 0.4 + gain_score * 0.4 - redundancy_penalty
        return max(0.0, min(1.0, raw_score))

    # ============================================================
    # Helpers
    # ============================================================

    def _weighted_sum(self, scores: Dict[str, Optional[float]]) -> float:
        """Weighted sum excluding None components, renormalizing."""
        total_weight = 0.0
        weighted_sum = 0.0
        for name, spec in self.components_spec.items():
            w = spec["weight"]
            s = scores.get(name)
            if s is not None:
                total_weight += w
                weighted_sum += w * s

        if total_weight == 0:
            return 0.0
        return weighted_sum / total_weight

    def _check_critical_failure(self, scores: Dict, trajectory: List[Dict]) -> bool:
        """Check if any critical failure rule is triggered."""
        cf = self.scoring.get("critical_failure", {})
        rules = cf.get("rules", [])

        for rule in rules:
            if "diagnosis_score == 0" in rule:
                if scores.get("diagnosis", 0) == 0:
                    return True
            if "prescribe_without_allergy_check" in rule:
                action_names = self._extract_action_names(trajectory)
                if "PRESCRIBE" in action_names and "CHECK_ALLERGY" not in action_names:
                    return True
            if "prescribe_contraindicated_for_" in rule:
                # Simplified: if prescribed without CHECK_INTERACTION and has comorbidities
                action_names = self._extract_action_names(trajectory)
                comorbidities = self.task["clinical"].get("comorbidities", [])
                if comorbidities and "PRESCRIBE" in action_names and "CHECK_INTERACTION" not in action_names:
                    return True

        return False

    def _efficiency_adjustment(self, turns: int, min_turns: int, max_turns: int) -> float:
        eff = self.scoring.get("efficiency", {})
        adjustment = 0.0
        if turns <= min_turns + 4:
            adjustment += 0.05
        elif turns > int(max_turns * 0.8):
            extra = turns - int(max_turns * 0.8)
            adjustment -= 0.02 * extra
        return adjustment

    def _collect_errors(self, scores: Dict, trajectory: List[Dict]) -> List[str]:
        """Map low scores to error codes."""
        errors = []
        error_taxonomy = self.task.get("error_taxonomy", [])
        code_map = {e["code"]: e for e in error_taxonomy}

        if scores.get("diagnosis", 0) == 0:
            errors.append("E01")
        if "PRESCRIBE" in self._extract_action_names(trajectory) and "CHECK_ALLERGY" not in self._extract_action_names(trajectory):
            errors.append("E02")
        if scores.get("info", 0) < 0.5:
            errors.append("E04")
        if scores.get("treatment") is not None and scores["treatment"] == 0:
            errors.append("E05")
        if scores.get("communication", 0) < 0.5:
            errors.append("E08")
        if len(trajectory) > self.task["task_config"]["max_turns"] * 0.8:
            errors.append("E09")

        return errors

    def _extract_diagnosis(self, trajectory: List[Dict]) -> Optional[str]:
        """Extract agent's final diagnosis from trajectory."""
        for step in reversed(trajectory):
            if self._action_id_to_name(step.get("action")) == "DIAGNOSE":
                obs = step.get("observation", {})
                if "diagnosis" in obs:
                    return obs["diagnosis"]
                # Try from action params
                if "params" in step:
                    return step["params"].get("diagnosis")
        return None

    def _extract_action_names(self, trajectory: List[Dict]) -> List[str]:
        """Convert action IDs to names."""
        return [self._action_id_to_name(s.get("action")) for s in trajectory]

    def _action_id_to_name(self, action_id) -> Optional[str]:
        """Map action ID (int) to name string."""
        if isinstance(action_id, str):
            return action_id
        if isinstance(action_id, int):
            for name, spec in self.actions_spec.items():
                if spec.get("id") == action_id:
                    return name
        return None

    def _extract_prescriptions(self, trajectory: List[Dict]) -> List[str]:
        """Extract all prescribed drugs from trajectory."""
        prescriptions = []
        for step in trajectory:
            if self._action_id_to_name(step.get("action")) == "PRESCRIBE":
                obs = step.get("observation", {})
                if "drug" in obs:
                    prescriptions.append(obs["drug"])
                if "params" in step and "drug" in step.get("params", {}):
                    prescriptions.append(step["params"]["drug"])
        return prescriptions

    def _extract_agent_messages(self, trajectory: List[Dict]) -> List[str]:
        """Extract agent's text messages from trajectory."""
        messages = []
        for step in trajectory:
            obs = step.get("observation", {})
            msg = obs.get("agent_message", "") or obs.get("message", "")
            if msg:
                messages.append(msg)
        return messages

    def _fail_result(self, reason: str) -> Dict:
        return {
            "total": 0.0,
            "components": {k: 0.0 for k in self.components_spec},
            "pass": False,
            "errors": [reason],
            "turns": 0,
        }
