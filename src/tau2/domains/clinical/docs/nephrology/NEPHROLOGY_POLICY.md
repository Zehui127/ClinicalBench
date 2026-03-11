# Nephrology Department - Clinical Policy Document

> **⚠️ MEDICAL EXPERT REVIEW REQUIRED**
> This policy document defines clinical protocols and decision-making frameworks for nephrology consultations. All protocols must be validated by board-certified nephrologists and aligned with current KDIGO (Kidney Disease: Improving Global Outcomes) guidelines.

---

## Document Control

| Field | Value |
|-------|-------|
| **Department** | Nephrology |
| **Version** | 1.0 (Draft) |
| **Effective Date** | Pending Review |
| **Review Cycle** | Annually |
| **Approved By** | ⚠️ Pending |
| **Last Updated** | 2025-03-09 |

---

## 1. Clinical Philosophy & Scope

### 1.1 Mission Statement
The Nephrology Department provides evidence-based kidney consultation services using AI-assisted clinical decision support while maintaining physician oversight and patient safety as paramount priorities.

### 1.2 Scope of Practice
This policy covers:
- CKD evaluation, staging, and management
- AKI detection and initial management
- Electrolyte disorder management (K+, Na+, Ca++, Phos)
- Medication renal dose adjustment
- Kidney stone risk assessment
- Anemia management in CKD
- Mineral bone disorder (CKD-MBD) screening
- Dialysis planning and referral

**Out of Scope** (requires specialist referral):
- Dialysis prescription and management
- Kidney transplantation evaluation
- Complex glomerular diseases (biopsy required)
- Nephrotic syndrome management
- Vasculitis management (ANCA-associated)
- Pregnancy-related kidney disorders
- Pediatric nephrology (under 18 years)

### 1.3 Clinical Decision Support Principles
1. **Augmentation, Not Replacement**: AI tools support, not replace, clinical judgment
2. **Evidence-Based**: All recommendations grounded in current KDIGO guidelines
3. **Safety First**: When uncertain, recommend specialist consultation
4. **Transparency**: Clearly communicate tool limitations and confidence levels
5. **Documentation**: All tool use and recommendations must be documented

---

## 2. Patient Evaluation Protocols

### 2.1 Initial Consultation Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    PATIENT PRESENTATION                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: Gather Basic Information                           │
│  • Patient demographics (age, sex, race)                    │
│  • Chief complaint                                          │
│  • Medical history (HTN, DM, CVD)                           │
│  • Current medications                                      │
│  • Kidney function labs (creatinine, eGFR)                 │
│  • Electrolytes (K+, Na++, HCO3)                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: Kidney Function Assessment                         │
│  • Calculate eGFR using CKD-EPI                             │
│  • Determine CKD stage                                      │
│  • Assess for AKI                                           │
│  • Review urinalysis if available                           │
│  • Check for proteinuria                                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: Medication Review                                  │
│  • Screen for nephrotoxins (NSAIDs, ACEI/ARB, diuretics)   │
│  • Adjust doses based on eGFR                               │
│  • Identify drug interactions                               │
│  • Monitor for adverse effects                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 4: Complication Screening                             │
│  • Electrolyte abnormalities                                │
│  • Anemia                                                   │
│  • Mineral bone disorder                                    │
│  • Cardiovascular risk                                      │
│  • Proteinuria                                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 5: Formulate Management Plan                          │
│  • Slow CKD progression                                     │
│  • Manage complications                                     │
│  • Optimize medications                                     │
│  • Plan follow-up                                           │
│  • Refer to nephrology if indicated                        │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Mandatory Documentation Elements

Every consultation must include:
- [ ] Patient identifiers (de-identified for AI systems)
- [ ] Chief complaint and history
- [ ] Current kidney function (creatinine, eGFR, CKD stage)
- [ ] Electrolyte status
- [ ] Relevant medical history
- [ ] Current medications with dose adjustments
- [ ] All tools used with results
- [ ] Assessment and plan
- [ ] Patient education provided
- [ ] Follow-up arrangements
- [ ] Referral to nephrology (if applicable)

