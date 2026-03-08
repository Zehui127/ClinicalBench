"""
Clinical Tools for Nephrology Domain
Implements kidney-related clinical tools
"""

from typing import Optional
from tau2.domains.clinical_nephrology.data_model import NephrologyDB
from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool


class NephrologyTools(ToolKitBase):
    """Clinical tools for nephrology domain"""

    db: NephrologyDB

    def __init__(self, db: NephrologyDB) -> None:
        super().__init__(db)

    @is_tool(ToolType.READ)
    def calculate_egfr(
        self,
        creatinine: float,
        age: int,
        gender: str,
        race: Optional[str] = None
    ) -> dict:
        """
        Calculate estimated Glomerular Filtration Rate (eGFR) using CKD-EPI formula.

        Args:
            creatinine: Serum creatinine level in mg/dL
            age: Patient age in years
            gender: Patient gender ("male" or "female")
            race: Patient race (optional, for adjusted calculation)

        Returns:
            Dictionary with eGFR value, CKD stage, and interpretation
        """
        # CKD-EPI 2009 formula
        kappa = 0.7 if gender == "female" else 0.9
        alpha = -0.329 if gender == "female" else -0.411

        if gender == "female":
            creatinine_factor = 0.7
        else:
            creatinine_factor = 0.9

        # Calculate eGFR
        creatinine_kappa = creatinine ** kappa
        egfr = 141 * min(creatinine / creatinine_factor, 1.0) ** alpha \
                * max(creatinine / creatinine_factor, 1.0) ** -1.209 \
                * (0.993 ** age)

        if gender == "female":
            egfr *= 1.018
        if race and race.lower() == "black":
            egfr *= 1.212

        egfr = round(egfr, 1)

        # Determine CKD stage
        if egfr >= 90:
            ckd_stage = 1
            stage_desc = "Normal or increased"
        elif egfr >= 60:
            ckd_stage = 2
            stage_desc = "Mildly decreased"
        elif egfr >= 45:
            ckd_stage = "3a"
            stage_desc = "Mild to moderately decreased"
        elif egfr >= 30:
            ckd_stage = "3b"
            stage_desc = "Moderately to severely decreased"
        elif egfr >= 15:
            ckd_stage = 4
            stage_desc = "Severely decreased"
        else:
            ckd_stage = 5
            stage_desc = "Kidney failure"

        return {
            "egfr": egfr,
            "ckd_stage": ckd_stage,
            "stage_description": stage_desc,
            "interpretation": f"eGFR of {egfr} mL/min/1.73m² indicates {stage_desc} (Stage {ckd_stage})"
        }

    @is_tool(ToolType.READ)
    def get_patient_kidney_function(self, patient_id: str) -> dict:
        """
        Get patient's kidney function lab results.

        Args:
            patient_id: Patient identifier

        Returns:
            Patient's kidney function data including creatinine, eGFR, etc.
        """
        patient = self.db.get_patient(patient_id)
        if not patient:
            raise ValueError(f"Patient {patient_id} not found")

        if not patient.kidney_function:
            return {"error": "No kidney function data available for this patient"}

        return {
            "patient_id": patient_id,
            "creatinine": patient.kidney_function.creatinine,
            "egfr": patient.kidney_function.egfr,
            "bun": patient.kidney_function.bun,
            "potassium": patient.kidney_function.potassium,
            "sodium": patient.kidney_function.sodium,
            "albumin": patient.kidney_function.albumin,
            "ckd_stage": patient.ckd_stage
        }

    @is_tool(ToolType.WRITE)
    def adjust_medication_dose(
        self,
        medication_name: str,
        egfr: float,
        standard_dose: float
    ) -> dict:
        """
        Calculate adjusted medication dose based on kidney function.

        Args:
            medication_name: Name of the medication
            egfr: Patient's eGFR value in mL/min/1.73m²
            standard_dose: Standard dose in mg

        Returns:
            Adjusted dose with clinical recommendations
        """
        # Common renal dosing guidelines
        renal_meds = {
            "metformin": {
                "threshold": 30,
                "adjustment": 0.5,
                "warning": "Contraindicated if eGFR < 30"
            },
            "lisinopril": {
                "threshold": 30,
                "adjustment": 0.5,
                "warning": "Start at 50% dose if eGFR < 30"
            },
            "furosemide": {
                "threshold": 20,
                "adjustment": None,
                "warning": "May require higher doses for effect in severe CKD"
            },
            "vancomycin": {
                "threshold": 50,
                "adjustment": 0.75,
                "warning": "Dose adjustment needed if eGFR < 50"
            }
        }

        med_info = renal_meds.get(medication_name.lower())

        if not med_info:
            return {
                "medication": medication_name,
                "egfr": egfr,
                "standard_dose": standard_dose,
                "adjusted_dose": standard_dose,
                "recommendation": "No renal dose adjustment needed"
            }

        if egfr < med_info["threshold"]:
            if med_info["adjustment"]:
                adjusted_dose = standard_dose * med_info["adjustment"]
                return {
                    "medication": medication_name,
                    "egfr": egfr,
                    "standard_dose": standard_dose,
                    "adjusted_dose": round(adjusted_dose, 2),
                    "recommendation": med_info["warning"],
                    "action_required": "Dose adjustment needed"
                }
            else:
                return {
                    "medication": medication_name,
                    "egfr": egfr,
                    "standard_dose": standard_dose,
                    "adjusted_dose": standard_dose,
                    "recommendation": med_info["warning"],
                    "action_required": "Monitor renal function"
                }

        return {
            "medication": medication_name,
            "egfr": egfr,
            "standard_dose": standard_dose,
            "adjusted_dose": standard_dose,
            "recommendation": "No dose adjustment needed",
            "action_required": "None"
        }

    @is_tool(ToolType.READ)
    def get_patient_by_mrn(self, mrn: str) -> dict:
        """
        Find patient by Medical Record Number (MRN).

        Args:
            mrn: Medical Record Number

        Returns:
            Patient information
        """
        for patient_id, patient in self.db.patients.items():
            if patient.patient_id == mrn:
                return {
                    "patient_id": patient.patient_id,
                    "name": patient.name,
                    "age": patient.age,
                    "gender": patient.gender,
                    "race": patient.race,
                    "diagnoses": patient.diagnoses,
                    "ckd_stage": patient.ckd_stage,
                    "medications": patient.medications,
                    "comorbidities": patient.comorbidities
                }
        raise ValueError(f"Patient with MRN {mrn} not found")
