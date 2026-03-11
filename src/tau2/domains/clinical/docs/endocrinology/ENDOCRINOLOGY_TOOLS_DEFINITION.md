# Endocrinology Department - Clinical Tools Definition

> **⚠️ MEDICAL EXPERT REVIEW REQUIRED**
> This document contains clinical tool definitions that require validation by board-certified endocrinologists. All medical guidelines, reference ranges, and clinical decision points should be verified against current Endocrine Society, ADA (American Diabetes Association), and AACE (American Association of Clinical Endocrinologists) guidelines.

---

## 1. Patient Information Tools

### 1.1 Get Patient by MRN
- **Purpose**: Retrieve patient demographic and clinical information
- **Input**: Medical Record Number (MRN)
- **Output**: Patient demographics, diagnoses, medications, chief complaint
- **Clinical Use**: Initial patient identification and history gathering
- **Validation Required**: ✓ Data fields completeness

---

## 2. Endocrine Assessment Tools

### 2.1 Blood Glucose Interpretation Tool

**Function**: `interpret_blood_glucose(glucose, fasting)`

**Purpose**: Classify blood glucose levels according to ADA criteria

**Reference Ranges**:

**Fasting Glucose** (no caloric intake for ≥8 hours):
| Category | Glucose (mg/dL) | Implication |
|----------|-----------------|-------------|
| Hypoglycemia | <70 | Low blood sugar - immediate treatment |
| Normal | 70-99 | Normal fasting glucose |
| Impaired Fasting Glucose (Prediabetes) | 100-125 | Increased diabetes risk |
| Diabetes | ≥126 | Diagnostic of diabetes (confirm with repeat) |

**Random Glucose** (any time of day):
| Category | Glucose (mg/dL) | Implication |
|----------|-----------------|-------------|
| Hypoglycemia | <70 | Low blood sugar - immediate treatment |
| Normal | <140 | Normal random glucose |
| Hyperglycemia | ≥140 | Abnormal - further evaluation needed |

**Clinical Decision Points**:
- **Hypoglycemia**: Immediate glucose intake, assess cause (meds, fasting, alcohol)
- **Normal**: Continue routine screening
- **Prediabetes**: Lifestyle modification, metformin consideration, retest in 1 year
- **Diabetes**: Confirm with HbA1c or second glucose, initiate management

**Hypoglycemia Classification**:
| Level | Glucose (mg/dL) | Symptoms | Treatment |
|-------|-----------------|----------|-----------|
| Alert | 54-69 | Mild symptoms | Oral carbs |
| Clinically significant | 40-54 | Neuroglycopenic symptoms | Oral carbs + reassess |
| Severe | <40 | Altered mental status | Glucagon or IV dextrose |

**⚠️ Medical Review Required**:
- [ ] Verify ADA glucose thresholds are current
- [ ] Confirm hypoglycemia treatment protocols
- [ ] Assess pregnancy glucose thresholds
- [ ] Pediatric reference ranges

---

### 2.2 Hemoglobin A1c Interpretation Tool

**Function**: `interpret_hba1c(hba1c)`

**Purpose**: Classify HbA1c levels for diabetes diagnosis and management

**Reference Ranges** (ADA Guidelines):
| Category | A1c (%) | Estimated Average Glucose | Implication |
|----------|---------|--------------------------|-------------|
| Normal | <5.7 | 117 mg/dL | Normal glucose levels |
| Prediabetes | 5.7-6.4 | 117-137 mg/dL | Increased diabetes risk |
| Diabetes | ≥6.5 | ~140 mg/dL | Diagnostic of diabetes |

**A1c to Average Glucose Conversion** (ADAG formula):
```
eAG (mg/dL) = 28.7 × A1c - 46.7

Examples:
- A1c 5.0% → ~97 mg/dL
- A1c 6.0% → ~126 mg/dL
- A1c 7.0% → ~154 mg/dL
- A1c 8.0% → ~183 mg/dL
```

**Clinical Decision Points**:
- **Normal (<5.7%)**: Routine screening every 3 years
- **Prediabetes (5.7-6.4%)**:
  - Lifestyle modification (diet, exercise, weight loss)
  - Consider metformin if high-risk (BMI >35, <60 years, + other risk factors)
  - Rescreen annually
  - CV risk factor management