---

## 3. Clinical Protocols

### 3.1 CKD Evaluation and Management Protocol

**CKD Definition** (KDIGO 2012):
- Kidney damage (albuminuria, urine sediment, imaging, histology) OR
- eGFR <60 mL/min/1.73m² for >3 months

**CKD Staging**:
| Stage | eGFR | Description | Action |
|-------|------|-------------|--------|
| 1 | ≥90 | Normal/high with kidney damage | Risk reduction, slow progression |
| 2 | 60-89 | Mild decrease | Monitor, CV risk reduction |
| 3a | 45-59 | Mild-moderate decrease | Evaluate complications |
| 3b | 30-44 | Moderate-severe decrease | Refer to nephrology |
| 4 | 15-29 | Severe decrease | Nephrology referral, prepare for RRT |
| 5 | <15 | Kidney failure | Nephrology referral, RRT evaluation |

**Initial Workup** (New CKD):
```
Diagnosed CKD → Urinalysis → Proteinuria → Imaging → Referral Decision
                    │            │             │
                    │            │             ├─ Stage 1-2: Monitor, refer if
                    │            │             │  atypical, rapid progression
                    │            │             │
                    │            │             ├─ Stage 3a: Consider referral
                    │            │             │
                    │            │             ├─ Stage 3b: Refer to nephrology
                    │            │             │
                    │            │             └─ Stage 4-5: Urgent referral
                    │            │
                    ▼            ▼
              Hematuria      Nephrotic      Renal Ultrasound
              evaluation    range          (obstruction, cysts)
```

**Management Principles**:
- **Slow Progression**: BP control (<130/80 if albuminuria), ACEI/ARB if proteinuric, SGLT2i
- **Reduce CV Risk**: Statins, aspirin if indicated
- **Manage Complications**: Anemia, MBD, electrolytes, acidosis
- **Avoid Nephrotoxins**: NSAIDs, iodinated contrast (if possible)
- **Vaccinate**: Influenza, pneumococcal, hepatitis

**Referral Criteria** to Nephrology:
- eGFR <30 (Stage 4)
- Rapid eGFR decline (>5 mL/min/1.73m²/year)
- Albuminuria >300 mg/day or ACR >300 mg/g
- Uncontrolled hypertension (>140/90 despite 3+ drugs)
- Recurrent AKI
- Unexplained hematuria or proteinuria
- Pregnancy planning or pregnancy with CKD

**⚠️ Medical Review Required**:
- Verify KDIGO 2012 staging accuracy
- Confirm referral criteria
- Assess medication recommendations (ACEI/ARB, SGLT2i)

---

### 3.2 AKI Detection and Management Protocol

**AKI Definition** (KDIGO 2017):
```
Acute Kidney Injury = One of the following within 48 hours:
1. Creatinine increase ≥0.3 mg/dL (≥26.5 μmol/L)
2. Creatinine increase ≥1.5× baseline (within 7 days)
3. Urine output <0.5 mL/kg/h for 6 hours
```

**AKI Staging**:
| Stage | Creatinine | Urine Output | Action |
|-------|------------|--------------|--------|
| 1 | ↑1.5-1.9× or ↑0.3 mg/dL | <0.5 mL/kg/h for 6-12h | Identify cause, optimize volume |
| 2 | ↑2.0-2.9× | <0.5 mL/kg/h for ≥12h | Nephrology consult |
| 3 | ≥3.0× or ≥4.0 mg/dL | <0.3 mL/kg/h for ≥24h | Dialysis evaluation |

