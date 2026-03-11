# Gastroenterology Department - Clinical Policy Document

> **⚠️ MEDICAL EXPERT REVIEW REQUIRED**
> This policy document defines clinical protocols and decision-making frameworks for gastroenterology consultations. All protocols must be validated by board-certified gastroenterologists and aligned with current ACG (American College of Gastroenterology) and AGA (American Gastroenterological Association) guidelines.

---

## Document Control

| Field | Value |
|-------|-------|
| **Department** | Gastroenterology |
| **Version** | 1.0 (Draft) |
| **Effective Date** | Pending Review |
| **Review Cycle** | Annually |
| **Approved By** | ⚠️ Pending |
| **Last Updated** | 2025-03-09 |

---

## 1. Clinical Philosophy & Scope

### 1.1 Mission Statement
The Gastroenterology Department provides evidence-based GI consultation services using AI-assisted clinical decision support while maintaining physician oversight and patient safety as paramount priorities.

### 1.2 Scope of Practice
This policy covers:
- Liver disease evaluation (LFT interpretation, fibrosis assessment)
- Anemia evaluation (iron deficiency, B12 deficiency)
- GI bleeding assessment (upper and lower)
- Inflammatory bowel disease (IBD) initial assessment
- Dyspepsia and GERD evaluation
- Celiac disease screening
- H. pylori testing and treatment
- Colon cancer screening

**Out of Scope** (requires specialist referral):
- Endoscopic procedures (EGD, colonoscopy)
- Advanced liver disease management (cirrhosis complications)
- IBD biologics and advanced therapies
- Complex pancreaticobiliary disease (ERCP)
- GI motility disorders (manometry, pH testing)
- capsule endoscopy interpretation
- pediatric GI (under 18 years)

### 1.3 Clinical Decision Support Principles
1. **Augmentation, Not Replacement**: AI tools support, not replace, clinical judgment
2. **Evidence-Based**: All recommendations grounded in current ACG/AGA guidelines
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
│  • GI symptom history                                       │
│  • Medical history (liver disease, anemia, IBD)             │
│  • Current medications                                      │
│  • Review of systems                                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: Symptom-Specific Assessment                        │
│  • Liver disease → LFTs, fibrosis scoring                   │
│  • Anemia → Iron studies, B12, folate, GI evaluation        │
│  • GI bleeding → Risk assessment, urgent vs routine         │
│  • Dyspepsia → H. pylori, PPI trial, alarm features        │
│  • Diarrhea → IBD vs functional, alarm features             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: Red Flag Assessment                                │
│  • Alarm features (weight loss, bleeding, anemia)           │
│  • Age threshold considerations                             │
│  • Family history of GI malignancy                          │
│  • Determine need for urgent evaluation/specialist         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 4: Formulate Management Plan                          │
│  • Symptom management                                       │
│  • Diagnostic testing recommendations                        │
│  • Empiric treatment (if appropriate)                       │
│  • Lifestyle modifications                                  │
│  • Follow-up planning                                       │
│  • Specialist referral if indicated                         │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Mandatory Documentation Elements

Every consultation must include:
- [ ] Patient identifiers (de-identified for AI systems)
- [ ] Chief complaint and symptom history
- [ ] Alarm feature assessment
- [ ] Relevant medical and surgical history
- [ ] Current medications
- [ ] All tools used with results
- [ ] Assessment and differential diagnosis
- [ ] Management plan
- [ ] Patient education provided
- [ ] Follow-up arrangements
- [ ] Referral to gastroenterology (if applicable)

---

## 3. Clinical Protocols

### 3.1 Liver Disease Evaluation Protocol

**LFT Interpretation Algorithm**:
```
Abnormal LFTs → Check ALT → Check AST → Check Alk Phos → Pattern Recognition
                    │            │              │
                    │            │              ├─ Hepatocellular: ALT/AST ↑↑
                    │            │              │
                    │            │              ├─ Cholestatic: Alk Phos ↑↑
                    │            │              │
                    │            │              └─ Mixed: Both elevated
                    │            │
                    ▼            ▼
              ALT/AST Ratio   Bilirubin
                Assessment    Assessment
```

