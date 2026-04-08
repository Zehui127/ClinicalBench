#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Noise Calibration — Data-derived noise parameters for symptom generation.

Analyzes real dialogue data (Chinese MedDialog, HealthCareMagic) to measure:
- How many symptoms patients volunteer
- How often noise/misleading symptoms appear
- How symptom revelation varies by complexity

These measurements replace hand-coded fractions in UncertaintyConfig.
"""

import json
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from collections import Counter


# Symptom-counting patterns for Chinese and English
CHINESE_SYMPTOM_PATTERNS = [
    r"头疼|头痛|头晕|恶心|呕吐|发烧|发热|咳嗽|胸闷|心慌",
    r"乏力|疲劳|失眠|腹痛|腹泻|便秘|腰痛|关节痛|腿肿",
    r"气短|呼吸困难|视物模糊|耳鸣|鼻塞|流涕|嗓子疼",
    r"麻木|抽搐|皮疹|瘙痒|出血|紫癜|水肿|黄疸",
]

ENGLISH_SYMPTOM_PATTERNS = [
    r"\bheadache\b", r"\bdizziness\b", r"\bnausea\b", r"\bvomiting\b",
    r"\bfever\b", r"\bcough\b", r"\bchest pain\b", r"\bfatigue\b",
    r"\bshortness of breath\b", r"\babdominal pain\b", r"\bback pain\b",
    r"\bjoint pain\b", r"\bswelling\b", r"\bnumbness\b", r"\brash\b",
    r"\bblurry vision\b", r"\bpalpitation\b", r"\binsomnia\b",
    r"\bweight loss\b", r"\bweight gain\b", r"\bappetite\b",
]

# Irrelevant/noise symptom indicators
NOISE_INDICATORS_CN = [
    "偶尔", "轻微", "有时", "一点点", "说不清",
]
NOISE_INDICATORS_EN = [
    "occasionally", "mild", "sometimes", "slight", "minor",
]


@dataclass
class NoiseCalibrationData:
    """Statistical noise parameters derived from real dialogues."""
    # Averaged from data
    avg_volunteered_symptoms: float = 2.3
    avg_total_symptoms_per_dialogue: float = 4.1
    avg_dialogue_turns: float = 6.2

    # Noise rates (measured from data)
    noise_symptom_rate: float = 0.08      # Fraction of symptoms that are unrelated
    misleading_symptom_rate: float = 0.05  # Fraction that point to wrong diagnosis
    missing_info_rate: float = 0.30        # Fraction of info not initially provided

    # Per-difficulty adjustments (multipliers)
    difficulty_noise_multiplier: Dict[str, float] = field(default_factory=lambda: {
        "L1": 0.5, "L2": 1.0, "L3": 1.5,
    })
    difficulty_missing_multiplier: Dict[str, float] = field(default_factory=lambda: {
        "L1": 0.6, "L2": 1.0, "L3": 1.4,
    })
    difficulty_misleading_multiplier: Dict[str, float] = field(default_factory=lambda: {
        "L1": 0.0, "L2": 1.0, "L3": 2.0,
    })

    # Symptom revelation curve (cumulative fraction by turn)
    # [turn1, turn2, turn3, ...] — how much info is revealed by each turn
    revelation_curve: List[float] = field(default_factory=lambda: [
        0.35, 0.55, 0.70, 0.80, 0.88, 0.93, 0.96, 0.98, 1.0
    ])

    # Source metadata
    n_dialogues_analyzed: int = 0
    data_source: str = ""

    def to_dict(self) -> Dict:
        return {
            "avg_volunteered_symptoms": self.avg_volunteered_symptoms,
            "avg_total_symptoms": self.avg_total_symptoms_per_dialogue,
            "noise_rate": self.noise_symptom_rate,
            "misleading_rate": self.misleading_symptom_rate,
            "missing_rate": self.missing_info_rate,
            "n_analyzed": self.n_dialogues_analyzed,
            "source": self.data_source,
        }


# Default calibration data (conservative estimates, no data file needed)
DEFAULT_CALIBRATION = NoiseCalibrationData(
    avg_volunteered_symptoms=2.3,
    avg_total_symptoms_per_dialogue=4.1,
    avg_dialogue_turns=6.2,
    noise_symptom_rate=0.08,
    misleading_symptom_rate=0.05,
    missing_info_rate=0.30,
    difficulty_noise_multiplier={"L1": 0.5, "L2": 1.0, "L3": 1.5},
    difficulty_missing_multiplier={"L1": 0.6, "L2": 1.0, "L3": 1.4},
    difficulty_misleading_multiplier={"L1": 0.0, "L2": 1.0, "L3": 2.0},
    revelation_curve=[0.35, 0.55, 0.70, 0.80, 0.88, 0.93, 0.96, 0.98, 1.0],
)


class NoiseCalibration:
    """
    Calibrate symptom noise model from real dialogue data.

    Usage:
        cal = NoiseCalibration("data/processed/medical_dialogues/chinese_meddialog/tasks.json")
        data = cal.analyze()
        config = cal.get_calibrated_config("L2", "diagnostic_uncertainty")
    """

    def __init__(self, dialogue_data_path: Optional[str] = None):
        self.data_path = dialogue_data_path
        self._data: Optional[NoiseCalibrationData] = None

    def load_data(self, path: Optional[str] = None) -> List[Dict]:
        """Load dialogue data from JSON file."""
        path = path or self.data_path
        if not path:
            return []

        filepath = Path(path)
        if not filepath.exists():
            return []

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # Might be wrapped in a key
            for key in ["tasks", "dialogues", "data", "entries"]:
                if key in data:
                    return data[key]
            return [data]

        return []

    def analyze_dialogues(self, entries: List[Dict]) -> NoiseCalibrationData:
        """
        Measure noise parameters from real dialogue data.

        Works with both Chinese MedDialog and English HealthCareMagic formats.
        """
        if not entries:
            return DEFAULT_CALIBRATION

        volunteered_counts = []
        total_symptom_counts = []
        dialogue_lengths = []
        noise_counts = []

        for entry in entries:
            # Extract chief complaint / opening statement
            complaint = self._extract_complaint(entry)
            if not complaint:
                continue

            # Count symptoms in complaint
            n_symptoms = self._count_symptoms(complaint)
            volunteered_counts.append(min(n_symptoms, 10))

            # Estimate total symptoms from full dialogue
            full_text = self._extract_full_text(entry)
            total_symptoms = self._count_symptoms(full_text)
            total_symptom_counts.append(min(total_symptoms, 15))

            # Estimate dialogue length
            turns = self._estimate_turns(entry)
            if turns > 0:
                dialogue_lengths.append(turns)

            # Detect noise symptoms
            noise_symptoms = self._count_noise_indicators(full_text)
            noise_counts.append(noise_symptoms)

        if not volunteered_counts:
            return DEFAULT_CALIBRATION

        avg_volunteered = sum(volunteered_counts) / len(volunteered_counts)
        avg_total = sum(total_symptom_counts) / len(total_symptom_counts) if total_symptom_counts else avg_volunteered * 2
        avg_turns = sum(dialogue_lengths) / len(dialogue_lengths) if dialogue_lengths else 6.0

        # Compute rates
        noise_rate = 0.0
        if total_symptom_counts:
            avg_noise = sum(noise_counts) / len(noise_counts) if noise_counts else 0
            noise_rate = min(0.3, avg_noise / max(1, avg_total))

        missing_rate = 0.0
        if avg_total > avg_volunteered:
            missing_rate = (avg_total - avg_volunteered) / avg_total

        misleading_rate = min(0.15, noise_rate * 0.5)

        self._data = NoiseCalibrationData(
            avg_volunteered_symptoms=round(avg_volunteered, 2),
            avg_total_symptoms_per_dialogue=round(avg_total, 2),
            avg_dialogue_turns=round(avg_turns, 1),
            noise_symptom_rate=round(noise_rate, 3),
            misleading_symptom_rate=round(misleading_rate, 3),
            missing_info_rate=round(missing_rate, 3),
            n_dialogues_analyzed=len(volunteered_counts),
            data_source=str(self.data_path or "unknown"),
        )

        return self._data

    def analyze(self) -> NoiseCalibrationData:
        """Load and analyze data from configured path."""
        entries = self.load_data()
        if entries:
            return self.analyze_dialogues(entries)
        return DEFAULT_CALIBRATION

    def get_calibrated_config(self, difficulty: str, task_type: str = "") -> Dict:
        """
        Get calibrated uncertainty parameters for a difficulty + task type.

        Returns dict with: noise_fraction, misleading_fraction, missing_fraction
        """
        data = self._data or DEFAULT_CALIBRATION

        noise = data.noise_symptom_rate * data.difficulty_noise_multiplier.get(difficulty, 1.0)
        misleading = data.misleading_symptom_rate * data.difficulty_misleading_multiplier.get(difficulty, 1.0)
        missing = data.missing_info_rate * data.difficulty_missing_multiplier.get(difficulty, 1.0)

        # Task-type overrides
        if task_type == "diagnostic_uncertainty":
            missing = min(0.7, missing * 1.3)
        elif task_type == "conflicting_evidence":
            misleading = min(0.3, misleading * 1.5)
        elif task_type == "patient_non_compliance":
            missing = min(0.7, missing * 1.2)

        return {
            "noise_fraction": round(min(0.4, noise), 3),
            "misleading_fraction": round(min(0.3, misleading), 3),
            "missing_fraction": round(min(0.7, missing), 3),
        }

    def get_default_data(cls) -> NoiseCalibrationData:
        """Get default calibration data without loading files."""
        return DEFAULT_CALIBRATION

    # ================================================================
    # Text extraction helpers
    # ================================================================

    def _extract_complaint(self, entry: Dict) -> str:
        """Extract chief complaint from a dialogue entry."""
        # Chinese MedDialog format
        for key in ["chief_complaint", "title", "question", "user_scenario"]:
            if entry.get(key):
                return str(entry[key])
        return ""

    def _extract_full_text(self, entry: Dict) -> str:
        """Extract full dialogue text."""
        parts = []
        for key in ["question", "answer", "title", "ticket", "user_scenario"]:
            val = entry.get(key)
            if val:
                if isinstance(val, str):
                    parts.append(val)
                elif isinstance(val, dict):
                    parts.append(json.dumps(val, ensure_ascii=False))
        return " ".join(parts)

    def _count_symptoms(self, text: str) -> int:
        """Count symptom mentions in text."""
        count = 0
        text_lower = text.lower()

        for pattern in CHINESE_SYMPTOM_PATTERNS:
            count += len(re.findall(pattern, text))
        for pattern in ENGLISH_SYMPTOM_PATTERNS:
            count += len(re.findall(pattern, text_lower))

        # Also count comma-separated items (common in complaints)
        if count == 0 and text:
            # Rough estimate: items separated by commas/conjunctions
            separators = len(re.findall(r"[,、，和与及伴pluswith]", text))
            count = max(1, separators // 2)

        return count

    def _estimate_turns(self, entry: Dict) -> int:
        """Estimate number of dialogue turns."""
        # Check for explicit turn data
        if "turns" in entry:
            turns = entry["turns"]
            if isinstance(turns, list):
                return len(turns)
            if isinstance(turns, int):
                return turns

        # Estimate from text length
        text = self._extract_full_text(entry)
        if not text:
            return 0

        # Rough estimate: every 100-200 characters ≈ 1 turn
        return max(1, len(text) // 150)

    def _count_noise_indicators(self, text: str) -> int:
        """Count noise symptom indicators in text."""
        count = 0
        text_lower = text.lower()

        for indicator in NOISE_INDICATORS_CN:
            count += text.count(indicator)
        for indicator in NOISE_INDICATORS_EN:
            count += text_lower.count(indicator)

        return count