**AKI Etiology** (Pre-renal, Intrinsic, Post-renal):
```
AKI Diagnosed → Volume Status → Urinalysis → Urine Electrolytes → Etiology
                    │              │                │
                    │              │                ├─ Pre-renal: FE<Na <1%
                    │              │                │  (low perfusion)
                    │              │                │
                    │              │                ├─ Intrinsic: FE<Na >2%
                    │              │                │  (ATN, AIN, GN)
                    │              │                │
                    │              │                └─ Post-renal: obstruction
                    │              │
                    ▼              ▼
              JVP, Edema      Hematuria,
              Orthostatics    Proteinuria,
                             Granular casts
```

**Initial Management**:
- **Stop nephrotoxins**: NSAIDs, ACEI/ARB, diuretics
- **Optimize volume**: IV fluids if pre-renal, diuretics if volume overloaded
- **Correct electrolytes**: Potassium, sodium, calcium
- **Medication adjustment**: Dose based on eGFR
- **Nephrology consult**: Stage 2-3, unclear etiology, multisystem involvement

**Red Flags Requiring Urgent Nephrology Consult**:
- Anuria (<100 mL/day)
- Hyperkalemia >6.5 mEq/L or ECG changes
- Volume overload with respiratory compromise
- Severe metabolic acidosis
- Known or suspected glomerulonephritis
- Vasculitis

**⚠️ Medical Review Required**:
- Verify KDIGO 2017 AKI criteria
- Confirm initial management recommendations
- Assess nephrology consultation thresholds

---

### 3.3 Electrolyte Management Protocol

**Hyperkalemia** (K+ >5.0 mEq/L):
```
K+ Level → ECG Changes → Symptoms → Urgency → Treatment
    │            │           │          │
    │            │           │          ├─ >6.5 or ECG changes: EMERGENT
    │            │           │          │  • Calcium gluconate
    │            │           │          │  • Insulin + glucose
    │            │           │          │  • β-agonist
    │            │           │          │  • Dialysis if severe
    │            │           │          │
    │            │           │          ├─ 5.5-6.5, no ECG changes: URGENT
    │            │           │          │  • Stop K+ supplements, ACEI/ARB
    │            │           │          │  • Kayexalate or Patiromer
    │            │           │          │  • Loop diuretic if volume overloaded
    │            │           │          │
    │            ▼           ▼          └─ 5.0-5.5: Monitor
    │        Peaked T        │            • Repeat labs
    │        Widened QRS   Weakness      • Review medications
    ▼                        ↓
Asystole risk            Muscle weakness
```

**Hyponatremia** (Na+ <135 mEq/L):
- **Mild** (130-134): Often asymptomatic, assess cause
- **Moderate** (125-129): May have symptoms, treat underlying cause
- **Severe** (<125): Symptoms likely, urgent correction

**Correction Rate** (to avoid osmotic demyelination):
- Chronic hyponatremia: <8-10 mEq/L/day
- Acute hyponatremia: <1-2 mEq/L/hour until symptoms resolve or Na+ 130

**Disorders of Calcium and Phosphate**:
- **Hypercalcemia** (>10.5 mg/dL): Hydration, consider bisphosphonates
- **Hypocalcemia** (<8.5 mg/dL): Calcium gluconate if symptomatic
- **Hyperphosphatemia** (>4.5 mg/dL): Phosphate binders (CKD)

**⚠️ Medical Review Required**:
- Verify electrolyte thresholds
- Confirm treatment recommendations
- Assess correction rates for hyponatremia

---

### 3.4 Medication Dose Adjustment Protocol

**Principles**:
1. Screen all medications when eGFR <60 mL/min/1.73m²
2. Use eGFR not creatinine for dosing decisions
3. Consider patient factors (age, weight, concurrent illness)
4. Monitor for adverse effects
5. Adjust dose, frequency, or avoid medication

**Common Medications Requiring Adjustment**:

