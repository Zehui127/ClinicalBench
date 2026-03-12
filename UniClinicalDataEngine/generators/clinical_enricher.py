"""Clinical Data Enricher for enhancing MCQ-based clinical scenarios.

This module uses LLM-based generation to add rich clinical details to
simplified MCQ-based tasks, transforming them into realistic clinical
consultation scenarios.
"""

from typing import Any, Dict, List, Optional
import json
import re


class ClinicalDataEnricher:
    """Enriches clinical scenarios with detailed medical information."""

    # Clinical templates by scenario type
    CLINICAL_TEMPLATES = {
        "acute_coronary_syndrome": {
            "symptoms": {
                "typical": ["substernal chest pain", "radiation to left arm/jaw", "pressure-like sensation"],
                "atypical": ["epigastric pain", "indigestion", "pleuritic pain"],
            },
            "associated_symptoms": ["diaphoresis", "nausea", "vomiting", "dyspnea", "lightheadedness"],
            "risk_factors": ["age > 45 (men) or > 55 (women)", "hypertension", "diabetes", "smoking",
                            "family history of premature CAD", "hyperlipidemia", "obesity"],
            "red_flags": ["pain at rest", "pain lasting > 20 minutes", "hemodynamic instability",
                        "radiating pain", "sweating", "nausea/vomiting"],
            "physical_exam": ["diaphoresis", "S3/S4 gallop", "crackles at lung bases",
                           "hypotension or hypertension", "bradycardia or tachycardia"],
        },
        "heart_failure": {
            "symptoms": {
                "systolic dysfunction": ["dyspnea on exertion", "orthopnea", "PND", "leg swelling"],
                "diastolic dysfunction": ["exercise intolerance", "fatigue", "volume overload"],
            },
            "associated_symptoms": ["weight gain", "abdominal distension", "early satiety", "anorexia"],
            "risk_factors": ["CAD", "hypertension", "valvular disease", "cardiomyopathy", "diabetes",
                            "obesity", "sleep apnea"],
            "red_flags": ["resting dyspnea", "PND", "orthopnea > 2 pillows", "rapid weight gain (>2 lbs/day)",
                        "ascending edema to thighs", "JVD", "hepatomegaly"],
            "physical_exam": ["elevated JVP", "S3 gallop", "laterally displaced PMI",
                           "bilateral crackles", "peripheral edema", "hepatjugular reflux"],
        },
        "arrhythmia": {
            "symptoms": {
                "tachyarrhythmia": ["palpitations", "racing heart", "skipped beats", "forceful beats"],
                "bradyarrhythmia": ["fatigue", "exercise intolerance", "presyncope", "syncope"],
            },
            "associated_symptoms": ["lightheadedness", "dizziness", "shortness of breath", "chest discomfort"],
            "risk_factors": ["age", "structural heart disease", "electrolyte abnormalities", "thyroid disease",
                            "sleep apnea", "alcohol use", "stimulants"],
            "red_flags": ["syncope", "presyncope", "chest pain", "shortness of breath", "sustained HR > 150",
                        "HR < 40", "irregularly irregular"],
            "physical_exam": ["irregular pulse", "tachycardia or bradycardia", "variable S1 intensity",
                           "JVD variations", "hypotension if severe"],
        },
        "hypertensive_urgent": {
            "symptoms": ["headache", "visual changes", "chest pain", "shortness of breath", "dizziness"],
            "associated_symptoms": ["epistaxis", "facial flushing", "tinnitus"],
            "risk_factors": ["poor medication adherence", "medication non-compliance", "salt sensitivity",
                            "obstructive sleep apnea", "renal disease"],
            "red_flags": ["BP > 180/120", "end-organ damage signs", "encephalopathy", "pulmonary edema",
                        "chest pain", "aortic dissection signs"],
            "physical_exam": ["elevated blood pressure", "retinopathy changes", "S4 heart sound",
                           "carotid bruit", "left ventricular heave"],
        },
        "valvular_disease": {
            "symptoms": {
                "stenosis": ["progressive dyspnea", "fatigue", "syncope", "chest pain", "palpitations"],
                "regurgitation": ["exertional dyspnea", "orthopnea", "PND", "fatigue", "edema"],
            },
            "associated_symptoms": ["weight gain", "abdominal bloating", "loss of appetite"],
            "risk_factors": ["age-related degeneration", "rheumatic heart disease", "infective endocarditis",
                            "congenital bicuspid valve", "radiation therapy"],
            "red_flags": ["syncope", "rapidly progressive symptoms", "infective endocarditis signs",
                        "acute decompensation", "new arrhythmias"],
            "physical_exam": ["murmurs (characteristic by valve)", "paradoxical splitting of S2",
                           "loud P2 (pulmonary HTN)", "displaced apex", "elevated JVP"],
        },
    }

    # Demographic profiles for realistic patient generation
    DEMOGRAPHIC_PROFILES = {
        "young_adult": {"age_range": (18, 40), "common_issues": ["arrhythmia", "valvular_congenital"]},
        "middle_aged": {"age_range": (41, 60), "common_issues": ["CAD", "hypertension", "early_HF"]},
        "elderly": {"age_range": (61, 85), "common_issues": ["HF", "CAD", "valvular", "multimorbidity"]},
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the clinical data enricher.

        Args:
            config: Configuration dictionary with options:
                - enrichment_level: "basic", "moderate", "comprehensive" (default: "moderate")
                - include_vitals: bool (default: True)
                - include_lab_results: bool (default: False)
                - include_imaging: bool (default: False)
        """
        self.config = config or {}
        self.enrichment_level = self.config.get("enrichment_level", "moderate")
        self.include_vitals = self.config.get("include_vitals", True)
        self.include_lab_results = self.config.get("include_lab_results", False)
        self.include_imaging = self.config.get("include_imaging", False)

    def detect_scenario_type(self, task_data: Dict[str, Any]) -> str:
        """Detect the clinical scenario type from task data.

        Args:
            task_data: Task dictionary with ticket, description, etc.

        Returns:
            Scenario type key from CLINICAL_TEMPLATES
        """
        ticket = task_data.get("ticket", "").lower()
        known_info = task_data.get("user_scenario", {}).get("instructions", {}).get("known_info", "").lower()

        combined_text = f"{ticket} {known_info}"

        # Keyword matching for scenario types
        scenario_keywords = {
            "acute_coronary_syndrome": ["chest pain", "chest discomfort", "heart attack", "mi", "coronary",
                                      "angina", "ischemic", "stemi", "nstemi"],
            "heart_failure": ["heart failure", "fluid overload", "swelling", "edema", "shortness of breath",
                            "dyspnea", "orthopnea", "pnd", "cardiomyopathy"],
            "arrhythmia": ["palpitation", "racing heart", "irregular", "arrhythmia", "afib", "atrial fibrillation",
                         "tachycardia", "bradycardia", "svd", "av block"],
            "hypertensive_urgent": ["hypertension", "high blood pressure", "elevated bp", "bp",
                                  "severe hypertension", "urgent"],
            "valvular_disease": ["murmur", "valve", "stenosis", "regurgitation", "aortic", "mitral"],
        }

        # Count matches for each scenario
        scores = {}
        for scenario, keywords in scenario_keywords.items():
            score = sum(1 for kw in keywords if kw in combined_text)
            if score > 0:
                scores[scenario] = score

        # Return highest scoring scenario, or default
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        return "acute_coronary_syndrome"  # Default

    def enrich_patient_profile(
        self,
        task_data: Dict[str, Any],
        scenario_type: str
    ) -> Dict[str, Any]:
        """Enrich the patient profile with clinical details.

        Args:
            task_data: Original task data
            scenario_type: Detected clinical scenario type

        Returns:
            Enriched patient profile dictionary
        """
        # Get base patient info
        base_profile = task_data.get("user_scenario", {}).get("instructions", {})
        initial_state = task_data.get("initial_state", {})
        init_actions = initial_state.get("initialization_actions", [{}])[0].get("arguments", {})

        # Build enriched profile
        enriched = {
            "name": init_actions.get("name", "Patient"),
            "age": init_actions.get("age") or self._generate_age(scenario_type),
            "gender": init_actions.get("gender") or self._generate_gender(scenario_type),
            "mrn": init_actions.get("mrn", "AUTO"),
        }

        # Add demographic-appropriate details
        age = enriched["age"]
        if age < 40:
            demographic = "young_adult"
        elif age < 65:
            demographic = "middle_aged"
        else:
            demographic = "elderly"

        # Add social history based on scenario
        enriched["social_history"] = self._generate_social_history(scenario_type, demographic)

        # Add medical history
        enriched["medical_history"] = self._generate_medical_history(scenario_type, demographic)

        # Add medications
        enriched["medications"] = self._generate_medications(scenario_type)

        # Add allergies
        enriched["allergies"] = self._generate_allergies()

        return enriched

    def enrich_clinical_details(
        self,
        task_data: Dict[str, Any],
        scenario_type: str
    ) -> Dict[str, Any]:
        """Generate rich clinical details for the scenario.

        Args:
            task_data: Original task data
            scenario_type: Detected clinical scenario type

        Returns:
            Dictionary with enriched clinical information
        """
        template = self.CLINICAL_TEMPLATES.get(scenario_type, self.CLINICAL_TEMPLATES["acute_coronary_syndrome"])

        enriched = {
            "scenario_type": scenario_type,
            "chief_complaint": self._generate_chief_complaint(task_data, template),
            "present_illness": self._generate_present_illness(task_data, template),
            "symptoms": self._select_symptoms(template, self.enrichment_level),
            "risk_factors": self._select_risk_factors(template, self.enrichment_level),
            "red_flags": self._select_red_flags(template),
        }

        # Add vital signs if configured
        if self.include_vitals:
            enriched["vital_signs"] = self._generate_vital_signs(scenario_type, template)

        # Add physical exam findings
        enriched["physical_exam"] = self._generate_physical_exam(template)

        # Add lab results if configured
        if self.include_lab_results:
            enriched["lab_results"] = self._generate_lab_results(scenario_type)

        # Add imaging if configured
        if self.include_imaging:
            enriched["imaging"] = self._generate_imaging(scenario_type)

        return enriched

    def generate_rich_known_info(
        self,
        patient_profile: Dict[str, Any],
        clinical_details: Dict[str, Any]
    ) -> str:
        """Generate a comprehensive 'known_info' string.

        Args:
            patient_profile: Enriched patient profile
            clinical_details: Enriched clinical details

        Returns:
            Rich, detailed known_info string
        """
        parts = []

        # Demographics
        age = patient_profile.get("age")
        gender = patient_profile.get("gender")
        parts.append(f"{age}-year-old {gender}")

        # Chief complaint with details
        chief_complaint = clinical_details.get("chief_complaint", "")
        parts.append(f"presents with {chief_complaint}")

        # History of present illness
        if clinical_details.get("present_illness"):
            parts.append(f"HPI: {clinical_details['present_illness']}")

        # Risk factors
        risk_factors = clinical_details.get("risk_factors", [])
        if risk_factors:
            parts.append(f"Risk factors: {', '.join(risk_factors[:5])}")  # Limit to top 5

        # Vital signs
        if clinical_details.get("vital_signs"):
            vitals = clinical_details["vital_signs"]
            parts.append(f"Vitals: BP {vitals.get('bp')}, HR {vitals.get('hr')}, RR {vitals.get('rr')}, T {vitals.get('temp')}")

        # Physical exam
        if clinical_details.get("physical_exam"):
            parts.append(f"Exam: {', '.join(clinical_details['physical_exam'][:3])}")

        # Red flags
        if clinical_details.get("red_flags"):
            parts.append(f"Red flags: {', '.join(clinical_details['red_flags'][:3])}")

        return ". ".join(parts) + "."

    def _generate_age(self, scenario_type: str) -> int:
        """Generate age appropriate for scenario type."""
        import random
        if scenario_type == "arrhythmia":
            return random.randint(35, 75)
        elif scenario_type in ["heart_failure", "valvular_disease"]:
            return random.randint(55, 80)
        else:  # ACS, hypertensive
            return random.randint(45, 75)

    def _generate_gender(self, scenario_type: str) -> str:
        """Generate gender appropriate for scenario type."""
        import random
        return random.choice(["male", "female"])

    def _generate_social_history(self, scenario_type: str, demographic: str) -> Dict[str, str]:
        """Generate social history based on scenario and demographics."""
        history = {}

        if scenario_type in ["acute_coronary_syndrome", "heart_failure"]:
            # Common risk factors
            history["smoking"] = "Former smoker (20 pack-years), quit 5 years ago"
            history["alcohol"] = "Social drinker (1-2 drinks/week)"
        elif scenario_type == "arrhythmia":
            history["caffeine"] = "Drinks 2-3 cups of coffee/day"
            history["alcohol"] = "Occasional social drinker"

        return history

    def _generate_medical_history(self, scenario_type: str, demographic: str) -> List[str]:
        """Generate relevant medical history."""
        if scenario_type == "acute_coronary_syndrome":
            return ["Hypertension (10 years)", "Hyperlipidemia", "Type 2 Diabetes Mellitus"]
        elif scenario_type == "heart_failure":
            return ["Hypertension (15 years)", "Previous MI (3 years ago)", "CKD Stage 3"]
        elif scenario_type == "arrhythmia":
            return ["Hypertension", "Sleep apnea", "Thyroid disorder"]
        elif scenario_type == "hypertensive_urgent":
            return ["Hypertension (diagnosed 8 years ago)", "Medication non-adherence"]
        else:  # valvular
            return ["Childhood rheumatic fever", "Progressive dyspnea (2 years)"]

    def _generate_medications(self, scenario_type: str) -> List[str]:
        """Generate current medications based on scenario."""
        if scenario_type == "acute_coronary_syndrome":
            return ["Lisinopril 10mg daily", "Metformin 1000mg BID", "Atorvastatin 20mg nightly"]
        elif scenario_type == "heart_failure":
            return ["Carvedilol 25mg BID", "Lisinopril 20mg daily", "Furosemide 40mg daily",
                   "Spironolactone 25mg daily"]
        else:
            return ["Lisinopril 10mg daily", "Amlodipine 5mg daily"]

    def _generate_allergies(self) -> List[str]:
        """Generate medication allergies."""
        import random
        # 80% no allergies, 20% have allergies
        if random.random() < 0.8:
            return ["NKDA"]
        else:
            return ["Penicillin (rash)", "Sulfa drugs"]

    def _generate_chief_complaint(self, task_data: Dict, template: Dict) -> str:
        """Generate detailed chief complaint."""
        original_ticket = task_data.get("ticket", "")

        # Extract key complaint and add detail
        if "chest" in original_ticket.lower():
            return "substernal chest discomfort lasting 2 hours, non-radiating, 6/10 severity, " \
                   "associated with diaphoresis but no nausea"
        elif "palpitation" in original_ticket.lower() or "racing" in original_ticket.lower():
            return "episodic palpitations lasting 10-15 minutes, associated with lightheadedness, " \
                   "no chest pain or syncope"
        elif "swelling" in original_ticket.lower() or "edema" in original_ticket.lower():
            return "progressive bilateral lower extremity edema over 4 weeks, now up to thighs, " \
                   "worse at end of day, improved with elevation"
        else:
            return original_ticket

    def _generate_present_illness(self, task_data: Dict, template: Dict) -> str:
        """Generate detailed history of present illness."""
        scenario_type = template.get("scenario_type", "general")

        if scenario_type == "acute_coronary_syndrome":
            return "Patient reports chest discomfort that began 2 hours ago while resting. " \
                   "Describes as pressure-like, 6/10 severity, located substernally without radiation. " \
                   "Associated with diaphoresis but no nausea, vomiting, or dyspnea. " \
                   "Denies similar episodes in the past. No exacerbating or relieving factors identified."
        elif scenario_type == "arrhythmia":
            return "Patient reports episodic palpitations for the past 3 months, occurring 2-3 times per week. " \
                   "Episodes last 10-15 minutes, associated with lightheadedness but no syncope. " \
                   "Palpations described as 'irregular racing'. No clear triggers identified. " \
                   "Caffeine intake unchanged."
        else:
            return "Symptoms have been gradually worsening over the past few weeks."

    def _select_symptoms(self, template: Dict, level: str) -> List[str]:
        """Select appropriate symptoms based on enrichment level."""
        typical = template.get("symptoms", {}).get("typical", [])
        associated = template.get("associated_symptoms", [])

        if level == "basic":
            return typical[:2] + associated[:1]
        elif level == "moderate":
            return typical + associated[:3]
        else:  # comprehensive
            return typical + associated

    def _select_risk_factors(self, template: Dict, level: str) -> List[str]:
        """Select risk factors based on enrichment level."""
        all_factors = template.get("risk_factors", [])

        if level == "basic":
            return all_factors[:2]
        elif level == "moderate":
            return all_factors[:4]
        else:
            return all_factors

    def _select_red_flags(self, template: Dict) -> List[str]:
        """Select red flags from template."""
        return template.get("red_flags", [])

    def _generate_vital_signs(self, scenario_type: str, template: Dict) -> Dict[str, str]:
        """Generate appropriate vital signs for scenario."""
        import random

        if scenario_type == "acute_coronary_syndrome":
            return {
                "bp": "158/92 mmHg",
                "hr": "102 bpm",
                "rr": "18 breaths/min",
                "temp": "98.6°F (37.0°C)",
                "spo2": "97% on room air"
            }
        elif scenario_type == "heart_failure":
            return {
                "bp": "138/84 mmHg",
                "hr": "88 bpm (irregularly irregular)",
                "rr": "22 breaths/min",
                "temp": "98.4°F (36.9°C)",
                "spo2": "94% on room air"
            }
        else:
            return {
                "bp": "145/88 mmHg",
                "hr": "78 bpm",
                "rr": "16 breaths/min",
                "temp": "98.6°F (37.0°C)",
                "spo2": "98% on room air"
            }

    def _generate_physical_exam(self, template: Dict) -> List[str]:
        """Generate physical exam findings."""
        all_findings = template.get("physical_exam", [])
        # Select 3-4 relevant findings
        return all_findings[:4] if len(all_findings) >= 4 else all_findings

    def _generate_lab_results(self, scenario_type: str) -> Dict[str, str]:
        """Generate relevant lab results."""
        if scenario_type == "acute_coronary_syndrome":
            return {
                "troponin": "0.08 ng/mL (elevated, normal <0.04)",
                "ck_mb": "Normal",
                "bnf": "Normal",
                "cmp": "K+ 4.2, Cr 1.1, BUN 18",
                "cbc": "WNL"
            }
        elif scenario_type == "heart_failure":
            return {
                "bnp": "650 pg/mL (elevated)",
                "cmp": "K+ 4.0, Cr 1.4, BUN 28",
                "cbc": "Hb 13.2, Hct 39.5%",
                "lft": "WNL"
            }
        else:
            return {}

    def _generate_imaging(self, scenario_type: str) -> Dict[str, str]:
        """Generate imaging findings."""
        if scenario_type == "acute_coronary_syndrome":
            return {
                "ekg": "Sinus tachycardia at 102, ST elevation 1mm in V2-V4, T wave inversions in I, aVL",
                "cxr": "Normal cardiac silhouette, clear lung fields"
            }
        elif scenario_type == "heart_failure":
            return {
                "ekg": "Atrial fibrillation at 88 bpm, LVH criteria",
                "echo": "LVEF 35%, mild to moderate MR, LA enlargement",
                "cxr": "Cardiomegaly, mild pulmonary edema"
            }
        else:
            return {}

    def enrich_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main method to enrich a single task.

        Args:
            task_data: Original task dictionary

        Returns:
            Enriched task dictionary with enhanced clinical information
        """
        # Detect scenario type
        scenario_type = self.detect_scenario_type(task_data)

        # Enrich patient profile
        enriched_profile = self.enrich_patient_profile(task_data, scenario_type)

        # Enrich clinical details
        enriched_clinical = self.enrich_clinical_details(task_data, scenario_type)

        # Generate rich known_info
        rich_known_info = self.generate_rich_known_info(enriched_profile, enriched_clinical)

        # Build enriched task
        enriched_task = task_data.copy()

        # Update user_scenario with enriched information
        if "user_scenario" not in enriched_task:
            enriched_task["user_scenario"] = {}
        if "instructions" not in enriched_task["user_scenario"]:
            enriched_task["user_scenario"]["instructions"] = {}

        # Update instructions with rich clinical info
        enriched_task["user_scenario"]["instructions"].update({
            "known_info": rich_known_info,
            "enriched_scenario_type": scenario_type,
            "enrichment_level": self.enrichment_level,
        })

        # Update initial state with enriched patient info
        if "initial_state" not in enriched_task:
            enriched_task["initial_state"] = {}
        if "initialization_actions" not in enriched_task["initial_state"]:
            enriched_task["initial_state"]["initialization_actions"] = []

        enriched_task["initial_state"]["initialization_actions"] = [{
            "env_type": "user",
            "func_name": "set_user_info",
            "arguments": enriched_profile
        }]

        # Add metadata
        if "description" not in enriched_task:
            enriched_task["description"] = {}
        enriched_task["description"]["notes"] = (
            f"Enriched from MCQ. Scenario: {scenario_type}. "
            f"Enrichment level: {self.enrichment_level}."
        )

        return enriched_task


def batch_enrich_tasks(
    tasks: List[Dict[str, Any]],
    config: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Enrich a batch of tasks.

    Args:
        tasks: List of task dictionaries
        config: Optional configuration for enricher

    Returns:
        List of enriched task dictionaries
    """
    enricher = ClinicalDataEnricher(config)
    return [enricher.enrich_task(task) for task in tasks]


if __name__ == "__main__":
    # Example usage
    sample_task = {
        "id": "test_task_001",
        "ticket": "I have chest pain",
        "user_scenario": {
            "instructions": {
                "known_info": "Chest pain"
            }
        },
        "initial_state": {
            "initialization_actions": [{
                "arguments": {
                    "name": "John Doe",
                    "age": None,
                    "gender": None
                }
            }]
        }
    }

    enricher = ClinicalDataEnricher({"enrichment_level": "moderate"})
    enriched = enricher.enrich_task(sample_task)

    print("=== Original Task ===")
    print(json.dumps(sample_task, indent=2))
    print("\n=== Enriched Task ===")
    print(json.dumps(enriched, indent=2))
