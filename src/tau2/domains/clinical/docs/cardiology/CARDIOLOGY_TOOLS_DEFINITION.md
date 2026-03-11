# Cardiology Department - Clinical Tools Definition

> **⚠️ MEDICAL EXPERT REVIEW REQUIRED**
> This document contains clinical tool definitions that require validation by board-certified cardiologists. All medical guidelines, reference ranges, and clinical decision points should be verified against current ACC/AHA guidelines.

---

## 1. Patient Information Tools

### 1.1 Get Patient by MRN
- **Purpose**: Retrieve patient demographic and clinical information
- **Input**: Medical Record Number (MRN)
- **Output**: Patient demographics, diagnoses, medications, chief complaint
- **Clinical Use**: Initial patient identification and history gathering
- **Validation Required**: ✓ Data fields completeness

---

## 2. Cardiovascular Assessment Tools

### 2.1 Blood Pressure Assessment Tool

**Function**: `assess_blood_pressure(systolic, diastolic, age)`

**Purpose**: Classify blood pressure according to ACC/AHA 2017 guidelines

**Reference Ranges**:
| Category | Systolic (mmHg) | Diastolic (mmHg) |
|----------|-----------------|------------------|
| Normal | < 120 | AND < 80 |
| Elevated | 120-129 | AND < 80 |
| Hypertension Stage 1 | 130-139 | OR 80-89 |
| Hypertension Stage 2 | ≥ 140 | OR ≥ 90 |
| Hypertensive Crisis | > 180 | AND/OR > 120 |

**Clinical Decision Points**:
- **Normal**: Lifestyle counseling, continue healthy habits
- **Elevated**: Lifestyle modification recommended (DASH diet, exercise, sodium reduction)
- **Stage 1**: Lifestyle changes + consider medication based on ASCVD risk
- **Stage 2**: Medication likely required (one or two drugs)
- **Crisis**: Immediate medical attention required, urgent evaluation

**⚠️ Medical Review Required**:
- [ ] Verify ACC/AHA 2017 guidelines currency
- [ ] Confirm decision points for different age groups
- [ ] Special populations considerations (pregnancy, diabetes, CKD)
- [ ] Pediatric BP norms (age, height, gender-specific)

---

### 2.2 QT Interval Correction Tool

**Function**: `calculate_qtc(qt_interval, heart_rate)`

**Purpose**: Calculate corrected QT interval using Bazett's formula

**Formula**: QTc = QT / √(RR interval)

**Reference Ranges**:
| QTc (ms) | Interpretation |
|----------|----------------|
| < 440 | Normal |
| 440-469 | Borderline |
| ≥ 470 (men), ≥ 480 (women) | Prolonged |

**Clinical Significance**:
- Prolonged QTc indicates increased risk of torsades de pointes
- Consider medication review (QT-prolonging drugs)
- Evaluate for electrolyte abnormalities (K+, Mg++)

**⚠️ Medical Review Required**:
- [ ] Verify Bazett's formula appropriateness (vs. Fridericia, Framingham)
- [ ] Confirm gender-specific thresholds
- [ ] Pediatric QTc considerations
- [ ] Special populations (bundle branch block, ventricular pacing)

---

### 2.3 Heart Rate Interpretation Tool

**Function**: `interpret_heart_rate(heart_rate, age)`

**Purpose**: Interpret heart rate based on age-appropriate norms

**Reference Ranges** (Resting Heart Rate):
| Age Group | Normal Range (bpm) |
|-----------|-------------------|
| < 1 year | 100-160 |
| 1-5 years | 80-120 |
| 6-11 years | 70-110 |
| ≥ 12 years | 60-100 |

**Classifications**:
- **Bradycardia**: Below normal range
- **Normal**: Within normal range
- **Tachycardia**: Above normal range

**Clinical Decision Points**:
- Bradycardia: Evaluate for sinus node dysfunction, AV block, medications
- Tachycardia: Assess for fever, anemia, hyperthyroidism, arrhythmia

**⚠️ Medical Review Required**:
- [ ] Verify age-specific ranges
- [ ] Activity level considerations (resting vs. exercise)
- [- ] Athlete's bradycardia considerations
- [ ] Medication effects on HR

---

## 3. Additional Recommended Tools

### 3.1 ASCVD Risk Calculator
- **Purpose**: 10-year atherosclerotic cardiovascular disease risk assessment
- **Inputs**: Age, sex, race, total cholesterol, HDL, SBP, hypertension treatment, smoking, diabetes
- **Output**: 10-year risk percentage, treatment recommendations
- **Guideline**: ACC/AHA 2018 Pooled Cohort Equations
- **Status**: ⚠️ PENDING IMPLEMENTATION

### 3.2 Chest Pain Risk Assessment (HEART Score)
- **Purpose**: Risk stratify patients with chest pain
- **Components**: History, ECG, Age, Risk factors, Troponin
- **Score**: 0-10 (Low risk: 0-3, Moderate: 4-6, High: 7-10)
- **Status**: ⚠️ PENDING IMPLEMENTATION

### 3.3 Heart Failure Classification
- **Purpose**: Classify heart failure by ACC/AHA stages and NYHA functional class
- **Stages**: A (at risk), B (structural), C (symptomatic), D (refractory)
- **Status**: ⚠️ PENDING IMPLEMENTATION

### 3.4 Lipid Panel Interpretation
- **Purpose**: Interpret lipid levels and assess cardiovascular risk
- **Components**: Total cholesterol, LDL, HDL, triglycerides
- **Guideline**: ACC/AHA 2018 Cholesterol Guidelines
- **Status**: ⚠️ PENDING IMPLEMENTATION

---

## 4. Clinical Workflow Integration

### Recommended Tool Usage Sequence:

1. **Initial Assessment**:
   - Get patient information
   - Assess vital signs (BP, HR)

2. **Risk Stratification**:
   - Calculate ASCVD risk (if applicable)
   - Review lipid panel

3. **Diagnostic Evaluation**:
   - ECG interpretation (QTc)
   - Arrhythmia assessment

4. **Treatment Planning**:
   - Blood pressure management
   - Lipid-lowering therapy
   - Lifestyle modifications

---

## 5. References (To Be Updated)

1. **ACC/AHA Hypertension Guidelines** (2017)
   - URL: https://doi.org/10.1161/HYP.0000000000000065
   - Last verified: [DATE]

2. **ACC/AHA Cholesterol Guidelines** (2018)
   - URL: https://doi.org/10.1161/CIR.0000000000000625
   - Last verified: [DATE]

3. **AHA/ACC/HRS Guideline for Evaluation and Management of Bradycardia** (2018)
   - URL: https://doi.org/10.1016/j.jacc.2018.10.044
   - Last verified: [DATE]

4. **AHA/ACC/HRS Guideline for Management of Patients With Atrial Fibrillation** (2023)
   - URL: https://doi.org/10.1016/j.jacc.2023.04.021
   - Last verified: [DATE]

---

## 6. Review Checklist

### For Cardiologist Reviewers:

- [ ] Verify all BP classification thresholds
- [ ] Confirm QTc calculation methodology
- [ ] Validate heart rate normal ranges
- [ ] Assess clinical appropriateness of recommendations
- [ ] Check for missing critical tools
- [ ] Review special population considerations
- [ ] Update reference guidelines to most current versions
- [ ] Add any additional tools needed for clinical practice

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
