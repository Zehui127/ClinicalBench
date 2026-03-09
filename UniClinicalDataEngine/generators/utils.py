"""Utility functions for dialogue generation.

This module provides helper functions for entity extraction, text processing,
and clinical domain mapping.
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict


# Clinical system to tau2 domain mapping
SYSTEM_TO_DOMAIN = {
    "nervous": "clinical_neurology",
    "skeletal": "clinical_neurology",  # Maps to neurology for now
    "cardiovascular": "clinical_cardiology",
    "digestive": "clinical_gastroenterology",
    "respiratory": "clinical_cardiology",  # Maps to cardiology for now
    "endocrine": "clinical_endocrinology",
    "muscular": "clinical_nephrology",  # Maps to nephrology for now
    "urinary": "clinical_nephrology",
    "reproductive": "clinical_gastroenterology",  # Maps to gastro for now
    "lymphatic": "clinical_cardiology",  # Maps to cardiology for now
    "integumentary": "clinical_cardiology",  # Maps to cardiology for now
    "other / na": "clinical_cardiology",  # Default to cardiology
}

# Task type to dialogue style mapping
TASK_TYPE_PATTERNS = {
    "diagnosis": {
        "style": "diagnostic",
        "focus": "symptoms, history, examination",
        "turns": ["opening", "history", "examination", "diagnosis"]
    },
    "treatment": {
        "style": "treatment",
        "focus": "condition, options, follow-up",
        "turns": ["opening", "diagnosis", "treatment", "closing"]
    },
    "basic science": {
        "style": "educational",
        "focus": "mechanisms, principles",
        "turns": ["opening", "explanation", "closing"]
    },
}


def extract_entities_from_text(text: str) -> Dict[str, Any]:
    """Extract medical entities from question text.

    Args:
        text: The question text

    Returns:
        Dictionary with extracted entities
    """
    entities = {
        "age": None,
        "gender": None,
        "symptoms": [],
        "conditions": [],
        "medications": [],
        "vital_signs": {},
        "lab_values": [],
    }

    # Extract age
    age_patterns = [
        r"(\d+)-year-old",
        r"aged (\d+)",
        r"age\s*:?\s*(\d+)",
    ]
    for pattern in age_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            entities["age"] = int(match.group(1))
            break

    # Extract gender
    if re.search(r"\bmale\b", text, re.IGNORECASE):
        entities["gender"] = "male"
    elif re.search(r"\bfemale\b", text, re.IGNORECASE):
        entities["gender"] = "female"
    elif re.search(r"\bman\b", text, re.IGNORECASE):
        entities["gender"] = "male"
    elif re.search(r"\bwoman\b", text, re.IGNORECASE):
        entities["gender"] = "female"
    elif re.search(r"\bboy\b", text, re.IGNORECASE):
        entities["gender"] = "male"
    elif re.search(r"\bgirl\b", text, re.IGNORECASE):
        entities["gender"] = "female"

    # Common symptoms patterns
    symptom_keywords = [
        "pain", "headache", "fever", "cough", "nausea", "vomiting",
        "fatigue", "weakness", "dizziness", "shortness of breath",
        "chest pain", "abdominal pain", "dyspnea", "palpitations",
        "numbness", "tingling", "rash", "swelling", "bleeding",
    ]
    text_lower = text.lower()
    for symptom in symptom_keywords:
        if symptom in text_lower:
            entities["symptoms"].append(symptom)

    # Extract vital signs
    bp_match = re.search(r"blood pressure\s*(\d+)/(\d+)\s*mmhg", text, re.IGNORECASE)
    if bp_match:
        entities["vital_signs"]["blood_pressure_systolic"] = int(bp_match.group(1))
        entities["vital_signs"]["blood_pressure_diastolic"] = int(bp_match.group(2))

    hr_match = re.search(r"(?:heart rate|pulse)\s*(\d+)\s*/min", text, re.IGNORECASE)
    if hr_match:
        entities["vital_signs"]["heart_rate"] = int(hr_match.group(1))

    temp_match = re.search(r"temperature\s*(\d+\.?\d*)\s*[°fF]", text, re.IGNORECASE)
    if temp_match:
        entities["vital_signs"]["temperature"] = float(temp_match.group(1))

    # Extract medications (common drug names)
    medication_patterns = [
        r"(?:metoprolol|warfarin|aspirin|lisinopril|atorvastatin|metformin|insulin)",
        r"(?:ibuprofen|acetaminophen|amoxicillin|azithromycin|prednisone)",
    ]
    for pattern in medication_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        entities["medications"].extend(matches)

    # Extract conditions (common diseases)
    condition_patterns = [
        r"(?:hypertension|diabetes|atrial fibrillation|asthma|copd)",
        r"(?:cirrhosis|hepatitis|depression|obesity)",
    ]
    for pattern in condition_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        entities["conditions"].extend(matches)

    return entities


def parse_notes(notes: str) -> Dict[str, str]:
    """Parse task notes to extract task type and system.

    Args:
        notes: The notes field from task description

    Returns:
        Dictionary with 'task_type' and 'system' keys
    """
    result = {"task_type": "unknown", "system": "unknown"}

    if "Task:" in notes:
        task_match = re.search(r"Task:\s*([^,]+)", notes)
        if task_match:
            result["task_type"] = task_match.group(1).strip().lower()

    if "System:" in notes:
        system_match = re.search(r"System:\s*([^,\n]+)", notes)
        if system_match:
            result["system"] = system_match.group(1).strip().lower()

    return result


def map_to_tau2_domain(system: str) -> str:
    """Map clinical system to tau2 domain name.

    Args:
        system: The clinical system (e.g., "nervous", "cardiovascular")

    Returns:
        The corresponding tau2 domain name
    """
    return SYSTEM_TO_DOMAIN.get(system, "clinical_general")


def infer_difficulty(task_type: str, question_length: int, has_multiple_choice: bool) -> str:
    """Infer task difficulty from characteristics.

    Args:
        task_type: The type of task (diagnosis, treatment, basic science)
        question_length: Length of the question text
        has_multiple_choice: Whether the question has answer choices

    Returns:
        Difficulty level: "easy", "medium", or "hard"
    """
    if task_type == "basic science":
        return "medium"

    if has_multiple_choice and question_length < 500:
        return "easy"

    if not has_multiple_choice:
        return "hard"

    return "medium"


def determine_gender_from_context(text: str, age: Optional[int] = None) -> Optional[str]:
    """Determine patient gender from context clues.

    Args:
        text: The question text
        age: Patient age (if known)

    Returns:
        "male", "female", or None
    """
    # Direct gender mentions
    if re.search(r"\b(male|man|boy|father|husband)\b", text, re.IGNORECASE):
        return "male"
    if re.search(r"\b(female|woman|girl|mother|wife|pregnant)\b", text, re.IGNORECASE):
        return "female"

    # Context clues
    if re.search(r"\b(prostate|testicular)\b", text, re.IGNORECASE):
        return "male"
    if re.search(r"\b(ovarian|uterine|vaginal|pregnan|menopaus)\b", text, re.IGNORECASE):
        return "female"

    # For children, sometimes indicated by "boy" or "girl"
    if age and age < 18:
        if re.search(r"\bboy\b", text, re.IGNORECASE):
            return "male"
        if re.search(r"\bgirl\b", text, re.IGNORECASE):
            return "female"

    return None


def generate_patient_mrn() -> str:
    """Generate a random patient MRN.

    Returns:
        A random MRN string like "MRN123456"
    """
    import random
    return f"MRN{random.randint(100000, 999999)}"


def truncate_instructions(text: str, max_length: int = 300) -> str:
    """Truncate text to a maximum length, preserving word boundaries.

    Args:
        text: The text to truncate
        max_length: Maximum length

    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text

    # Truncate at word boundary
    truncated = text[:max_length]
    last_space = truncated.rfind(" ")
    if last_space > max_length * 0.8:  # Only if we're not cutting too much
        truncated = truncated[:last_space]

    return truncated + "..."


def generate_patient_name(gender: Optional[str]) -> str:
    """Generate a random patient name based on gender.

    Args:
        gender: "male", "female", or None

    Returns:
        A random full name
    """
    import random

    first_names_male = ["James", "John", "Robert", "Michael", "David", "William", "Richard", "Joseph", "Thomas", "Charles"]
    first_names_female = ["Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]

    if gender == "male":
        first = random.choice(first_names_male)
    elif gender == "female":
        first = random.choice(first_names_female)
    else:
        first = random.choice(first_names_male + first_names_female)

    last = random.choice(last_names)
    return f"{first} {last}"
