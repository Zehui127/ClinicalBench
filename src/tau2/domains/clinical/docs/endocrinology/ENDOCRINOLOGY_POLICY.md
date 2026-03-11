# Endocrinology Department - Clinical Policy Document

> **⚠️ MEDICAL EXPERT REVIEW REQUIRED**
> This policy document defines clinical protocols and decision-making frameworks for endocrinology consultations. All protocols must be validated by board-certified endocrinologists and aligned with current Endocrine Society, ADA (American Diabetes Association), and AACE (American Association of Clinical Endocrinologists) guidelines.

---

## Document Control

| Field | Value |
|-------|-------|
| **Department** | Endocrinology |
| **Version** | 1.0 (Draft) |
| **Effective Date** | Pending Review |
| **Review Cycle** | Annually |
| **Approved By** | ⚠️ Pending |
| **Last Updated** | 2025-03-09 |

---

## 1. Clinical Philosophy & Scope

### 1.1 Mission Statement
The Endocrinology Department provides evidence-based endocrine consultation services using AI-assisted clinical decision support while maintaining physician oversight and patient safety as paramount priorities.

### 1.2 Scope of Practice
This policy covers:
- Diabetes management (Type 1 and Type 2)
- Thyroid disorder evaluation and management
- Glucose and HbA1c interpretation
- Lipid management in diabetes
- Osteoporosis risk assessment
- Menopause management
- Basic reproductive endocrinology (PCOS)
- Calcium and phosphate disorders

**Out of Scope** (requires specialist referral):
- Complex diabetes technology (insulin pumps, CGM programming)
- Pediatric endocrinology (under 18 years)
- Pituitary and adrenal disorders
- Reproductive endocrinology and infertility
- Thyroid nodule FNA and management
- Complex bone disorders (osteomalacia, renal osteodystrophy)
- Endocrine tumor management
- Gender-affirming hormone therapy

### 1.3 Clinical Decision Support Principles
1. **Augmentation, Not Replacement**: AI tools support, not replace, clinical judgment
2. **Evidence-Based**: All recommendations grounded in current ADA/Endocrine Society guidelines
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
│  • Patient demographics (age, sex, BMI)                     │
│  • Chief complaint                                          │
│  • Present illness history                                  │
│  • Endocrine-specific history                               │
│  • Current medications                                      │
│  • Relevant labs (glucose, HbA1c, TSH, lipids)              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: Symptom-Specific Assessment                        │
│  • Hyperglycemia → Glucose/HbA1c interpretation             │
│  • Thyroid symptoms → TSH, free T4                          │
│  • Fatigue → Consider thyroid, diabetes, adrenal            │
│  • Weight change → Thyroid, diabetes, cortisol             │
│  • Bone health → Osteoporosis risk assessment               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: Risk Stratification                                │
│  • ASCVD risk assessment                                    │
│  • Diabetes complication screening                          │
│  • Red flag assessment                                      │
│  • Determine need for specialist referral                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 4: Formulate Management Plan                          │
│  • Acute symptom management                                 │
│  • Chronic disease management                               │
│  • Preventive measures                                      │
│  • Lifestyle modifications                                  │
│  • Follow-up planning                                       │
│  • Specialist referral if indicated                         │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Mandatory Documentation Elements

Every consultation must include:
- [ ] Patient identifiers (de-identified for AI systems)
- [ ] Chief complaint and symptom history
- [ ] Relevant endocrine history
- [ ] Current medications with doses
- [ ] All tools used with results
- [ ] Assessment and diagnosis
- [ ] Management plan
- [ ] Patient education provided
- [ ] Follow-up arrangements
- [ ] Referral to endocrinology (if applicable)

---

## 3. Clinical Protocols

### 3.1 Diabetes Management Protocol

**Diabetes Classification**:
```
Hyperglycemia → Fasting Glucose → HbA1c → Random Glucose → Classification
                    │               │              │
                    │               │              ├─ Type 1: C-peptide negative,
                    │               │              │  autoantibodies, young age
                    │               │              │
                    │               │              ├─ Type 2: C-peptide positive,
                    │               │              │  insulin resistance, adult
                    │               │              │
                    │               │              ├─ Gestational: pregnancy onset
                    │               │              │
                    │               │              ├─ Prediabetes: 100-125 fasting,
                    │               │              │  5.7-6.4% A1c
                    │               │              │
                    │               │              └─ Secondary: pancreatitis,
                    │               │                 medications, Cushing's
                    │               │
                    ▼               ▼              ▼
                 ≥126 mg/dL      ≥6.5%         ≥200 + symptoms
```

