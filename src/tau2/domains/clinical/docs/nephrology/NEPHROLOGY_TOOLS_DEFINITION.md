# Nephrology Department - Clinical Tools Definition

> **⚠️ MEDICAL EXPERT REVIEW REQUIRED**
> This document contains clinical tool definitions that require validation by board-certified nephrologists. All medical guidelines, reference ranges, and clinical decision points should be verified against current KDIGO (Kidney Disease: Improving Global Outcomes) guidelines.

---

## 1. Patient Information Tools

### 1.1 Get Patient by MRN
- **Purpose**: Retrieve patient demographic and clinical information
- **Input**: Medical Record Number (MRN)
- **Output**: Patient demographics, diagnoses, CKD stage, medications, comorbidities, race
- **Clinical Use**: Initial patient identification and history gathering
- **Validation Required**: ✓ Data fields completeness (race important for eGFR calculation)

---

## 2. Renal Assessment Tools

### 2.1 eGFR Calculator Tool

**Function**: `calculate_egfr(creatinine, age, gender, race)`

**Purpose**: Calculate estimated Glomerular Filtration Rate using CKD-EPI 2009 formula

**Formula (CKD-EPI 2009)**:
```
eGFR = 141 × min(Scr/κ, 1)^α × max(Scr/κ, 1)^(-1.209) × 0.993^Age × [1.018 if female] × [1.212 if Black]

Where:
κ = 0.7 (females) or 0.9 (males)
α = -0.329 (females) or -0.411 (males)
Scr = serum creatinine (mg/dL)
```

**CKD Staging** (KDIGO 2012):
| Stage | eGFR (mL/min/1.73m²) | Description |
|-------|----------------------|-------------|
| 1 | ≥90 | Normal or increased (with kidney damage) |
| 2 | 60-89 | Mildly decreased |
| 3a | 45-59 | Mild to moderately decreased |
| 3b | 30-44 | Moderately to severely decreased |
| 4 | 15-29 | Severely decreased |
| 5 | <15 | Kidney failure |

**Clinical Decision Points**:
- Stage 1-2: Monitor, slow progression, CV risk reduction
- Stage 3a: Evaluate complications, consider referral
- Stage 3b: Refer to nephrology, manage complications
- Stage 4: Nephrology referral required, prepare for RRT
- Stage 5: Kidney replacement therapy evaluation

**⚠️ Medical Review Required**:
- [ ] Verify CKD-EPI 2009 formula is current standard
- [ ] Confirm appropriateness of race coefficient (current debate)
- [ ] Validate staging thresholds per KDIGO
- [ ] Consider alternative formulas (MDRD, cystatin C)
- [ ] Special populations (pregnancy, extremes of age, amputations)

---

### 2.2 Kidney Function Assessment Tool

**Function**: `get_patient_kidney_function(patient_id)`

**Purpose**: Retrieve comprehensive kidney function lab results

**Lab Components**:
| Parameter | Normal Range | Clinical Significance |
|-----------|--------------|----------------------|
| Creatinine | 0.6-1.2 mg/dL (varies) | Marker of filtration |
| eGFR | ≥90 mL/min/1.73m² | Overall kidney function |
| BUN | 7-20 mg/dL | Kidney excretory function |
| Potassium | 3.5-5.0 mEq/L | Electrolyte balance |
| Sodium | 135-145 mEq/L | Volume status |
| Albumin | ≥4.0 g/dL | Nutritional status |

**Abnormal Results Interpretation**:
- Elevated creatinine + decreased eGFR → AKI or CKD
- Elevated BUN:Creatinine ratio (>20:1) → Pre-renal cause
- Hyperkalemia (>5.5) → Arrhythmia risk, requires treatment
- Hyponatremia (<135) → Volume assessment needed
- Proteinuria/albuminuria → Kidney damage marker

**⚠️ Medical Review Required**:
- [ ] Verify all reference ranges
- [ ] Confirm interpretation algorithms
- [ ] Acute vs chronic kidney injury differentiation
- [ ] Proteinuria quantification methods

---

### 2.3 Medication Dose Adjustment Tool

**Function**: `adjust_medication_dose(medication_name, egfr, standard_dose)`

**Purpose**: Calculate renal dose adjustments based on kidney function

**Common Medications Requiring Adjustment**:

| Medication | eGFR Threshold | Adjustment | Notes |
|------------|---------------|------------|-------|
| Metformin | <30 | Contraindicated | Lactic acidosis risk |
| Lisinopril | <30 | 50% dose | Hyperkalemia monitoring |
| Furosemide | <20 | Higher dose needed | Resistance in CKD |
| Vancomycin | <50 | Extend interval | TDM required |
| DOACs | <30-50 | Dose reduce/avoid | Bleeding risk |
| Aminoglycosides | Any | Avoid or TDM | Nephrotoxic |
| NSAIDs | <60 | Avoid | AKI risk |
| Contrast dye | <45 | Hydration protocol | CIN prevention |

**Clinical Decision Points**:
- eGFR >60: Standard dosing typically appropriate
- eGFR 30-60: Review all medications for renal adjustment
- eGFR <30: Nephrology consultation recommended
- eGFR <15: Dialysis-dependent dosing considerations

