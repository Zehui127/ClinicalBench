"""Generic CSV clinical data adapter with configurable column mapping."""

import csv
from typing import Any, Dict, List, Optional

from UniClinicalDataEngine.adapters.base import BaseAdapter
from UniClinicalDataEngine.models import ClinicalScenario, PatientRecord


DEFAULT_COLUMN_MAPPING = {
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
}


class CSVAdapter(BaseAdapter):
    """Adapter for CSV clinical data files.

    Supports configurable column mapping via the `column_mapping` kwarg.
    The mapping is a dict from PatientRecord field names to CSV column names.
    """

    def __init__(self, source_path: str, **kwargs: Any):
        super().__init__(source_path, **kwargs)
        self.column_mapping: Dict[str, str] = kwargs.get(
            "column_mapping", DEFAULT_COLUMN_MAPPING
        )
        self.delimiter: str = kwargs.get("delimiter", ",")

    def load_raw_data(self) -> List[Dict[str, Any]]:
        records = []
        with open(self.source_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=self.delimiter)
            for row in reader:
                records.append(dict(row))
        return records

    def _get_field(
        self, raw: Dict[str, Any], field_name: str
    ) -> Optional[str]:
        """Get a field from a raw record using the column mapping."""
        col = self.column_mapping.get(field_name)
        if col is None:
            return None
        return raw.get(col)

    def _parse_list_field(
        self, raw: Dict[str, Any], field_name: str
    ) -> Optional[List[str]]:
        """Parse a comma-separated field into a list."""
        val = self._get_field(raw, field_name)
        if val is None or val.strip() == "":
            return None
        return [item.strip() for item in val.split(",") if item.strip()]

    def normalize_record(self, raw_record: Dict[str, Any]) -> PatientRecord:
        pid = self._get_field(raw_record, "patient_id") or f"csv_{id(raw_record)}"
        name = self._get_field(raw_record, "name")

        age_str = self._get_field(raw_record, "age")
        age = None
        if age_str:
            try:
                age = int(age_str)
            except (ValueError, TypeError):
                age = None

        sex = self._get_field(raw_record, "sex")
        chief_complaint = self._get_field(raw_record, "chief_complaint")
        medical_history = self._parse_list_field(raw_record, "medical_history")
        medications = self._parse_list_field(raw_record, "current_medications")
        allergies = self._parse_list_field(raw_record, "allergies")
        diagnoses = self._parse_list_field(raw_record, "diagnoses")
        notes = self._get_field(raw_record, "notes")

        # Collect unmapped columns into extra
        mapped_cols = set(self.column_mapping.values())
        extra = {k: v for k, v in raw_record.items() if k not in mapped_cols and v}

        return PatientRecord(
            patient_id=str(pid),
            name=name,
            age=age,
            sex=sex,
            chief_complaint=chief_complaint,
            medical_history=medical_history,
            current_medications=medications,
            allergies=allergies,
            diagnoses=diagnoses,
            notes=notes,
            extra=extra if extra else None,
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