**A1c Targets** (Individualized):
| Patient Category | Target A1c | Rationale |
|------------------|------------|-----------|
| Most adults | <7.0% | Balance benefits and risks |
| Older adults (≥65) | <7.5-8.0% | Avoid hypoglycemia, life expectancy |
| Younger, healthy | <6.5% | Prevent complications |
| Pregnancy | <6.0-6.5% | Prevent fetal complications |
| Limited life expectancy | <8.0-8.5% | Avoid hypoglycemia, focus on comfort |

**Glucose Monitoring**:
- **Type 1**: Continuous glucose monitoring (CGM) preferred, or 4+ daily checks
- **Type 2 on insulin**: CGM or SMBG at least daily
- **Type 2 not on insulin**: SMBG as needed, consider periodic A1c
- **Hypoglycemia unawareness**: More frequent monitoring

**Medication Management** (Type 2):
```
New Diagnosis → Lifestyle + Metformin → A1c Check (3 months) → Escalation
                          │                  │
                          │                  ├─ At goal: Continue
                          │                  │
                          │                  ├─ Above goal: Add second agent
                          │                  │  • SGLT2 inhibitor (CVD/CKD)
                          │                  │  • GLP-1 RA (CVD/weight)
                          │                  │  • Sulfonylurea (cost issues)
                          │                  │  • Insulin (very high A1c)
                          │                  │
                          ▼                  ▼
                     Metformin          Individualized
                     First-line        Treatment
```

**Complication Screening**:
- **Annual**: Eye exam, foot exam, urine albumin, lipid panel, neuropathy testing
- **At diagnosis**: Comprehensive evaluation
- **Pregnancy planning**: Pre-conception counseling

**Red Flags** (Urgent Endocrinology Referral):
- Type 1 diabetes (new diagnosis)
- DKA or HHS (diabetic emergencies)
| - Severe hypoglycemia requiring assistance
- Uncontrolled diabetes (A1c >9% despite therapy)
- Diabetes complications (retinopathy, nephropathy, neuropathy)
- Pregnancy planning or pregnancy

**⚠️ Medical Review Required**:
- Verify A1c target recommendations
- Confirm medication escalation algorithm
- Assess complication screening recommendations

---

### 3.2 Thyroid Disorder Management Protocol

**Thyroid Function Testing Algorithm**:
```
Symptoms → TSH First-Line → Abnormal → Free T4 → Classification
              │                   │
              │                   ├─ Low TSH + High T4 → Primary Hyperthyroidism
              │                   ├─ Low TSH + Normal T4 → Subclinical Hyperthyroidism
              │                   ├─ High TSH + Low T4 → Primary Hypothyroidism
              │                   └─ High TSH + Normal T4 → Subclinical Hypothyroidism
              │
              ▼
          Normal TSH → Euthyroid (usually)
```

**Hypothyroidism Management**:
```
Diagnosed → Age <65 → Start Levothyroxine (1.6 mcg/kg/day)
    │           │
    │           └─ Age >65 → Start lower dose (25-50 mcg/day)
    │                           ↑ TSH >20 → Consider full dose
    │
    ▼
Retest TSH in 6-8 weeks → Adjust dose → Goal TSH 0.5-3.0
```