**ALT Elevation Patterns**:
| ALT Level | Interpretation | Common Causes | Next Steps |
|-----------|---------------|---------------|------------|
| <1.5× ULN | Mild | Fatty liver, meds | Monitor, repeat LFTs |
| 1.5-10× ULN | Moderate | Viral hepatitis, NAFLD | Further workup |
| >10× ULN | Marked | Ischemic, toxic, viral | Urgent evaluation |

**AST:ALT Ratio**:
- >2:1 → Alcoholic liver disease, cirrhosis
- ~1:1 → Viral hepatitis, NAFLD
- <1 → Non-alcoholic fatty liver disease

**Liver Fibrosis Assessment** (APRI Score):
- APRI <0.5 → Significant fibrosis unlikely
- APRI 0.5-1.0 → Intermediate fibrosis possible
- APRI >1.0 → Significant fibrosis likely

**Management Principles**:
- **Abnormal LFTs**: Repeat in 2-3 months, evaluate for liver disease
- **Markedly elevated** (>5× ULN): Urgent gastroenterology referral
- **Fibrosis suspected**: Gastroenterology referral for further assessment

**Red Flags** (Urgent Referral):
- ALT or AST >1000 U/L
- Acute liver failure (INR elevation, encephalopathy)
| - Ascites or edema suggestive of cirrhosis
- New jaundice

**⚠️ Medical Review Required**:
- Verify ALT elevation thresholds
- Confirm AST:ALT ratio interpretation
- Assess APRI score thresholds

---

### 3.2 Anemia in GI Practice Protocol

**Anemia Evaluation Algorithm**:
```
Anemia Detected → Check MCV → Iron Studies → B12/Folate → GI Evaluation
                     │          │             │
                     │          │             ├─ Iron deficiency → GI blood loss
                     │          │             │
                     │          │             ├─ B12 deficiency → Malabsorption
                     │          │             │
                     │          │             └─ Normocytic → Chronic disease
                     │          │
                     ▼          ▼
              Cell Size   Iron Status
              (MCV)       (Ferritin, Iron, TIBC)
```

**Anemia Classifications**:
| Type | MCV (fL) | Ferritin | TIBC | Iron | Common GI Causes |
|------|----------|----------|------|------|------------------|
| Iron deficiency | <80 | Low | High | Low | Celiac, IBD, malignancy, bleeding |
| B12 deficiency | >100 | Normal | Normal | Normal | Atrophic gastritis, Crohn's |
| Chronic disease | 80-100 | Normal/High | Normal | Normal | IBD, cancer, chronic inflammation |
| Mixed | Variable | Low | High | Low | Combined deficiencies |

**Iron Deficiency Anemia Workup**:
```
Iron Deficiency → Age/Factors → Endoscopy Decision
                        │
                        ├─ <50, men, non-specific → Upper + lower endoscopy
                        │
                        ├─ Premenopausal women → Consider menstrual blood loss
                        │
                        ├─ >50 → Colonoscopy ± EGD
                        │
                        └─ GI symptoms → Targeted evaluation
```

**Red Flags** (Urgent GI Referral):
- Hb <7 g/dL
- Melena or hematochezia
- Positive FOBT/FIT
- Weight loss with anemia
- Family history of GI malignancy
- Iron deficiency with GI symptoms

**Management**:
- Identify and treat underlying cause
- Iron replacement (oral or IV)
- Treat H. pylori if present
- Treat IBD if present
- Celiac disease evaluation if indicated

**⚠️ Medical Review Required**:
- Verify anemia threshold values
- Confirm endoscopy decision criteria
- Assess iron replacement protocols

---

### 3.3 GI Bleeding Assessment Protocol

