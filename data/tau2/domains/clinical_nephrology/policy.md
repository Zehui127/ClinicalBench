# Clinical Nephrology Domain Policy

## Overview
This domain specializes in kidney-related clinical tasks including:
- Glomerular Filtration Rate (eGFR) calculations using CKD-EPI formula
- Renal function assessment and Chronic Kidney Disease (CKD) staging
- Medication dose adjustments for renal impairment
- Nephrology consultations

## Clinical Guidelines
- **eGFR Calculation**: Use CKD-EPI 2009 formula with race adjustment for African American patients
- **CKD Staging**:
  - Stage 1: eGFR ≥90 (Normal or increased)
  - Stage 2: eGFR 60-89 (Mildly decreased)
  - Stage 3a: eGFR 45-59 (Mild to moderately decreased)
  - Stage 3b: eGFR 30-44 (Moderately to severely decreased)
  - Stage 4: eGFR 15-29 (Severely decreased)
  - Stage 5: eGFR <15 (Kidney failure)

## Renal Dosing Guidelines
Common medications requiring renal dose adjustment:
- **Metformin**: Contraindicated if eGFR <30
- **ACE Inhibitors (lisinopril)**: 50% dose if eGFR <30
- **Furosemide**: May require higher doses for effect in severe CKD
- **Vancomycin**: Dose adjustment if eGFR <50

## Available Tools
- `calculate_egfr(creatinine, age, gender, race)`: Calculate eGFR with CKD-EPI formula
- `get_patient_kidney_function(patient_id)`: Retrieve patient's kidney function data
- `adjust_medication_dose(medication_name, egfr, standard_dose)`: Calculate renal-adjusted doses
- `get_patient_by_mrn(mrn)`: Find patients by Medical Record Number

## Privacy Considerations
- Handle all patient data with confidentiality following HIPAA guidelines