**Hyperthyroidism Management**:
- **Confirmatory Tests**: Free T4, T3, TSI (Graves'), TPOAb
- **Initial Treatment**: Beta-blocker for symptoms
- **Definitive Treatment**: Endocrinology referral for:
  - Antithyroid medications (methimazole, PTU)
  - Radioactive iodine ablation
  - Thyroidectomy (rare)

**Special Considerations**:
- **Pregnancy**: TSH targets differ (trimester-specific: 1st: <2.5, 2nd: <3.0, 3rd: <3.5)
- **Elderly**: Higher TSH may be acceptable (treat if >10)
- **Amiodarone**: Complex effects on thyroid function
- **Postpartum**: Screen for thyroiditis (6-12 weeks postpartum)

**Red Flags** (Urgent Endocrinology Referral):
- Thyroid storm (fever, tachycardia, altered mental status)
- Myxedema coma (hypothermia, bradycardia, altered mental status)
| - Pregnant with thyroid dysfunction
- New atrial fibrillation with thyroid dysfunction
- Goiter with compressive symptoms
- Thyroid nodule >1 cm with suspicious features

**⚠️ Medical Review Required**:
- Verify TSH normal ranges
- Confirm pregnancy-specific targets
- Assess treatment thresholds

---

### 3.3 Hypoglycemia Management Protocol

**Hypoglycemia Classification**:
| Level | Glucose (mg/dL) | Symptoms | Treatment |
|-------|-----------------|----------|-----------|
| Alert | 54-69 | Autonomic (tremor, sweating, palpitations) | Oral carbs (15-20g) |
| Clinically Significant | 40-54 | Neuroglycopenic (confusion, behavior change) | Oral carbs + recheck |
| Severe | <40 | Altered mental status, unconscious | Glucagon or IV dextrose |

**Hypoglycemia Management Algorithm**:
```
Low Glucose → Check Symptoms → Conscious? → Treatment
                       │            │
                       │            ├─ Yes → Oral carbs
                       │            │         • 15-20g fast-acting
                       │            │         • Recheck in 15 min
                       │            │         • Repeat if still low
                       │            │
                       │            └─ No → Glucagon (1mg IM/SC)
                       │                      or IV dextrose (50mL 50%)
                       │
                       ▼
               Identify Cause → Prevent Recurrence
```

**Common Causes**:
- **Too much diabetes medication**: Insulin, sulfonylureas
- **Delayed/missed meals**: Without medication adjustment
- **Exercise**: Without carbohydrate intake
- **Alcohol**: Impairs gluconeogenesis
- **Renal/hepatic dysfunction**: Altered medication clearance

**Prevention Strategies**:
- Adjust medication before exercise
- Eat carbohydrate before alcohol
- Frequent glucose monitoring
- Education on recognition and treatment
- Consider CGM with hypoglycemia alarms

**Red Flags** (Urgent Care):
- Repeated severe hypoglycemia
- Hypoglycemia unawareness
| - Hypoglycemia requiring emergency services
- Hypoglycemia causing injury (fall, accident)

**⚠️ Medical Review Required**:
- Verify hypoglycemia thresholds
- Confirm treatment recommendations
- Assess prevention strategies

---

## 4. Safety Protocols

### 4.1 Endocrine Emergencies

**Immediate Medical Attention Required**:
- Diabetic ketoacidosis (DKA): High glucose, ketones, acidosis
- Hyperosmolar hyperglycemic state (HHS): Very high glucose, dehydration
- Severe hypoglycemia requiring assistance
- Thyroid storm
- Myxedema coma
| - Adrenal crisis

### 4.2 Tool Limitations & Fail-Safes

**All Tools Must Include**:
- Clear indication of confidence level
- Known limitations (special populations, pregnancy)
- When to recommend endocrinology consultation
- Disclaimer that tools are advisory only

---

## 5. Quality Assurance

### 5.1 Tool Performance Monitoring

**Metrics to Track**:
- Tool usage frequency
- Endocrinology referral rate
- Hypoglycemia events
| - Patient outcomes (A1c control)
- User satisfaction scores

### 5.2 Clinical Decision Review

**Random Chart Review**:
- 10% of consultations reviewed monthly
- Focus on: Appropriate referral, medication safety
- Standardized evaluation tool

---

## 6. References (To Be Updated)

1. **ADA Standards of Care** (Annual)
   - Diabetes Management
   - URL: https://diabetesjournals.org/care/
   - Last verified: [DATE]

2. **ATA/AACE Hypothyroidism Guidelines** (Latest)
   - Thyroid Function Testing and Management
   - URL: [To be added]
   - Last verified: [DATE]

3. **Endocrine Society Guidelines** (Various)
   - Multiple endocrine conditions
   - URL: [To be added]
   - Last verified: [DATE]

---

## 7. Review & Approval

### Required Signatures

**Clinical Governance**:
- [ ] Medical Director Review
- [ ] Endocrinology Section Chief Review
- [ ] Quality Improvement Committee Approval
- [ ] Legal Review

**Expert Review Panel**:
- [ ] Board-Certified Endocrinologist #1
- [ ] Board-Certified Endocrinologist #2
- [ ] Certified Diabetes Educator (CDE)
- [ ] Primary Care Physician Representative

---

**⚠️ STATUS: AWAITING MEDICAL EXPERT REVIEW**

**Document Control**: This document is confidential and intended for use by authorized clinical personnel only.
