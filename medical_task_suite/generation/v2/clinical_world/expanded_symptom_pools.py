#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Expanded Symptom Pools — Larger noise/misleading pools from PrimeKG + curation.

Replaces the hand-coded 19-item NOISE_SYMPTOM_POOL and 10-item MISLEADING_SYMPTOM_MAP
with expanded versions derived from PrimeKG phenotype analysis and clinical curation.

Usage:
    from .expanded_symptom_pools import EXPANDED_NOISE_SYMPTOM_POOL, EXPANDED_MISLEADING_SYMPTOM_MAP
"""

from typing import Dict, List


# ============================================================
# Expanded Noise Symptom Pool (60+ symptoms)
# ============================================================

EXPANDED_NOISE_SYMPTOM_POOL: List[str] = [
    # Original 19 (kept)
    "mild headache", "occasional dizziness", "minor skin rash",
    "slight nausea", "mild fatigue", "intermittent back pain",
    "occasional heartburn", "mild joint stiffness", "slight blurry vision",
    "trouble sleeping", "dry mouth", "mild anxiety",
    "occasional ringing in ears", "slight swelling in ankles",
    "mild constipation", "bloating", "mild throat irritation",
    "occasional muscle cramps", "slight hand numbness",

    # New: General symptoms (patient-reportable, low specificity)
    "dry skin", "brittle nails", "hair thinning",
    "mild eye dryness", "occasional eye floaters",
    "mild jaw clicking", "clicking in knee",
    "occasional tingling in fingers", "cold hands and feet",
    "mild sweating at night", "occasional hot flashes",
    "mild sensitivity to light", "occasional ear fullness",
    "slight tremor in hands", "mild unsteadiness when walking",
    "occasional food craving", "metallic taste in mouth",
    "mild body odor change", "slight change in urine color",
    "occasional shallow breathing", "mild weakness in arms",

    # New: Common benign symptoms
    "morning stiffness", "occasional heart pounding after exercise",
    "mild itching without rash", "slight sensitivity to cold",
    "occasional clicking jaw", "mild foot arch pain",
    "slight memory fog", "occasional word-finding difficulty",
    "mild neck tension", "slight shoulder tightness",
    "occasional twitching eyelid", "mild teeth grinding",
    "slight change in appetite", "mild indigestion after spicy food",
    "occasional yawning", "slight voice hoarseness in morning",
    "mild sensitivity to noise", "occasional deja vu",
]


# ============================================================
# Expanded Misleading Symptom Map (30+ diseases)
# ============================================================

EXPANDED_MISLEADING_SYMPTOM_MAP: Dict[str, List[str]] = {
    # Original 10 (kept)
    "type 2 diabetes": ["weight loss", "frequent infections"],
    "hypertension": ["nosebleed", "visual changes"],
    "coronary artery disease": ["jaw pain", "left arm pain"],
    "copd": ["morning headache", "swollen ankles"],
    "asthma": ["chronic cough", "difficulty swallowing"],
    "heart failure": ["abdominal swelling", "loss of appetite"],
    "stroke": ["ear pain", "toothache"],
    "atrial fibrillation": ["chest pressure", "sweating"],
    "gerd": ["chronic cough", "sore throat"],
    "anxiety disorder": ["chest pain", "shortness of breath"],

    # New: Cardiovascular
    "hyperlipidemia": ["yellow skin bumps", "arcus corneae"],
    "pulmonary embolism": ["leg swelling", "calf pain"],
    "deep vein thrombosis": ["leg warmth", "leg redness"],

    # New: Endocrine
    "hyperthyroidism": ["heat intolerance", "bulging eyes"],
    "hypothyroidism": ["cold intolerance", "puffy face"],
    "metabolic syndrome": ["darkened skin folds", "increased thirst"],

    # New: Respiratory
    "pneumonia": ["chest pain with breathing", "night sweats"],
    "bronchitis": ["wheezing", "low-grade fever"],
    "sleep apnea": ["morning headache", "difficulty concentrating"],

    # New: Neurological
    "migraine": ["neck stiffness", "visual spots"],
    "epilepsy": ["confusion", "memory loss"],
    "parkinson disease": ["soft voice", "small handwriting"],
    "multiple sclerosis": ["eye pain with movement", "electric shock sensation"],

    # New: GI
    "cirrhosis": ["spider-like blood vessels", "red palms"],
    "pancreatitis": ["back pain", "fatty stools"],
    "peptic ulcer disease": ["nighttime stomach pain", "bloating"],
    "irritable bowel syndrome": ["urgency", "incomplete evacuation"],

    # New: Musculoskeletal
    "rheumatoid arthritis": ["morning stiffness over 1 hour", "symmetrical joint pain"],
    "gout": ["red hot joint", "intense pain at night"],
    "osteoporosis": ["height loss", "stooped posture"],
    "fibromyalgia": ["tender points", "widespread pain"],

    # New: Renal/Heme
    "chronic kidney disease": ["metallic taste", "itching all over"],
    "anemia": ["pale skin", "cold hands"],
    "nephrolithiasis": ["groin pain", "blood in urine"],

    # New: Other
    "depression": ["unexplained aches", "social withdrawal"],
    "anemia": ["pale skin", "cold hands"],
    "psoriasis": ["joint pain", "nail pitting"],
    "meningitis": ["light sensitivity", "stiff neck"],
}


def generate_misleading_from_overlap(
    disease: str,
    disease_symptoms: List[str],
    overlap_diseases: Dict[str, float],
    overlap_symptom_map: Dict[str, List[str]],
) -> List[str]:
    """
    Generate misleading symptoms from symptom overlap between diseases.

    For each overlapping disease, pick symptoms present in the overlap disease
    but NOT in the target disease. These are naturally misleading because they
    suggest the wrong diagnosis.

    Args:
        disease: Target disease name
        disease_symptoms: Target disease's symptoms
        overlap_diseases: {other_disease: jaccard_score}
        overlap_symptom_map: {disease: [symptoms]}

    Returns:
        List of misleading symptoms
    """
    target_set = {s.lower() for s in disease_symptoms}
    misleading = []

    # Sort by overlap score (highest overlap = most confusing)
    sorted_overlaps = sorted(overlap_diseases.items(), key=lambda x: -x[1])

    for other_disease, overlap_score in sorted_overlaps[:3]:
        other_symptoms = overlap_symptom_map.get(other_disease, [])
        # Symptoms in other disease but NOT in target = misleading
        for symptom in other_symptoms:
            if symptom.lower() not in target_set and symptom not in misleading:
                misleading.append(symptom)
                if len(misleading) >= 3:
                    return misleading

    return misleading
