"""Generic JSON/JSONL clinical data adapter with dot-path field mapping."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from UniClinicalDataEngine.adapters.base import BaseAdapter
from UniClinicalDataEngine.models import ClinicalScenario, PatientRecord


DEFAULT_FIELD_PATH_MAPPING = {
    "patient_id": "patient_id",
    "name": "name",
    "age": "age",
    "sex": "sex",
    "chief_complaint": "chief_complaint",
    "medical_history": "medical_history",
    "current_medications": "current_medications",
    "allergies": "allergies",
    "diagnoses": "diagnoses",
    "notes": "notes",
    "vitals": "vitals",
    "lab_results": "lab_results",
}


def _resolve_dot_path(obj: Any, path: str) -> Any:
    """Resolve a dot-separated path against a nested dict/list.

    Examples:
        _resolve_dot_path({"a": {"b": 1}}, "a.b") -> 1
        _resolve_dot_path({"a": [{"x": 1}]}, "a.0.x") -> 1
    """
    parts = path.split(".")
    current = obj
    for part in parts:
        if current is None:
            return None
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError):
                return None
        else:
            return None
    return current


class JSONAdapter(BaseAdapter):
    """Adapter for JSON or JSONL clinical data files.

    Supports configurable dot-path field mapping via the `field_path_mapping` kwarg.
    The mapping is a dict from PatientRecord field names to dot-separated paths
    into the raw JSON records.

    Optionally specify `records_path` to point to the array of records within
    a JSON file (e.g., "data.patients").
    """

    def __init__(self, source_path: str, **kwargs: Any):
        super().__init__(source_path, **kwargs)
        self.field_path_mapping: Dict[str, str] = kwargs.get(
            "field_path_mapping", DEFAULT_FIELD_PATH_MAPPING
        )
        self.records_path: Optional[str] = kwargs.get("records_path")

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

            if self.records_path:
                data = _resolve_dot_path(data, self.records_path)
                if data is None:
                    raise ValueError(
                        f"records_path '{self.records_path}' resolved to None"
                    )

            if isinstance(data, list):
                return data
            return [data]

    def _get_field(self, raw: Dict[str, Any], field_name: str) -> Any:
        """Resolve a field using the dot-path mapping."""
        path = self.field_path_mapping.get(field_name)
        if path is None:
            return None
        return _resolve_dot_path(raw, path)

    def _ensure_list(self, val: Any) -> Optional[List[str]]:
        """Coerce a value to a list of strings."""
        if val is None:
            return None
        if isinstance(val, list):
            return [str(v) for v in val]
        if isinstance(val, str):
            return [v.strip() for v in val.split(",") if v.strip()]
        return [str(val)]

    def normalize_record(self, raw_record: Dict[str, Any]) -> PatientRecord:
        pid = self._get_field(raw_record, "patient_id") or f"json_{id(raw_record)}"
        name = self._get_field(raw_record, "name")

        age = self._get_field(raw_record, "age")
        if age is not None:
            try:
                age = int(age)
            except (ValueError, TypeError):
                age = None

        sex = self._get_field(raw_record, "sex")
        chief_complaint = self._get_field(raw_record, "chief_complaint")
        medical_history = self._ensure_list(
            self._get_field(raw_record, "medical_history")
        )
        medications = self._ensure_list(
            self._get_field(raw_record, "current_medications")
        )
        allergies = self._ensure_list(self._get_field(raw_record, "allergies"))
        diagnoses = self._ensure_list(self._get_field(raw_record, "diagnoses"))
        notes = self._get_field(raw_record, "notes")
        if notes is not None:
            notes = str(notes)
        vitals = self._get_field(raw_record, "vitals")
        if vitals is not None and not isinstance(vitals, dict):
            vitals = {"raw": vitals}
        lab_results = self._get_field(raw_record, "lab_results")
        if lab_results is not None and not isinstance(lab_results, dict):
            lab_results = {"raw": lab_results}

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
        )

    def build_scenario(self, record: PatientRecord, index: int) -> ClinicalScenario:
        scenario_id = f"clinical_{record.patient_id}_{index}"
        reason = record.chief_complaint or "General consultation"

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

        expected_actions = []
        if record.patient_id:
            expected_actions.append(
                {
                    "action_id": f"find_patient_{index}",
                    "name": "find_patient_info",
                    "arguments": {"patient_id": record.patient_id},
                    "compare_args": ["patient_id"],
                }
            )

        nl_assertions = []
        if record.chief_complaint:
            nl_assertions.append(
                "The clinician addressed the patient's chief complaint"
            )
        if record.diagnoses:
            for diag in record.diagnoses:
                nl_assertions.append(
                    f"The clinician considered or discussed the diagnosis: {diag}"
                )

        return ClinicalScenario(
            scenario_id=scenario_id,
            patient=record,
            reason_for_call=reason,
            task_instructions=task_instructions,
            expected_actions=expected_actions if expected_actions else None,
            nl_assertions=nl_assertions if nl_assertions else None,
            difficulty="medium",
        )