| Medication | eGFR Threshold | Adjustment | Notes |
|------------|---------------|------------|-------|
| **DOACs** | <50 | Dose reduce/avoid | Bleeding risk |
| **Direct Oral Anticoagulants** | | | |
| Apixaban | <25 | 2.5 mg BID | Avoid if <15 |
| Rivaroxaban | <15 | Avoid | |
| Dabigatran | <30 | 75 mg BID | Avoid if <15 |
| Edoxaban | <15-95 | 30 mg daily | |
| **Antibiotics** | | | |
| Nitrofurantoin | <30 | Avoid | |
| Sulfamethoxazole/trimethoprim | <30 | Dose extend | |
| Vancomycin | <50 | Dose extend, TDM | |
| Aminoglycosides | Any | Avoid or TDM | Nephrotoxic |
| **Diabetes** | | | |
| Metformin | <30 | Contraindicated | Lactic acidosis risk |
| Sulfonylureas | <30 | Avoid | Hypoglycemia risk |
| SGLT2 inhibitors | <30 | Avoid | |
| Insulin | Any | Dose reduce | CKD changes sensitivity |
| **Cardiovascular** | | | |
| ACEI/ARB | <30 | Dose reduce/hold | Hyperkalemia risk |
| Spironolactone | <30 | Avoid | Hyperkalemia risk |
| Eplerenone | <30 | Avoid | |
| Digoxin | <50 | Dose reduce | Narrow therapeutic |
| **Analgesics** | | | |
| NSAIDs | <60 | Avoid | AKI risk |
| Opioids | <30 | Dose reduce | Accumulation |
| **Other** | | | |
| Allopurinol | <30 | Dose reduce | |
| Colchicine | <30 | Dose reduce | |
| Gabapentin | <60 | Dose reduce | Sedation |

**Red Flags** (Nephrology Consult):
- eGFR <30 and patient on multiple renally-cleared meds
- Medication toxicity suspected
- Unable to find appropriate dose adjustment
- Complex medication regimen

**⚠️ Medical Review Required**:
- Verify all medication thresholds
- Confirm specific dose adjustments
- Update with new medications as approved

---

## 4. Safety Protocols

### 4.1 Nephrological Emergencies

**Immediate Medical Attention Required**:
- Severe hyperkalemia (>6.5 or ECG changes)
- Anuria or severe oliguria
- Pulmonary edema from volume overload
- Severe metabolic acidosis
- Pericarditis or uremic symptoms (Stage 5)
- Rapidly rising creatinine (>2 mg/dL/day)

### 4.2 Tool Limitations & Fail-Safes

**All Tools Must Include**:
- Clear indication of confidence level
- Known limitations (acute vs chronic, special populations)
- When to recommend nephrology consultation
- Disclaimer that tools are advisory only

---

## 5. Quality Assurance

### 5.1 Tool Performance Monitoring

**Metrics to Track**:
- Tool usage frequency
- Nephrology referral rate
- AKI detection rate
- Medication adverse events
- Patient outcomes

### 5.2 Clinical Decision Review

**Random Chart Review**:
- 10% of consultations reviewed monthly
- Focus on: Appropriate referral, medication safety
- Standardized evaluation tool

---

## 6. References (To Be Updated)

1. **KDIGO Clinical Practice Guidelines** (2012-2023)
   - CKD Evaluation and Management (2013)
   - AKI (2012, 2017 update)
   - CKD-MBD (2017)
   - URL: https://kdigo.org/guidelines/
   - Last verified: [DATE]

---

## 7. Review & Approval

### Required Signatures

**Clinical Governance**:
- [ ] Medical Director Review
- [ ] Nephrology Section Chief Review
- [ ] Quality Improvement Committee Approval
- [ ] Legal Review

**Expert Review Panel**:
- [ ] Board-Certified Nephrologist #1
- [ ] Board-Certified Nephrologist #2
- [ ] Clinical Pharmacist (Renal dosing specialist)
- [ ] Primary Care Physician Representative

---

**⚠️ STATUS: AWAITING MEDICAL EXPERT REVIEW**

**Document Control**: This document is confidential and intended for use by authorized clinical personnel only.
