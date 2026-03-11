"""Clinical Tools for Neurology Domain"""

from typing import Optional, TYPE_CHECKING
from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool

if TYPE_CHECKING:
    from tau2.domains.clinical.neurology.environment import NeurologyDB


class NeurologyTools(ToolKitBase):
    """Clinical tools for neurology domain"""
    db: "NeurologyDB"

    def __init__(self, db: "NeurologyDB") -> None:
        super().__init__(db)

    @is_tool(ToolType.READ)
    def assess_stroke_risk(self, age: int, hypertension: bool, diabetes: bool, smoking: bool) -> dict:
        """
        Assess stroke risk using basic risk factors.

        Args:
            age: Patient age
            hypertension: Has hypertension
            diabetes: Has diabetes
            smoking: Current smoker

        Returns:
            Stroke risk assessment
        """
        risk_factors = 0
        if age >= 55:
            risk_factors += 1
        if hypertension:
            risk_factors += 1
        if diabetes:
            risk_factors += 1
        if smoking:
            risk_factors += 1

        if risk_factors == 0:
            risk_level = "Low"
            recommendation = "Continue healthy lifestyle"
        elif risk_factors <= 2:
            risk_level = "Moderate"
            recommendation = "Regular screening recommended"
        else:
            risk_level = "High"
            recommendation = "Comprehensive stroke prevention evaluation recommended"

        return {
            "risk_factors": risk_factors,
            "risk_level": risk_level,
            "recommendation": recommendation
        }

    @is_tool(ToolType.READ)
    def get_patient_by_mrn(self, mrn: str) -> dict:
        """Find patient by MRN"""
        for patient_id, patient in self.db.patients.items():
            if patient.patient_id == mrn:
                return {
                    "patient_id": patient.patient_id,
                    "name": patient.name,
                    "age": patient.age,
                    "gender": patient.gender,
                    "diagnoses": patient.diagnoses,
                    "chief_complaint": patient.chief_complaint,
                    "medications": patient.medications
                }
        raise ValueError(f"Patient with MRN {mrn} not found")

    @is_tool(ToolType.READ)
    def interpret_headache(self, location: str, severity: str, duration: str) -> dict:
        """
        Classify headache type based on characteristics.

        Args:
            location: Headache location (unilateral, bilateral, etc.)
            severity: Pain severity (mild, moderate, severe)
            duration: Duration (acute, chronic)

        Returns:
            Headache classification and recommendations
        """
        # Simple classification logic
        if location.lower() == "unilateral" and severity == "severe":
            classification = "Possible Migraine"
            recommendation = "Consider migraine-specific treatment"
        elif duration.lower() == "chronic" and location == "bilateral":
            classification = "Tension-type Headache"
            recommendation = "Consider stress management and analgesics"
        elif location.lower() == "around eye" and severity == "severe":
            classification = "Possible Cluster Headache"
            recommendation = "Urgent neurology evaluation recommended"
        else:
            classification = "Headache - unspecified"
            recommendation = "Further evaluation needed"

        return {
            "location": location,
            "severity": severity,
            "duration": duration,
            "classification": classification,
            "recommendation": recommendation
        }

    @is_tool(ToolType.READ)
    def evaluate_seizure(self, description: str, consciousness: bool) -> dict:
        """
        Evaluate seizure type based on description.

        Args:
            description: Seizure description
            consciousness: Whether consciousness was preserved

        Returns:
            Seizure type classification
        """
        if consciousness:
            seizure_type = "Focal Seizure (awareness retained)"
        else:
            if description and "convulsion" in description.lower():
                seizure_type = "Generalized Tonic-Clonic Seizure"
            else:
                seizure_type = "Focal Impaired Awareness Seizure"

        return {
            "description": description,
            "consciousness_preserved": consciousness,
            "seizure_type": seizure_type,
            "recommendation": "Neurology consultation and EEG recommended"
        }
