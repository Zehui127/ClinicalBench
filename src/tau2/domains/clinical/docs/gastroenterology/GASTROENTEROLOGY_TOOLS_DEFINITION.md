# Gastroenterology Department - Clinical Tools Definition

> **⚠️ MEDICAL EXPERT REVIEW REQUIRED**
> This document contains clinical tool definitions that require validation by board-certified gastroenterologists. All medical guidelines, reference ranges, and clinical decision points should be verified against current ACG (American College of Gastroenterology) and AGA (American Gastroenterological Association) guidelines.

---

## 1. Patient Information Tools

### 1.1 Get Patient by MRN
- **Purpose**: Retrieve patient demographic and clinical information
- **Input**: Medical Record Number (MRN)
- **Output**: Patient demographics, diagnoses, medications, chief complaint, GI symptoms
- **Clinical Use**: Initial patient identification and history gathering
- **Validation Required**: ✓ Data fields completeness

---

## 2. Gastrointestinal Assessment Tools

### 2.1 Liver Function Assessment Tool

**Function**: `get_patient_liver_function(patient_id)`

**Purpose**: Retrieve and interpret liver function test results

**Lab Components**:
| Parameter | Normal Range | Clinical Significance |
|-----------|--------------|----------------------|
| ALT (SGPT) | 7-56 U/L | Hepatocellular damage |
| AST (SGOT) | 10-40 U/L | Hepatocellular/muscle damage |
| Alkaline Phosphatase | 45-117 U/L | Cholestatic injury |
| Bilirubin (Total) | 0.3-1.2 mg/dL | Excretory function |
| Albumin | 3.5-5.0 g/dL | Synthetic function |
| INR | 0.9-1.1 | Synthetic function |

**Interpretation Patterns**:

**ALT Elevation Patterns**:
| ALT Level | Interpretation | Common Causes |
|-----------|---------------|---------------|
| <1.5× ULN | Mild elevation | Fatty liver, medication effect |
| 1.5-10× ULN | Moderate elevation | Viral hepatitis, NAFLD |
| >10× ULN | Marked elevation | Ischemic hepatitis, toxin, viral |

**AST:ALT Ratio**:
- AST:ALT > 2:1 → Alcoholic liver disease, cirrhosis
- AST:ALT ~1:1 → Viral hepatitis, NAFLD
- AST:ALT <1 → Non-alcoholic fatty liver disease

**Bilirubin Elevation**:
| Pattern | Interpretation |
|---------|---------------|
| Unconjugated (indirect) ↑ | Hemolysis, Gilbert's |
| Conjugated (direct) ↑ | Obstruction, hepatitis |
| Mixed | Various liver disease |

**⚠️ Medical Review Required**:
- [ ] Verify all normal ranges (lab-specific variations)
- [ ] Confirm AST:ALT ratio interpretation
- [ ] Validate pattern recognition algorithms
- [ ] Consider gender-specific ALT thresholds
- [ ] Pediatric normal ranges

---

### 2.2 Liver Fibrosis Assessment Tool (APRI Score)

**Function**: `assess_liver_fibrosis(alt, ast, platelets)`

**Purpose**: Assess liver fibrosis using AST-to-Platelet Ratio Index

**Formula**:
```
APRI = [(AST / ULN_AST) × 100] / Platelet count (×10^9/L)

Where:
- ULN_AST = 40 U/L (upper limit of normal)
- Platelet count in ×10^9/L
```

**APRI Interpretation**:
| APRI Score | Fibrosis Stage | Interpretation |
|------------|----------------|----------------|
| < 0.5 | F0-F1 | Significant fibrosis unlikely |
| 0.5 - <1.0 | F1-F2 | Intermediate fibrosis possible |
| 1.0 - <1.5 | F2-F3 | Significant fibrosis likely |
| ≥ 1.5 | F3-F4 | Cirrhosis likely |

**Clinical Utility**:
- Screening test to identify patients who may need:
  - Further fibrosis assessment (FibroScan, liver biopsy)
  - Referral to hepatology
  - HCC surveillance if advanced fibrosis

**Limitations**:
- Less accurate in certain conditions (acute hepatitis, extrahepatic cholestasis)
- Platelet count affected by many factors
- Not validated for all liver diseases

**⚠️ Medical Review Required**:
- [ ] Verify APRI thresholds for fibrosis stages
- [ ] Confirm appropriate use cases
- [ ] Consider adding FIB-4 score as alternative
- [ ] Validate against current AASLD/AGA guidelines

---

### 2.3 Anemia Assessment Tool

**Function**: `evaluate_anemia(hemoglobin, age, gender)`

**Purpose**: Evaluate anemia severity and provide initial interpretation

**WHO Anemia Thresholds**:
| Population | Hb Threshold (g/dL) | Mild | Moderate | Severe |
|------------|---------------------|------|----------|--------|
| Adult Men | <13.0 | 11.0-12.9 | 8.0-10.9 | <8.0 |
| Adult Women (non-pregnant) | <12.0 | 11.0-11.9 | 8.0-10.9 | <8.0 |
| Pregnant Women | <11.0 | 10.0-10.9 | 7.0-9.9 | <7.0 |

**Anemia Classifications**:
- **Microcytic** (MCV <80): Iron deficiency, thalassemia, anemia of chronic disease
- **Normocytic** (MCV 80-100): Acute blood loss, hemolysis, renal failure, mixed
- **Macrocytic** (MCV >100): B12/folate deficiency, alcohol, liver disease, meds

