"""
Clinical Tools for Gastroenterology Domain
Implements GI-related clinical tools
"""

from typing import Optional
from tau2.domains.clinical_gastroenterology.data_model import GastroenterologyDB, GILabResults
from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool


def _interpret_liver_enzymes(labs: GILabResults) -> str:
    """
    Interpret liver function test results.

    Args:
        labs: GI lab results containing liver enzymes

    Returns:
        Semicolon-separated interpretation string
    """
    interpretations = []

    if labs.liver_enzymes_alt:
        if labs.liver_enzymes_alt > 1000:
            interpretations.append("Markedly elevated ALT - possible acute liver injury")
        elif labs.liver_enzymes_alt > 3 * 40:  # Using 40 U/L as upper limit
            interpretations.append("Elevated ALT - consider hepatocellular damage")
        elif labs.liver_enzymes_alt > 40:
            interpretations.append("Mildly elevated ALT")

    if labs.liver_enzymes_ast:
        if labs.liver_enzymes_ast > labs.liver_enzymes_alt:
            interpretations.append("AST > ALT ratio - consider alcoholic liver disease")

    if labs.bilirubin and labs.bilirubin > 1.2:
        interpretations.append("Elevated bilirubin - consider hyperbilirubinemia")

    return "; ".join(interpretations) if interpretations else "Normal liver enzymes"


class GastroenterologyTools(ToolKitBase):
    """Clinical tools for gastroenterology domain"""

    db: GastroenterologyDB

    def __init__(self, db: GastroenterologyDB) -> None:
        super().__init__(db)

    @is_tool(ToolType.READ)
    def get_patient_liver_function(self, patient_id: str) -> dict:
        """
        Get patient's liver function tests.

        Args:
            patient_id: Patient identifier

        Returns:
            Patient's liver function data including ALT, AST, bilirubin, etc.
        """
        patient = self.db.get_patient(patient_id)
        if not patient:
            raise ValueError(f"Patient {patient_id} not found")

        if not patient.gi_lab_results:
            return {"error": "No liver function data available for this patient"}

        return {
            "patient_id": patient_id,
            "alt": patient.gi_lab_results.liver_enzymes_alt,
            "ast": patient.gi_lab_results.liver_enzymes_ast,
            "bilimbin": patient.gi_lab_results.bilirubin,
            "albumin": patient.gi_lab_results.albumin,
            "inr": patient.gi_lab_results.inr,
            "interpretation": _interpret_liver_enzymes(patient.gi_lab_results)
        }

    @is_tool(ToolType.READ)
    def get_patient_by_mrn(self, mrn: str) -> dict:
        """Find patient by Medical Record Number (MRN)."""
        for patient_id, patient in self.db.patients.items():
            if patient.patient_id == mrn:
                return {
                    "patient_id": patient.patient_id,
                    "name": patient.name,
                    "age": patient.age,
                    "gender": patient.gender,
                    "diagnoses": patient.diagnoses,
                    "chief_complaint": patient.chief_complaint,
                    "medications": patient.medications,
                    "comorbidities": patient.comorbidities
                }
        raise ValueError(f"Patient with MRN {mrn} not found")

    @is_tool(ToolType.READ)
    def evaluate_anemia(self, hemoglobin: float, age: int, gender: str) -> dict:
        """
        Evaluate anemia and provide interpretation.

        Args:
            hemoglobin: Hemoglobin level in g/dL
            age: Patient age
            gender: Patient gender

        Returns:
            Anemia evaluation with severity and recommendations
        """
        # Define anemia thresholds
        if gender.lower() == "female":
            mild = 11.0
            moderate = 8.0
            severe = 6.5
        else:
            mild = 13.0
            moderate = 10.0
            severe = 8.0

        if hemoglobin >= mild:
            severity = "normal"
            recommendation = "No anemia"
        elif hemoglobin >= moderate:
            severity = "mild"
            recommendation = "Mild anemia - consider iron studies"
        elif hemoglobin >= severe:
            severity = "moderate"
            recommendation = "Moderate anemia - investigate cause and consider treatment"
        else:
            severity = "severe"
            recommendation = "Severe anemia - urgent evaluation and treatment required"

        return {
            "hemoglobin": hemoglobin,
            "severity": severity,
            "threshold": mild,
            "recommendation": recommendation
        }

    @is_tool(ToolType.READ)
    def assess_liver_fibrosis(self, alt: float, ast: float, platelets: float) -> dict:
        """
        Assess liver fibrosis using APRI score (AST-to-Platelet Ratio Index).

        Args:
            alt: ALT level in U/L
            ast: AST level in U/L
            platelets: Platelet count in K/uL

        Returns:
            APRI score and fibrosis risk assessment
        """
        # Calculate APRI score
        apri = ((ast / alt) * 100) / platelets

        # Interpret APRI
        if apri < 0.5:
            fibrosis_risk = "Significant fibrosis unlikely"
            stage = "F0-F1"
        elif apri < 1.0:
            fibrosis_risk = "Intermediate fibrosis possible"
            stage = "F1-F2"
        elif apri < 1.5:
            fibrosis_risk = "Significant fibrosis likely"
            stage = "F2-F3"
        else:
            fibrosis_risk = "Cirrhosis likely"
            stage = "F3-F4"

        return {
            "apri_score": round(apri, 3),
            "fibrosis_stage": stage,
            "risk_assessment": fibrosis_risk,
            "interpretation": f"APRI score of {apri:.3f} suggests {fibrosis_risk} ({stage})"
        }


# Duplicate function removed - _interpret_liver_enzymes is already defined above at line 11