- **Diabetes (≥6.5%)**:
  - Confirm diagnosis (unless clear symptoms + random glucose ≥200)
  - Initiate comprehensive diabetes management
  - Individualize A1c target (generally <7.0%)
  - Screen for complications

**A1c Limitations** (causes of inaccurate results):
- Anemia, hemoglobinopathies, recent transfusion
- Pregnancy, CKD, liver disease
- Certain medications (HIV meds, erythropoietin)

**⚠️ Medical Review Required**:
- [ ] Verify A1c diagnostic thresholds
- [ ] Confirm eAG conversion formula
- [ ] Assess individualized A1c target considerations
- [ ] Review special populations (elderly, pregnancy, CKD)

---

### 2.3 Thyroid Function Interpretation Tool

**Function**: `interpret_thyroid(tsh, t4)`

**Purpose**: Classify thyroid function test results

**Reference Ranges** (lab-specific):
| Test | Normal Range | Units |
|------|--------------|-------|
| TSH | 0.4-4.0 | mIU/L |
| Free T4 | 0.8-1.8 | ng/dL |
| Free T3 | 2.3-4.2 | pg/mL |

**Classification Framework**:
```
TSH First-Line Testing → Abnormal → Check Free T4
     │                        │
     │                        ├─ Low TSH + High T4 → Primary Hyperthyroidism
     │                        ├─ Low TSH + Normal T4 → Subclinical Hyperthyroidism
     │                        ├─ High TSH + Low T4 → Primary Hypothyroidism
     │                        └─ High TSH + Normal T4 → Subclinical Hypothyroidism
     │
     └─ Normal TSH → Typically euthyroid (rare exceptions)
```

**Thyroid Conditions**:

| Condition | TSH | Free T4 | Clinical Features | Management |
|-----------|-----|---------|------------------|------------|
| Primary Hyperthyroidism | ↓ (<0.4) | ↑ (>1.8) | Tachycardia, weight loss, heat intolerance | Antithyroid meds, beta-blocker, RAI |
| Subclinical Hyperthyroidism | ↓ (<0.4) | Normal | Often asymptomatic | Monitor, consider treatment if persistent/risk factors |
| Primary Hypothyroidism | ↑ (>4.0) | ↓ (<0.8) | Fatigue, weight gain, cold intolerance | Levothyroxine replacement |
| Subclinical Hypothyroidism | ↑ (>4.0) | Normal | Often asymptomatic | Monitor if TSH 4-10; treat if >10 or symptoms |
| Secondary Hypothyroidism | Normal/Low | ↓ | Low | Pituitary evaluation |

**Special Considerations**:
- **Pregnancy**: TSH targets differ (trimester-specific)
- **Elderly**: Higher TSH may be acceptable (treat if >10)
- **Amiodarone**: Complex effects on thyroid function
- **Critical illness**: Sick euthyroid syndrome

**Clinical Decision Points**:
- **Overt hypothyroidism**: Start levothyroxine (1.6 mcg/kg/day)
- **Subclinical hypothyroidism (TSH 4-10)**:
  - <65 years, symptomatic, TPO Ab+: Consider treatment
  - >65 years: Monitoring often preferred
  - TSH >10: Treat regardless of age
- **Overt hyperthyroidism**: Endocrinology referral, antithyroid medication
- **Subclinical hyperthyroidism**: Monitor if TSH 0.1-0.4; treat if <0.1 or risk factors

**⚠️ Medical Review Required**:
- [ ] Verify TSH normal ranges (lab variation exists)
- [ ] Confirm pregnancy-specific TSH targets
- [ ] Validate treatment thresholds
- [ ] Consider adding T3 testing in certain scenarios
- [ ] Review thyroid antibody testing indications

---

## 3. Additional Recommended Tools

### 3.1 Diabetes Comprehensive Management Tool
- **Purpose**: Full diabetes management including medication, lifestyle, monitoring
- **Components**: Glucose targets, medication selection, complication screening
- **Guidelines**: ADA Standards of Care (annual)
- **Status**: ⚠️ PENDING IMPLEMENTATION

### 3.2 Insulin Dosing Calculator
- **Purpose**: Calculate insulin doses for initiation and titration
- **Types**: Basal, bolus, correctional, premixed
- **Considerations**: Weight, renal function, age, goals
- **Status**: ⚠️ PENDING IMPLEMENTATION