**⚠️ Medical Review Required**:
- [ ] Verify all medication thresholds are current
- [ ] Add additional medications as needed
- [ ] Confirm specific dose adjustment recommendations
- [ ] Include geriatric considerations
- [ ] Pediatric dosing protocols

---

## 3. Additional Recommended Tools

### 3.1 AKI Detection Tool
- **Purpose**: Detect acute kidney injury using KDIGO criteria
- **Criteria**: Creatinine increase ≥0.3 mg/dL in 48h OR 1.5x baseline in 7 days
- **Staging**: Stage 1, 2, 3 based on creatinine/urine output
- **Status**: ⚠️ PENDING IMPLEMENTATION

### 3.2 Electrolyte Management Tool
- **Purpose**: Manage potassium, sodium, calcium, phosphorus abnormalities
- **Components**: Interpretation, treatment recommendations, monitoring
- **Emergency**: Hyperkalemia >6.5 or ECG changes
- **Status**: ⚠️ PENDING IMPLEMENTATION

### 3.3 Proteinuria Assessment Tool
- **Purpose**: Quantify and interpret proteinuria/albuminuria
- **Tests**: UACR, UPC, random protein/creatinine ratio
- **Categories**: A1 (<30), A2 (30-300), A3 (>300) mg/g
- **Status**: ⚠️ PENDING IMPLEMENTATION

### 3.4 Anemia in CKD Tool
- **Purpose**: Assess and manage anemia associated with CKD
- **Labs**: Hb, ferritin, TSAT, B12, folate
- **Treatment**: ESA considerations when Hb <10
- **Status**: ⚠️ PENDING IMPLEMENTATION

### 3.5 Mineral Bone Disorder (CKD-MBD) Tool
- **Purpose**: Manage calcium, phosphorus, PTH in CKD
- **Target ranges**: Vary by CKD stage
- **Treatment**: Phosphate binders, vitamin D analogs, calcimimetics
- **Status**: ⚠️ PENDING IMPLEMENTATION

### 3.6 Dialysis Readiness Assessment
- **Purpose**: Determine when to initiate kidney replacement therapy
- **Indications**: eGFR <15, uremic symptoms, refractory abnormalities
- **Modalities**: Hemodialysis, peritoneal dialysis, transplant
- **Status**: ⚠️ PENDING IMPLEMENTATION

### 3.7 Kidney Stone Risk Assessment
- **Purpose**: Assess risk of nephrolithiasis recurrence
- **Factors**: Stone composition, 24h urine, serum labs
- **Prevention**: Dietary modifications, medications
- **Status**: ⚠️ PENDING IMPLEMENTATION

---

## 4. Clinical Workflow Integration

### Recommended Tool Usage Sequence:

1. **Initial Assessment**:
   - Get patient information
   - Obtain kidney function labs (creatinine, eGFR, electrolytes)

2. **Kidney Function Evaluation**:
   - Calculate eGFR if not provided
   - Determine CKD stage
   - Assess for acute kidney injury

3. **Medication Review**:
   - Screen all medications for renal dosing
   - Adjust doses as needed
   - Identify nephrotoxins

4. **Complication Screening**:
   - Electrolyte abnormalities
   - Anemia
   - Mineral bone disorder
   - Proteinuria
   - Cardiovascular risk

5. **Management Planning**:
   - Slow CKD progression
   - Manage complications
   - Refer to nephrology if appropriate
   - Plan for kidney replacement therapy if Stage 4-5

---

## 5. References (To Be Updated)

1. **KDIGO Clinical Practice Guidelines** (2012-2023)
   - CKD Evaluation and Management (2013)
   - AKI (2012)
   - CKD-MBD (2017)
   - URL: https://kdigo.org/guidelines/
   - Last verified: [DATE]

2. **CKD-EPI Creatinine Equation** (2009)
   - URL: [To be added]
   - Last verified: [DATE]

3. **Drug Prescribing in CKD** (Various)
   - FDA prescribing information
   - Drug database references
   - Last verified: [DATE]

---

## 6. Review Checklist

### For Nephrologist Reviewers:

- [ ] Verify CKD-EPI formula accuracy and appropriateness
- [ ] Confirm CKD staging per KDIGO 2012
- [ ] Validate medication dosing thresholds
- [ ] Assess clinical appropriateness of recommendations
- [ ] Check for missing critical tools
- [ ] Review special population considerations
- [ ] Update reference guidelines to most current versions
- [ ] Address race coefficient controversy

### Specific Areas Requiring Expert Validation:

- [ ] eGFR: Should we implement cystatin C-based equation?
- [ ] Race coefficient: What is current recommendation?
- [ ] Medication dosing: Are thresholds evidence-based?
- [ ] AKI detection: Should we implement KDIGO AKI criteria?
- [ ] Referral criteria: At what CKD stage should referral occur?

### Reviewer Sign-off:

**Primary Reviewer**: _______________________ Date: _______
**Credentials**: _____________________________
**Specialty**: _______________________________
**Comments**: _______________________________

**Secondary Reviewer**: ___________________ Date: _______
**Credentials**: _____________________________
**Specialty**: _______________________________
**Comments**: _______________________________

---

**Document Version**: 1.0
**Last Updated**: 2025-03-09
**Next Review Date**: 2025-06-09
**Status**: ⚠️ AWAITING MEDICAL EXPERT REVIEW