**GI Causes of Anemia**:
- Iron deficiency: Celiac disease, IBD, gastritis, malignancy, GI bleeding
- B12 deficiency: Pernicious anemia, atrophic gastritis, Crohn's, bacterial overgrowth
- Chronic blood loss: Ulcers, vascular ectasia, malignancy, IBD

**Clinical Decision Points**:
- Mild: Consider iron studies, investigate cause
- Moderate: Full anemia workup + GI evaluation if iron deficient
- Severe: Urgent evaluation, consider transfusion if symptomatic

**Red Flags** (Urgent GI Referral):
- Hb <7 g/dL
- Iron deficiency with GI symptoms
- Positive FOBT/FIT
- Family history of GI malignancy
- Weight loss + anemia

**⚠️ Medical Review Required**:
- [ ] Verify WHO thresholds are appropriate
- [ ] Confirm MCV reference ranges
- [ ] Assess completeness of differential diagnosis
- [ ] Consider adding ferritin, iron, TIBC interpretation

---

## 3. Additional Recommended Tools

### 3.1 GI Bleeding Risk Assessment (Rockall Score)
- **Purpose**: Risk stratify upper GI bleeding
- **Components**: Age, shock, comorbidity, diagnosis, major stigmata
- **Score**: 0-11 (Low: 0-2, Moderate: 3-7, High: 8-11)
- **Status**: ⚠️ PENDING IMPLEMENTATION

### 3.2 Inflammatory Bowel Disease (IBD) Activity Assessment
- **Purpose**: Assess IBD disease activity
- **Tools**: Mayo Score (UC), CDAI (Crohn's)
- **Components**: Stool frequency, bleeding, endoscopy findings
- **Status**: ⚠️ PENDING IMPLEMENTATION

### 3.3 Celiac Disease Screening Tool
- **Purpose**: Determine when celiac serology is indicated
- **Indications**: Symptoms, risk factors, associated conditions
- **Tests**: tTG-IgA, total IgA, EMA
- **Status**: ⚠️ PENDING IMPLEMENTATION

### 3.4 H. pylori Management Tool
- **Purpose**: Test and treat H. pylori appropriately
- **Indications**: PUD, MALT lymphoma, idiopathic thrombocytopenia
- **Tests**: Urea breath test, stool antigen, biopsy
- **Treatment**: Triple/quadruple therapy based on resistance
- **Status**: ⚠️ PENDING IMPLEMENTATION

### 3.5 Pancreatitis Severity Assessment
- **Purpose**: Classify acute pancreatitis severity
- **Criteria**: Atlanta classification (mild, moderately severe, severe)
- **Scoring**: Ranson's, APACHE II, BISAP
- **Status**: ⚠️ PENDING IMPLEMENTATION

### 3.6 Colon Cancer Screening Tool
- **Purpose**: Determine appropriate colon cancer screening
- **Risk**: Average, increased, high
- **Modalities**: Colonoscopy, FIT, FIT-DNA, flexible sigmoidoscopy
- **Guidelines**: USPSTF, ACG, multi-society
- **Status**: ⚠️ PENDING IMPLEMENTATION

### 3.7 GERD Assessment Tool
- **Purpose**: Assess GERD symptoms and determine management
- **Classification**: Episodic, frequent, refractory
- **Complications**: Erosive esophagitis, Barrett's, stricture
- **Status**: ⚠️ PENDING IMPLEMENTATION

---

## 4. Clinical Workflow Integration

### Recommended Tool Usage Sequence:

1. **Initial Assessment**:
   - Get patient information
   - Document presenting GI symptoms

2. **Symptom-Specific Evaluation**:
   - Liver disease → Use LFT interpretation + APRI score
   - Anemia → Use anemia assessment + GI workup
   - GI bleed → Use bleeding risk assessment
   - IBD → Use disease activity tools
   - Dyspepsia → Consider H. pylori testing

3. **Risk Stratification**:
   - Red flag assessment (alarm symptoms)
   - Urgency determination
   - Specialist referral if needed

4. **Diagnostic Planning**:
   - Endoscopy decisions
   - Lab workup (LFTs, iron studies, celiac serology)
   - Imaging (CT, MRI, US) as indicated

5. **Management Planning**:
   - Acute symptom management
   - Chronic disease management
   - Preventive measures (screening)
   - Follow-up arrangements
   - Specialist referral

---

## 5. References (To Be Updated)

1. **ACG Guidelines** (Various)
   - Liver Disease
   - GI Bleeding
   - IBD
   - Celiac Disease
   - URL: [To be added]
   - Last verified: [DATE]

2. **AGA Guidelines** (Various)
   - Liver Fibrosis Assessment
   - Anemia in GI Practice
   - URL: [To be added]
   - Last verified: [DATE]

3. **AASLD Guidelines**
   - Liver Disease Management
   - URL: [To be added]
   - Last verified: [DATE]

---

## 6. Review Checklist

### For Gastroenterologist Reviewers:

- [ ] Verify all LFT normal ranges and interpretations
- [ ] Confirm APRI score thresholds
- [ ] Validate anemia assessment completeness
- [ ] Assess clinical appropriateness of recommendations
- [ ] Check for missing critical tools
- [ ] Review red flag lists for GI emergencies
- [ ] Update reference guidelines to most current versions
- [ ] Add any additional tools needed for clinical practice

### Specific Areas Requiring Expert Validation:

- [ ] LFTs: Are gender-specific thresholds needed?
- [ ] Fibrosis: Should we implement FIB-4 score in addition to APRI?
- [ ] Anemia: Should we include iron studies interpretation?
- [ ] GI bleed: Should we implement Glasgow-Blatchford score for lower GI bleed?
- [ ] Screening: Colon cancer screening algorithm?

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
