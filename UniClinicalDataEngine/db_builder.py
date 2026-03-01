"""Build db.json from clinical scenarios."""

from typing import Any, Dict, List

from UniClinicalDataEngine.models import ClinicalScenario


class ClinicalDBBuilder:
    """Builds a db.json dict from a list of ClinicalScenarios.

    The db.json structure mirrors the tau2-bench DB pattern:
    a dict of entity collections keyed by ID.
    """

    def build_db(self, scenarios: List[ClinicalScenario]) -> Dict[str, Any]:
        """Build a database dict from clinical scenarios.

        Args:
            scenarios: List of ClinicalScenarios.

        Returns:
            A dict suitable for serialization as db.json.
        """
        patients: Dict[str, Any] = {}
        encounters: Dict[str, Any] = {}

        for scenario in scenarios:
            patient = scenario.patient
            pid = patient.patient_id

            # Build patient entry
            patient_entry = {
                "patient_id": pid,
                "name": patient.name or "Unknown",
                "age": patient.age,
                "sex": patient.sex,
                "medical_history": patient.medical_history or [],
                "current_medications": patient.current_medications or [],
                "allergies": patient.allergies or [],
                "diagnoses": patient.diagnoses or [],
            }

            if patient.vitals:
                patient_entry["vitals"] = patient.vitals
            if patient.lab_results:
                patient_entry["lab_results"] = patient.lab_results

            patients[pid] = patient_entry

            # Build encounter entry
            encounter_id = scenario.scenario_id
            encounter_entry = {
                "encounter_id": encounter_id,
                "patient_id": pid,
                "chief_complaint": patient.chief_complaint or "",
                "notes": patient.notes or "",
                "status": "active",
                "prescriptions": [],
                "lab_orders": [],
                "recorded_diagnoses": [],
            }
            encounters[encounter_id] = encounter_entry

        return {
            "patients": patients,
            "encounters": encounters,
        }
