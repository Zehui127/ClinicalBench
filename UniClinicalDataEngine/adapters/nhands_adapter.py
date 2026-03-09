"""NHands-specific clinical data adapter."""

import json
from pathlib import Path
from typing import Any, Dict, List

from UniClinicalDataEngine.adapters.base import BaseAdapter
# Import from models.py file directly to avoid conflict with models/ directory
import importlib.util
_models_spec = importlib.util.spec_from_file_location(
    "uni_clinical_models",
    Path(__file__).parent.parent / "models.py"
)
_models_module = importlib.util.module_from_spec(_models_spec)
_models_spec.loader.exec_module(_models_module)
ClinicalScenario = _models_module.ClinicalScenario
PatientRecord = _models_module.PatientRecord


class NHandsAdapter(BaseAdapter):
    """Adapter for the NHands clinical dataset format.

    NHands data is expected as a JSON file containing a list of patient encounter
    records with fields like patient_id, demographics, complaints, history, etc.
    """

    def load_raw_data(self) -> List[Dict[str, Any]]:
        path = Path(self.source_path)
        if path.suffix == ".jsonl":
            records = []
            with open(path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        records.append(json.loads(line))
            return records
        else:
            with open(path, "r") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and "records" in data:
                return data["records"]
            if isinstance(data, dict) and "patients" in data:
                return data["patients"]
            return [data]

    def normalize_record(self, raw_record: Dict[str, Any]) -> PatientRecord:
        pid = raw_record.get("patient_id") or raw_record.get("id") or "unknown"
        name = raw_record.get("name") or raw_record.get("patient_name")

        age = raw_record.get("age")
        if age is not None:
            try:
                age = int(age)
            except (ValueError, TypeError):
                age = None

        sex = raw_record.get("sex") or raw_record.get("gender")
        chief_complaint = (
            raw_record.get("chief_complaint")
            or raw_record.get("complaint")
            or raw_record.get("reason_for_visit")
        )

        medical_history = raw_record.get("medical_history") or raw_record.get(
            "past_medical_history"
        )
        if isinstance(medical_history, str):
            medical_history = [h.strip() for h in medical_history.split(",")]

        medications = raw_record.get("current_medications") or raw_record.get(
            "medications"
        )
        if isinstance(medications, str):
            medications = [m.strip() for m in medications.split(",")]

        allergies = raw_record.get("allergies")
        if isinstance(allergies, str):
            allergies = [a.strip() for a in allergies.split(",")]

        vitals = raw_record.get("vitals") or raw_record.get("vital_signs")
        lab_results = raw_record.get("lab_results") or raw_record.get("labs")
        diagnoses = raw_record.get("diagnoses") or raw_record.get("diagnosis")
        if isinstance(diagnoses, str):
            diagnoses = [diagnoses]

        notes = raw_record.get("notes") or raw_record.get("clinical_notes")

        # Collect unmapped fields into extra
        known_keys = {
            "patient_id", "id", "name", "patient_name", "age", "sex", "gender",
            "chief_complaint", "complaint", "reason_for_visit",
            "medical_history", "past_medical_history",
            "current_medications", "medications", "allergies",
            "vitals", "vital_signs", "lab_results", "labs",
            "diagnoses", "diagnosis", "notes", "clinical_notes",
        }
        extra = {k: v for k, v in raw_record.items() if k not in known_keys}

        return PatientRecord(
            patient_id=str(pid),
            name=name,
            age=age,
            sex=sex,
            chief_complaint=chief_complaint,
            medical_history=medical_history,
            current_medications=medications,
            allergies=allergies,
            vitals=vitals,
            lab_results=lab_results,
            diagnoses=diagnoses,
            notes=notes,
            extra=extra if extra else None,
        )

    def build_scenario(self, record: PatientRecord, index: int) -> ClinicalScenario:
        scenario_id = f"clinical_{record.patient_id}_{index}"

        reason = record.chief_complaint or "General consultation"

        # Build patient context string for task instructions
        info_parts = []
        if record.name:
            info_parts.append(f"Your name is {record.name}.")
        if record.age:
            info_parts.append(f"You are {record.age} years old.")
        if record.sex:
            info_parts.append(f"Sex: {record.sex}.")
        if record.medical_history:
            info_parts.append(
                f"Your medical history includes: {', '.join(record.medical_history)}."
            )
        if record.current_medications:
            info_parts.append(
                f"You are currently taking: {', '.join(record.current_medications)}."
            )
        if record.allergies:
            info_parts.append(
                f"You have allergies to: {', '.join(record.allergies)}."
            )

        context = " ".join(info_parts) if info_parts else "No additional context."

        task_instructions = (
            f"You are a patient seeking medical attention. {context} "
            f"Your main concern is: {reason}. "
            f"Describe your symptoms and answer the clinician's questions based on your medical information."
        )

        # Build expected actions from record
        expected_actions = []
        if record.diagnoses:
            expected_actions.append(
                {
                    "action_id": f"find_patient_{index}",
                    "name": "find_patient_info",
                    "arguments": {"patient_id": record.patient_id},
                    "compare_args": ["patient_id"],
                }
            )

        nl_assertions = []
        if record.diagnoses:
            for diag in record.diagnoses:
                nl_assertions.append(
                    f"The clinician considered or discussed the diagnosis: {diag}"
                )
        if record.chief_complaint:
            nl_assertions.append(
                "The clinician addressed the patient's chief complaint"
            )

        return ClinicalScenario(
            scenario_id=scenario_id,
            patient=record,
            reason_for_call=reason,
            task_instructions=task_instructions,
            expected_actions=expected_actions if expected_actions else None,
            nl_assertions=nl_assertions if nl_assertions else None,
            difficulty="medium",
            clinical_domain=record.extra.get("department") if record.extra else None,
        )
