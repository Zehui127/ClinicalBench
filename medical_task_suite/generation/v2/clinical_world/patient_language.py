#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patient Language Layer — Convert clinical terminology to patient-friendly speech.

Problem: disease_profiles give us clinical questions ("Have you noticed increased thirst?")
         and medical terms ("bronchial asthma", "SARS-CoV-2", "hemoglobin SS disease").
         Real patients say "I've been really thirsty lately" or "I can't breathe well".

This module provides:
1. clinical_to_patient(): Convert any clinical term to patient-friendly language
2. generate_patient_complaint(): Generate natural chief complaint for a disease
3. symptom_to_patient_response(): Convert symptom to natural patient speech
"""

import random
import re
from typing import Dict, List, Optional, Tuple


# ============================================================
# Core Mapping: Clinical Term → Patient-Friendly Term
# ============================================================

CLINICAL_TO_PATIENT: Dict[str, str] = {
    # --- Symptoms (clinical → patient) ---
    "dyspnea": "trouble breathing",
    "dyspnoea": "trouble breathing",
    "orthopnea": "trouble breathing when lying down",
    "dysuria": "pain when urinating",
    "polyuria": "having to pee a lot",
    "polydipsia": "being really thirsty",
    "polyphagia": "being really hungry",
    "nocturia": "waking up at night to pee",
    "hematuria": "blood in my urine",
    "hemoptysis": "coughing up blood",
    "hematemesis": "throwing up blood",
    "melena": "dark tarry stools",
    "pruritus": "itching",
    "urticaria": "hives",
    "erythema": "redness",
    "edema": "swelling",
    "cyanosis": "turning blue",
    "jaundice": "yellowing of my skin and eyes",
    "pallor": "looking pale",
    "diaphoresis": "sweating a lot",
    "hyperhidrosis": "sweating a lot",
    "myalgia": "muscle pain",
    "arthralgia": "joint pain",
    "neuralgia": "nerve pain",
    "paresthesia": "tingling or numbness",
    "vertigo": "feeling like the room is spinning",
    "syncope": "fainting",
    "presyncope": "feeling like I'm going to pass out",
    "somnolence": "feeling really sleepy",
    "insomnia": "trouble sleeping",
    "anorexia": "loss of appetite",
    "nausea": "feeling sick to my stomach",
    "emesis": "throwing up",
    "constipation": "trouble going to the bathroom",
    "diarrhea": "loose stools",
    "tenesmus": "feeling like I need to go but can't",
    "dysphagia": "trouble swallowing",
    "odynophagia": "painful swallowing",
    "palpitations": "feeling my heart racing",
    "tachycardia": "fast heartbeat",
    "bradycardia": "slow heartbeat",
    "arrhythmia": "irregular heartbeat",
    "angina": "chest pain or pressure",
    "claudication": "leg pain when walking",
    "photophobia": "eyes hurting in bright light",
    "phonophobia": "being sensitive to loud sounds",
    "tinnitus": "ringing in my ears",
    "diplopia": "seeing double",
    "scotoma": "blind spots in my vision",
    "nystagmus": "eyes moving on their own",
    "ataxia": "trouble with balance",
    "aphasia": "trouble speaking",
    "dysarthria": "trouble speaking clearly",
    "apraxia": "trouble doing things I used to do",
    "cataplexy": "suddenly losing muscle strength",
    "narcolepsy": "falling asleep suddenly",

    # --- Disease names (clinical → patient) ---
    "bronchial asthma": "asthma",
    "sars-cov-2": "COVID",
    "covid-19": "COVID",
    "hemoglobin ss disease": "sickle cell disease",
    "sickle cell anemia": "sickle cell disease",
    "chronic obstructive airway disease": "COPD",
    "chronic obstructive pulmonary disease": "COPD",
    "coad": "COPD",
    "myocardial infarction": "heart attack",
    "cerebrovascular accident": "stroke",
    "cerebral vascular accident": "stroke",
    "transient ischemic attack": "mini-stroke",
    "hypertension": "high blood pressure",
    "htn": "high blood pressure",
    "essential hypertension": "high blood pressure",
    "primary hypertension": "high blood pressure",
    "hyperlipidemia": "high cholesterol",
    "dyslipidemia": "high cholesterol",
    "type 2 diabetes mellitus": "type 2 diabetes",
    "t2dm": "type 2 diabetes",
    "type 2 diabetes": "type 2 diabetes",
    "diabetes mellitus": "diabetes",
    "type 1 diabetes mellitus": "type 1 diabetes",
    "t1dm": "type 1 diabetes",
    "nephrolithiasis": "kidney stones",
    "urolithiasis": "kidney stones",
    "cholelithiasis": "gallstones",
    "peptic ulcer disease": "stomach ulcer",
    "gastroesophageal reflux disease": "acid reflux",
    "gerd": "acid reflux",
    "irritable bowel syndrome": "IBS",
    "ibs": "IBS",
    "ibd": "inflammatory bowel disease",
    "crohn disease": "Crohn's disease",
    "systemic lupus erythematosus": "lupus",
    "sle": "lupus",
    "rheumatoid arthritis": "RA",
    "osteoarthritis": "arthritis",
    "oa": "arthritis",
    "degenerative joint disease": "arthritis",
    "bph": "enlarged prostate",
    "benign prostatic hyperplasia": "enlarged prostate",
    "ckd": "chronic kidney disease",
    "chronic kidney disease": "kidney disease",
    "copd": "COPD",
    "cad": "coronary artery disease",
    "coronary artery disease": "heart disease",
    "chf": "heart failure",
    "afib": "atrial fibrillation",
    "major depressive disorder": "depression",
    "clinical depression": "depression",
    "generalized anxiety disorder": "anxiety",
    "panic disorder": "panic attacks",
    "post-traumatic stress disorder": "PTSD",
    "adhd": "ADHD",
    "bipolar disorder": "bipolar",
    "parkinson disease": "Parkinson's",
    "parkinsons": "Parkinson's",
    "multiple sclerosis": "MS",
    "amyotrophic lateral sclerosis": "ALS",
    "congestive heart failure": "heart failure",
    "chronic kidney disease": "kidney disease",
    "end-stage renal disease": "kidney failure",
    "esrd": "kidney failure",
    "hepatitis b": "hepatitis B",
    "hepatitis c": "hepatitis C",
    "pulmonary embolism": "blood clot in my lung",
    "deep vein thrombosis": "blood clot in my leg",
    "atrial fibrillation": "irregular heartbeat",
    "peripheral neuropathy": "nerve damage",
    "cellulitis": "skin infection",
    "pancreatitis": "inflammation of my pancreas",
    "appendicitis": "appendix inflammation",
    "meningitis": "infection around my brain",
    "encephalitis": "brain inflammation",
    "glaucoma": "eye pressure",
    "cataract": "cloudy vision",
    "macular degeneration": "vision loss",
    "fibromyalgia": "widespread pain",
    "chronic fatigue syndrome": "constant tiredness",
    "sleep apnea": "stopping breathing in my sleep",
    "obstructive sleep apnea": "stopping breathing in my sleep",

    # --- Lab/test terms ---
    "cbc": "blood count",
    "complete blood count": "blood count",
    "bmp": "basic blood panel",
    "cmp": "comprehensive blood panel",
    "hba1c": "A1C",
    "hemoglobin a1c": "A1C",
    "tsh": "thyroid test",
    "lipid panel": "cholesterol test",
    "metabolic panel": "blood chemistry test",
    "urinalysis": "urine test",
    "chest x-ray": "chest X-ray",
    "ct scan": "CT scan",
    "mri": "MRI",
    "ecg": "EKG",
    "ekg": "EKG",
    "electrocardiogram": "EKG",
    "echocardiogram": "heart ultrasound",
}

# Question patterns → patient complaint extraction
QUESTION_PATTERNS = [
    # "Have you noticed X?" → "I've been having X"
    (r"have you noticed (any )?(.+?)\??$", r"I've been having {2}"),
    # "Do you have X?" → "I have X"
    (r"do you (have|get|experience) (any )?(.+?)\??$", r"I {1} {3}"),
    # "Are you experiencing X?" → "I'm experiencing X"
    (r"are you experiencing (any )?(.+?)\??$", r"I'm experiencing {2}"),
    # "Has your X changed?" → "My X has changed"
    (r"has your (.+?) changed.*?\??$", r"my {1} has changed"),
    # "How often do you X?" → extract the action
    (r"how often (.+?)\??$", None),  # Can't extract complaint, use fallback
    # "Can you describe X?" → extract the topic
    (r"can you describe (.+?)\??$", None),
    # "Does X get worse when Y?" → extract X
    (r"does (.+?) (get|feel) worse.*?\??$", r"my {1} gets worse sometimes"),
    # "Have you had X?" → "I've had X"
    (r"have you had (any )?(.+?)\??$", r"I've had {2}"),
    # "Do you feel X?" → "I feel X"
    (r"do you feel (.+?)\??$", r"I feel {1}"),
    # "Is there X?" → "I have X"
    (r"is there (any )?(.+?)\??$", r"I have {2}"),
]

# Patient-friendly symptom templates for common complaints
PATIENT_COMPLAINT_TEMPLATES = {
    "fatigue": [
        "I've been feeling really tired lately",
        "I just have no energy",
        "I'm exhausted all the time",
        "I can barely keep my eyes open during the day",
    ],
    "headache": [
        "I've been getting headaches",
        "my head hurts a lot",
        "I keep getting these terrible headaches",
    ],
    "chest pain": [
        "I've been having chest pain",
        "my chest hurts",
        "I get this pressure in my chest",
    ],
    "shortness of breath": [
        "I can't catch my breath",
        "I get winded really easily",
        "it's hard to breathe",
    ],
    "cough": [
        "I can't stop coughing",
        "I've had this cough that won't go away",
    ],
    "fever": [
        "I've been running a fever",
        "I feel like I'm burning up",
        "I've had a temperature",
    ],
    "nausea": [
        "I feel sick to my stomach",
        "I keep feeling like I'm going to throw up",
        "my stomach's been upset",
    ],
    "dizziness": [
        "I've been getting dizzy",
        "the room keeps spinning",
        "I feel lightheaded",
    ],
    "pain": [
        "I'm in a lot of pain",
        "everything hurts",
    ],
    "joint pain": [
        "my joints ache",
        "my joints are really stiff and painful",
        "I can barely move my fingers some mornings",
    ],
    "back pain": [
        "my back is killing me",
        "I've had terrible back pain",
    ],
    "abdominal pain": [
        "my stomach really hurts",
        "I've been having belly pain",
        "I get these stomach cramps",
    ],
    "anxiety": [
        "I've been really anxious",
        "I can't stop worrying about everything",
        "I feel on edge all the time",
    ],
    "insomnia": [
        "I can't sleep",
        "I lie awake all night",
        "I haven't been sleeping well at all",
    ],
    "frequent urination": [
        "I keep having to pee all the time",
        "I'm running to the bathroom constantly",
    ],
    "thirst": [
        "I'm always thirsty",
        "I can't seem to drink enough water",
    ],
    "weight loss": [
        "I've been losing weight without trying",
        "the pounds are just falling off",
    ],
    "swelling": [
        "I've noticed swelling",
        "things are getting puffy and swollen",
    ],
    "weakness": [
        "I feel really weak",
        "my arms and legs feel like jelly",
    ],
    "confusion": [
        "I've been feeling confused",
        "I can't think straight",
        "things feel foggy",
    ],
    "wheezing": [
        "I make this whistling sound when I breathe",
        "my chest feels tight and I wheeze",
    ],
    "skin rash": [
        "I've got this rash",
        "my skin is all red and itchy",
    ],
    "palpitations": [
        "my heart keeps racing",
        "I can feel my heart pounding in my chest",
    ],
    "blurred vision": [
        "my vision's been blurry",
        "everything looks fuzzy",
    ],
    "numbness": [
        "parts of my body feel numb",
        "I can't feel my hands sometimes",
    ],
    "seizure": [
        "I've been having seizures",
        "I had an episode where I blacked out and shook",
    ],
    "tremor": [
        "my hands are shaking",
        "I can't keep my hands still",
    ],
    "constipation": [
        "I can't go to the bathroom",
        "I'm really backed up",
    ],
    "diarrhea": [
        "I keep having to run to the bathroom",
        "I've had really loose stools",
    ],
    "heartburn": [
        "I get this burning in my chest after eating",
        "I have terrible heartburn",
    ],
    "stiffness": [
        "I'm really stiff, especially in the mornings",
        "I can barely get moving when I wake up",
    ],
}


class PatientLanguageLayer:
    """
    Convert clinical terminology to natural patient speech.

    Usage:
        layer = PatientLanguageLayer()
        patient_symptom = layer.to_patient("bronchial asthma")       # "asthma"
        complaint = layer.generate_complaint("stroke", ["weakness"])  # "I feel really weak"
        response = layer.symptom_to_response("polyuria")             # "I keep having to pee"
    """

    def __init__(self):
        self._mapping = CLINICAL_TO_PATIENT
        self._templates = PATIENT_COMPLAINT_TEMPLATES
        self._rng = random.Random()

    def to_patient(self, clinical_term: str) -> str:
        """
        Convert any clinical term to patient-friendly language.

        Handles:
        - Direct mapping (dyspnea → trouble breathing)
        - Disease names (bronchial asthma → asthma)
        - Clinical questions → patient complaints
        - Fallback: clean up and humanize
        """
        term = clinical_term.strip().lower().rstrip("?.")

        # 1. Direct lookup
        if term in self._mapping:
            return self._mapping[term]

        # 2. Try reverse lookup for partial matches
        for clinical, patient in self._mapping.items():
            if clinical in term or term in clinical:
                return patient

        # 3. If it's a clinical question, extract the complaint
        if "?" in clinical_term or term.startswith(("have you", "do you", "are you", "has your", "does ", "is there", "can you")):
            extracted = self._extract_complaint_from_question(clinical_term)
            if extracted:
                return extracted

        # 4. Clean up remaining clinical terms
        cleaned = self._humanize(term)
        return cleaned

    def generate_complaint(
        self,
        disease: str,
        symptoms: List[str],
        mood: str = "neutral",
    ) -> str:
        """
        Generate a natural chief complaint for a disease.

        Args:
            disease: Target disease name
            symptoms: List of symptoms (clinical or patient-friendly)
            mood: Patient mood (neutral, anxious, reluctant, hurried)

        Returns:
            Natural patient complaint string
        """
        # Convert all symptoms to patient-friendly
        patient_symptoms = [self.to_patient(s) for s in symptoms]

        # Filter empty
        patient_symptoms = [s for s in patient_symptoms if s and len(s) > 2]

        if not patient_symptoms:
            return self._mood_template("I just don't feel right.", mood)

        # Use template-based generation for known symptoms
        complaints = []
        for symptom in patient_symptoms[:3]:
            template = self._find_template(symptom)
            if template:
                complaints.append(template)
            else:
                complaints.append(f"I've been having {symptom}")

        # Join complaints naturally
        if len(complaints) == 1:
            main = complaints[0]
        elif len(complaints) == 2:
            main = f"{complaints[0]}, and {complaints[1]}"
        else:
            main = f"{complaints[0]}, {complaints[1]}, and also {complaints[2]}"

        return self._mood_template(main, mood)

    def symptom_to_response(
        self,
        symptom: str,
        visibility: str = "volunteer",
    ) -> str:
        """
        Convert a symptom to a natural patient response.

        Args:
            symptom: Clinical symptom term
            visibility: "volunteer", "if_asked", "resistant", "hidden"

        Returns:
            Natural response string
        """
        patient_term = self.to_patient(symptom)

        templates = {
            "volunteer": [
                f"I've been having {patient_term}.",
                f"I noticed {patient_term}.",
                f"Actually, I've been dealing with {patient_term} too.",
            ],
            "if_asked": [
                f"Yes, I have been having {patient_term}.",
                f"Yeah, now that you mention it, {patient_term}.",
                f"Actually yes, {patient_term}.",
            ],
            "resistant": [
                f"Well, I didn't think it was important, but... {patient_term}.",
                f"I guess I should mention, {patient_term}.",
                f"Okay fine, {patient_term} too.",
            ],
            "hidden": [
                f"I didn't want to bring it up, but... {patient_term}.",
                f"Actually, there's one more thing. {patient_term}.",
                f"I was hoping it would go away, but {patient_term}.",
            ],
        }

        pool = templates.get(visibility, templates["volunteer"])
        return self._rng.choice(pool)

    # ================================================================
    # Internal
    # ================================================================

    def _extract_complaint_from_question(self, question: str) -> Optional[str]:
        """Extract a patient complaint from a clinical question."""
        q = question.strip().rstrip("?")

        # Try regex patterns
        for pattern, replacement in QUESTION_PATTERNS:
            if replacement is None:
                continue
            match = re.match(pattern, q.lower())
            if match:
                try:
                    groups = match.groups()
                    complaint = replacement
                    for i, g in enumerate(groups):
                        complaint = complaint.replace(f"{{{i+1}}}", g or "")
                    # Clean up double spaces
                    complaint = re.sub(r"\s+", " ", complaint).strip()
                    if len(complaint) > 10:
                        return complaint
                except (IndexError, ValueError):
                    continue

        # Fallback: extract the key noun phrase
        # Remove question words and modal verbs
        cleaned = re.sub(
            r"^(have you |do you |are you |does |is there |has your |can you |how often |when did |what )",
            "",
            q.lower(),
        )
        cleaned = re.sub(r"^(noticed|experienced|been having|any|some)\s*", "", cleaned)
        cleaned = re.sub(r"\?$", "", cleaned).strip()

        if len(cleaned) > 5:
            return f"I've been having {cleaned}"

        return None

    def _find_template(self, symptom: str) -> Optional[str]:
        """Find a complaint template matching this symptom."""
        symptom_lower = symptom.lower()

        # Direct match
        if symptom_lower in self._templates:
            return self._rng.choice(self._templates[symptom_lower])

        # Partial match
        for key, templates in self._templates.items():
            if key in symptom_lower or symptom_lower in key:
                return self._rng.choice(templates)

        return None

    def _humanize(self, term: str) -> str:
        """Clean up clinical terminology into more readable form."""
        # Remove common clinical suffixes
        cleaned = term
        for suffix in [" disease", " syndrome", " disorder", " condition"]:
            if cleaned.endswith(suffix):
                cleaned = cleaned[:-len(suffix)]
                break

        # Replace common clinical words
        replacements = {
            "chronic": "long-term",
            "acute": "sudden",
            "bilateral": "both sides",
            "unilateral": "one side",
            "recurrent": "recurring",
            "idiopathic": "unknown cause",
            "benign": "not cancer",
            "malignant": "cancer",
            "metastatic": "spread",
            "congenital": "born with",
        }
        for clinical, patient in replacements.items():
            cleaned = cleaned.replace(clinical, patient)

        return cleaned

    def _mood_template(self, base: str, mood: str) -> str:
        """Apply mood to a base complaint."""
        if mood == "anxious":
            return f"I'm really worried. {base}"
        elif mood == "reluctant":
            return f"I guess {base.lower()}. It's probably nothing."
        elif mood == "hurried":
            return f"Look, {base.lower()}. Can we figure this out quickly?"
        else:
            return base
