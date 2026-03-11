# Neurology Department - Clinical Tools Definition

> **⚠️ MEDICAL EXPERT REVIEW REQUIRED**
> This document contains clinical tool definitions that require validation by board-certified neurologists. All medical guidelines, reference ranges, and clinical decision points should be verified against current AAN (American Academy of Neurology) guidelines.

---

## 1. Patient Information Tools

### 1.1 Get Patient by MRN
- **Purpose**: Retrieve patient demographic and clinical information
- **Input**: Medical Record Number (MRN)
- **Output**: Patient demographics, diagnoses, medications, chief complaint, neuro exam findings
- **Clinical Use**: Initial patient identification and history gathering
- **Validation Required**: ✓ Data fields completeness

---

## 2. Neurological Assessment Tools

### 2.1 Stroke Risk Assessment Tool

**Function**: `assess_stroke_risk(age, hypertension, diabetes, smoking)`

**Purpose**: Basic stroke risk stratification using common risk factors

**Risk Factors Evaluated**:
| Factor | Points | Threshold |
|--------|--------|-----------|
| Age ≥ 55 | 1 | ≥ 55 years |
| Hypertension | 1 | Diagnosed or on treatment |
| Diabetes | 1 | Diagnosed or on treatment |
| Smoking | 1 | Current smoker |

**Risk Categories**:
- **Low** (0 factors): Continue healthy lifestyle
- **Moderate** (1-2 factors): Regular screening recommended, consider preventive measures
- **High** (3-4 factors): Comprehensive stroke prevention evaluation recommended

**Clinical Decision Points**:
- Low risk: Primary prevention counseling
- Moderate risk: Consider modifiable risk factor optimization
- High risk: Stroke specialist referral, consider carotid imaging if appropriate

**⚠️ Medical Review Required**:
- [ ] Verify against established stroke risk scores (CHA₂DS₂-VASc, ASCVD)
- [ ] Confirm age threshold appropriateness
- [ ] Additional risk factors (AFib, prior TIA, carotid stenosis)
- [ ] Link to comprehensive stroke risk calculator needed

---

### 2.2 Headache Classification Tool

**Function**: `interpret_headache(location, severity, duration)`

**Purpose**: Classify headache type based on clinical characteristics

**Classification Algorithm**:
```
Location + Severity + Duration → Classification
     │           │           │
     │           │           ├─ Acute: SAH, meningitis considerations
     │           │           │
     │           │           └─ Chronic: Migraine, tension, cluster
     │           │
     │           ├─ Severe: Migraine, cluster, SAH
     │           │
     │           └─ Mild-Moderate: Tension, sinus
     │
     └─ Unilateral: Migraine, cluster
     └─ Bilateral: Tension, etc.
```

**Headache Types**:
| Type | Location | Severity | Duration | Key Features |
|------|----------|----------|----------|--------------|
| Migraine | Unilateral | Severe | 4-72h | Nausea, photophobia, phonophobia |
| Tension | Bilateral | Mild-Mod | Chronic | Band-like pressure |
| Cluster | Unilateral/peri-orbital | Severe | 15-180min | Autonomic symptoms |
| SAH | Occipital/onset | "Worst" | Sudden | "Thunderclap" |
| Tension | Bilateral | Mild-Mod | Variable | Stress-related |

**Red Flags** (Specialist Referral Required):
- "Worst headache of my life"
- Sudden onset (<1 min to peak)
- Headache with fever, stiff neck
- New headache after age 50
- Pattern change
- Focal neurological deficits
- Papilledema

**⚠️ Medical Review Required**:
- [ ] Verify ICHD-3 classification criteria
- [ ] Confirm red flag list completeness
- [ ] Assessment of concussion/post-traumatic headache
- [ ] Medication overuse headache considerations

---

### 2.3 Seizure Classification Tool

**Function**: `evaluate_seizure(description, consciousness)`

**Purpose**: Classify seizure type based on clinical description

**Classification Framework** (ILAE 2017):

```
Focal Onset → Awareness Retained → Focal Aware Seizure
     │         │
     │         └─ Awareness Impaired → Focal Impaired Awareness Seizure
     │
     └─ Motor Onset → Automatisms, clonic, etc.
     └─ Non-Motor Onset → Autonomic, behavior, etc.

Generalized Onset → Motor → Tonic-Clonic, Clonic, Tonic, Atonic, Myoclonic
                  │
                  └─ Non-Motor → Absence (typical, atypical)

Unknown Onset
```

**Seizure Types**:
| Classification | Consciousness | Typical Features | EEG Correlation |
|----------------|---------------|------------------|-----------------|
| Focal Aware | Retained | Focal symptoms, aura | Focal onset |
| Focal Impaired | Lost | Automatisms, stare | Focal onset |
| Generalized Tonic-Clonic | Lost | Convulsion, postictal | Generalized spike-wave |
| Absence | Lost | Brief stare, no postictal | 3 Hz spike-wave |
| Atonic | Lost | Drop attacks | Generalized polyspike |