### 3.3 Lipid Management in Diabetes Tool
- **Purpose**: ASCVD risk assessment and statin therapy in diabetes
- **Risk**: Diabetes = high risk (age 40-75)
- **Intensity**: Moderate vs high-intensity statin based on risk
- **Status**: ⚠️ PENDING IMPLEMENTATION

### 3.4 Osteoporosis Assessment Tool
- **Purpose**: Assess fracture risk and need for DEXA
- **Tools**: FRAX, NOF guidelines
- **Indications**: Age >65 women, >70 men, risk factors
- **Status**: ⚠️ PENDING IMPLEMENTATION

### 3.5 Adrenal Insufficiency Assessment
- **Purpose**: Diagnose and manage adrenal insufficiency
- **Tests**: Morning cortisol, ACTH stimulation test
- **Management**: Glucocorticoid replacement, stress dosing
- **Status**: ⚠️ PENDING IMPLEMENTATION

### 3.6 Calcium/PTH Disorder Tool
- **Purpose**: Evaluate hypercalcemia and hypocalcemia
- **Tests**: Calcium, PTH, phosphorus, vitamin D
- **Conditions**: Hyperparathyroidism, hypoparathyroidism, vitamin D deficiency
- **Status**: ⚠️ PENDING IMPLEMENTATION

### 3.7 PCOS Diagnostic Tool
- **Purpose**: Diagnose polycystic ovary syndrome
- **Criteria**: Rotterdam (2 of 3): Oligo/anovulation, hyperandrogenism, polycystic ovaries
- **Exclusion**: Thyroid, hyperprolactinemia, adrenal
- **Status**: ⚠️ PENDING IMPLEMENTATION

### 3.8 Menopause Management Tool
- **Purpose**: Assess menopausal symptoms and hormone therapy
- **Symptoms**: Vasomotor, vaginal, sleep, mood
- **Treatment**: Lifestyle, non-hormonal, MHT consideration
- **Status**: ⚠️ PENDING IMPLEMENTATION

---

## 4. Clinical Workflow Integration

### Recommended Tool Usage Sequence:

1. **Initial Assessment**:
   - Get patient information
   - Document presenting endocrine symptoms

2. **Symptom-Specific Evaluation**:
   - Hyperglycemia symptoms → Use glucose/HbA1c interpretation
   - Thyroid symptoms → Use thyroid function interpretation
   - Fatigue → Consider thyroid, adrenal, diabetes evaluation
   - Weight change → Consider thyroid, diabetes, cortisol

3. **Laboratory Evaluation**:
   - Glucose (fasting, random, HbA1c)
   - Thyroid (TSH, free T4, T3 if indicated)
   - Additional labs as indicated (lipids, cortisol, etc.)

4. **Risk Stratification**:
   - ASCVD risk assessment
   - Microvascular complication screening
   - Red flag assessment

5. **Management Planning**:
   - Acute symptom management
   - Chronic disease management
   - Preventive measures
   - Specialist referral if needed
   - Patient education

---

## 5. References (To Be Updated)

1. **ADA Standards of Care** (Annual)
   - Diabetes Management
   - URL: https://diabetesjournals.org/care/
   - Last verified: [DATE]

2. **ATA/AACE Hypothyroidism Guidelines** (Latest)
   - Thyroid Function Testing
   - URL: [To be added]
   - Last verified: [DATE]

3. **Endocrine Society Clinical Practice Guidelines** (Various)
   - Multiple endocrine conditions
   - URL: [To be added]
   - Last verified: [DATE]

---

## 6. Review Checklist

### For Endocrinologist Reviewers:

- [ ] Verify glucose thresholds per ADA guidelines
- [ ] Confirm HbA1c diagnostic criteria
- [ ] Validate thyroid function interpretation
- [ ] Assess clinical appropriateness of recommendations
- [ ] Check for missing critical tools
- [ ] Review special population considerations (pregnancy, elderly, pediatric)
- [ ] Update reference guidelines to most current versions
- [ ] Add any additional tools needed for clinical practice

### Specific Areas Requiring Expert Validation:

- [ ] Glucose: Should we implement pre/post-prandial glucose interpretation?
- [ ] Diabetes: Should we add insulin dosing calculators?
- [ ] Thyroid: Should we include T3 testing algorithms?
- [ ] Lipids: Should we integrate lipid management in diabetes?
- [ ] Bone health: Should we implement osteoporosis risk assessment?

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