**GI Bleeding Classification**:
```
Bleeding Presentation → Upper vs Lower → Severity → Urgency → Management
                         │              │          │
                         │              │          ├─ Hemodynamic instability: EMERGENT
                         │              │          │  • ICU admission
                         │              │          │  • Fluid resuscitation
                         │              │          │  • Blood transfusion
                         │              │          │  • Urgent endoscopy
                         │              │          │
                         │              │          ├─ Significant bleeding: URGENT
                         │              │          │  • Hospital admission
                         │              │          │  • Specialist consultation
                         │              │          │  • Endoscopy within 24 hours
                         │              │          │
                         │              │          └─ Minor bleeding: Routine
                         │              │             • Outpatient evaluation
                         │              │             • Specialist referral
                         │              │
                         ▼              ▼
                       Source        Hemodynamic
                    (UGI vs LGI)      Stability
```

**Upper vs Lower GI Bleeding**:
| Feature | Upper GI | Lower GI |
|---------|----------|----------|
| Melena | ✓ | Rare |
| Hematochezia | Possible (massive) | ✓ |
| Hematemesis | ✓ | No |
| Blood per rectum | No | ✓ |
| Coffee grounds emesis | ✓ | No |

**Upper GI Bleeding Risk Stratification** (Rockall Score):
- Age, Shock, Comorbidity, Diagnosis, Major Stigmata
- Score 0-10
- High risk = urgent endoscopy, consider ICU

**Lower GI Bleeding Evaluation**:
- Colonoscopy (first-line)
- Tagged RBC scan (if bleeding not localized)
- Angiography/embolization (if active bleeding)

**Red Flags** (Emergency):
- Hemodynamic instability (SBP <100, HR >100)
- Active bleeding (vomiting blood, fresh rectal bleeding)
- Orthostatic hypotension
- Syncope
| - Coagulopathy (INR >1.5, platelets <50)
- signs of shock

**Management**:
- **Stabilize**: IV access, fluids, transfuse if needed
- **PPI** for upper GI bleeding (80 mg IV bolus)
- **Specialist consultation** for all significant bleeding
- **Endoscopy** after stabilization

**⚠️ Medical Review Required**:
- Verify bleeding risk assessment
- Confirm transfusion thresholds
- Assess specialist consultation criteria

---

## 4. Safety Protocols

### 4.1 GI Emergencies

**Immediate Medical Attention Required**:
- Acute GI bleeding with hemodynamic instability
- Severe abdominal pain (peritonitis signs)
- Acute liver failure
- Severe pancreatitis
| - Bowel obstruction or perforation
- Ingestion of caustic substances

### 4.2 Tool Limitations & Fail-Safes

**All Tools Must Include**:
- Clear indication of confidence level
- Known limitations
- When to recommend gastroenterology consultation
- Disclaimer that tools are advisory only

---

## 5. Quality Assurance

### 5.1 Tool Performance Monitoring

**Metrics to Track**:
- Tool usage frequency
- GI referral rate
- Red flag detection rate
- Patient outcomes
| - User satisfaction scores

### 5.2 Clinical Decision Review

**Random Chart Review**:
- 10% of consultations reviewed monthly
- Focus on: Red flag recognition, appropriate referrals
- Standardized evaluation tool

---

## 6. References (To Be Updated)

1. **ACG Guidelines** (Various)
   - Liver Disease, GI Bleeding, IBD, Celiac Disease
   - URL: [To be added]
   - Last verified: [DATE]

2. **AGA Guidelines** (Various)
   - Liver Fibrosis Assessment, Anemia
   - URL: [To be added]
   - Last verified: [DATE]

---

## 7. Review & Approval

### Required Signatures

**Clinical Governance**:
- [ ] Medical Director Review
- [ ] Gastroenterology Section Chief Review
- [ ] Quality Improvement Committee Approval
- [ ] Legal Review

**Expert Review Panel**:
- [ ] Board-Certified Gastroenterologist #1
- [ ] Board-Certified Gastroenterologist #2
- [ ] Primary Care Physician Representative
- [ ] Hematologist Representative (for anemia)

---

**⚠️ STATUS: AWAITING MEDICAL EXPERT REVIEW**

**Document Control**: This document is confidential and intended for use by authorized clinical personnel only.