**Clinical Decision Points**:
- First seizure: Neuroimaging (MRI preferred), EEG
- Recurrent seizures: Consider EEG, neurology referral
- Red flags: Prolonged (>5 min), status epilepticus, postictal deficit
- Emergency: Status epilepticus, seizure with trauma

**⚠️ Medical Review Required**:
- [ ] Verify ILAE 2017 classification accuracy
- [ ] Confirm consciousness assessment methodology
- [ ] EEG interpretation protocols
- [ ] Emergency management guidelines
- [ ] Driving restrictions documentation

---

## 3. Additional Recommended Tools

### 3.1 Neurological Examination Tool
- **Purpose**: Document standardized neurological exam
- **Components**: Mental status, cranial nerves, motor, sensation, reflexes, coordination, gait
- **Score**: NIH Stroke Scale if applicable
- **Status**: ⚠️ PENDING IMPLEMENTATION

### 3.2 Dementia Screening Tool
- **Purpose**: Initial cognitive impairment screening
- **Tools**: MMSE, MoCA, SLUMS
- **Indications**: Memory complaints, age >65, cognitive decline
- **Status**: ⚠️ PENDING IMPLEMENTATION

### 3.3 Parkinson's Disease Assessment
- **Purpose**: Parkinsonian symptom assessment
- **Scale**: UPDRS (Unified Parkinson's Disease Rating Scale)
- **Features**: Resting tremor, bradykinesia, rigidity, postural instability
- **Status**: ⚠️ PENDING IMPLEMENTATION

### 3.4 Neuroimaging Decision Support
- **Purpose**: Appropriate neuroimaging selection
- **Clinical Scenarios**: Headache, stroke, TIA, dementia, seizure
- **Modalities**: CT, MRI, MRA, CTA, EEG
- **Status**: ⚠️ PENDING IMPLEMENTATION

### 3.5 TIA Risk Assessment (ABCD2 Score)
- **Purpose**: Stroke risk after TIA
- **Components**: Age, BP, Clinical features, Duration, Diabetes
- **Score**: 0-7 (Low: 0-3, Moderate: 4-5, High: 6-7)
- **Status**: ⚠️ PENDING IMPLEMENTATION

### 3.6 Lumbar Puncture Decision Support
- **Purpose**: Determine when LP is indicated
- **Indications**: Meningitis, SAH (if CT negative), Guillain-Barre, etc.
- **Contraindications**: Increased ICP, coagulopathy, infection at site
- **Status**: ⚠️ PENDING IMPLEMENTATION

---

## 4. Clinical Workflow Integration

### Recommended Tool Usage Sequence:

1. **Initial Assessment**:
   - Get patient information
   - Document presenting symptom

2. **Symptom-Specific Evaluation**:
   - Headache → Use headache classification
   - Seizure → Use seizure classification
   - Stroke/TIA → Use stroke risk + TIA assessment
   - Cognitive decline → Use dementia screening

3. **Risk Stratification**:
   - Red flag assessment
   - Urgency determination
   - Specialist referral if needed

4. **Diagnostic Planning**:
   - Neuroimaging decisions
   - EEG if seizure
   - Lab workup as indicated

5. **Management Planning**:
   - Acute symptom management
   - Preventive measures
   - Follow-up arrangements
   - Specialist referral

---

## 5. References (To Be Updated)

1. **AAN Guidelines - Stroke Prevention** (Latest)
   - URL: [To be added]
   - Last verified: [DATE]

2. **ICHD-3 Classification** (2018)
   - International Classification of Headache Disorders
   - URL: [To be added]
   - Last verified: [DATE]

3. **ILAE Seizure Classification** (2017)
   - International League Against Epilepsy
   - URL: [To be added]
   - Last verified: [DATE]

4. **AAN Guidelines - Dementia** (Latest)
   - URL: [To be added]
   - Last verified: [DATE]

---

## 6. Review Checklist

### For Neurologist Reviewers:

- [ ] Verify stroke risk factor accuracy
- [ ] Confirm headache classification per ICHD-3
- [ ] Validate seizure classification per ILAE 2017
- [ ] Assess clinical appropriateness of recommendations
- [ ] Check for missing critical tools
- [ ] Review red flag lists for completeness
- [ ] Update reference guidelines to most current versions
- [ ] Add any additional tools needed for clinical practice

### Specific Areas Requiring Expert Validation:

- [ ] Stroke risk: Should we implement CHA₂DS₂-VASc or ABCD2 score?
- [ ] Headache: Are concussion and medication overuse headache adequately addressed?
- [ ] Seizure: Should we include seizure first aid instructions?
- [ ] Neuroimaging: Should we develop imaging decision support?
- [ ] Dementia: Which screening tool is preferred (MMSE vs MoCA)?

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
