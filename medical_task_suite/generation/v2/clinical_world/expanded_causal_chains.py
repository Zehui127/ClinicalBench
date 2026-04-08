#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Expanded Causal Chains — Data-driven clinical reasoning supplements.

Extends the 13 curated chains in causal_graph.py to 40+ chains covering
common clinical diseases across all major organ systems.

Each chain uses probabilistic causal edges:
    relation_type: "risk_factor" (increases probability) or "causes" (direct mechanism)
    strength: effect size (0-1)
    confidence: evidence quality (0-1)
"""

from .causal_graph import CausalRelation

# ============================================================
# Expanded Causal Chains (40+)
# ============================================================

EXPANDED_CAUSAL_CHAINS = [
    # ---- Cardiovascular (expanded) ----
    CausalRelation("hypertension", "chronic kidney disease", "risk_factor",
                   strength=0.5, confidence=0.9, description="Nephrosclerosis → CKD"),
    CausalRelation("atrial fibrillation", "heart failure", "risk_factor",
                   strength=0.4, confidence=0.8, description="Tachycardia-mediated cardiomyopathy"),
    CausalRelation("heart failure", "atrial fibrillation", "risk_factor",
                   strength=0.4, confidence=0.8, description="Atrial remodeling from pressure overload"),
    CausalRelation("hyperlipidemia", "coronary artery disease", "risk_factor",
                   strength=0.7, confidence=0.95, description="Atherosclerosis progression"),
    CausalRelation("coronary artery disease", "stroke", "risk_factor",
                   strength=0.3, confidence=0.7, description="Shared atherosclerotic risk"),
    CausalRelation("hypertension", "atrial fibrillation", "risk_factor",
                   strength=0.5, confidence=0.85, description="LVH → atrial dilation"),
    CausalRelation("heart failure", "chronic kidney disease", "risk_factor",
                   strength=0.4, confidence=0.8, description="Renal hypoperfusion"),
    CausalRelation("stroke", "aspiration pneumonia", "risk_factor",
                   strength=0.4, confidence=0.85, description="Dysphagia → aspiration"),

    # ---- Endocrine (expanded) ----
    CausalRelation("type 2 diabetes", "coronary artery disease", "risk_factor",
                   strength=0.6, confidence=0.9, description="Diabetic macrovascular disease"),
    CausalRelation("type 2 diabetes", "stroke", "risk_factor",
                   strength=0.5, confidence=0.9, description="Diabetic cerebrovascular disease"),
    CausalRelation("hyperthyroidism", "osteoporosis", "risk_factor",
                   strength=0.4, confidence=0.8, description="Increased bone turnover"),
    CausalRelation("hypothyroidism", "hyperlipidemia", "risk_factor",
                   strength=0.5, confidence=0.85, description="Decreased LDL receptor activity"),
    CausalRelation("hypothyroidism", "heart failure", "risk_factor",
                   strength=0.3, confidence=0.7, description="Myxedema heart"),
    CausalRelation("type 2 diabetes", "retinopathy", "risk_factor",
                   strength=0.6, confidence=0.9, description="Diabetic microvascular disease"),

    # ---- Respiratory (expanded) ----
    CausalRelation("asthma", "pneumothorax", "risk_factor",
                   strength=0.2, confidence=0.7, description="Barotrauma from severe asthma"),
    CausalRelation("pneumonia", "pleural effusion", "risk_factor",
                   strength=0.3, confidence=0.8, description="Parapneumonic effusion"),
    CausalRelation("pneumonia", "sepsis", "causes",
                   strength=0.3, confidence=0.85, description="Bacterial dissemination"),
    CausalRelation("copd", "pneumonia", "risk_factor",
                   strength=0.5, confidence=0.85, description="Impaired lung defense"),
    CausalRelation("copd", "lung cancer", "risk_factor",
                   strength=0.3, confidence=0.8, description="Shared inflammatory pathway + smoking"),
    CausalRelation("sleep apnea", "hypertension", "risk_factor",
                   strength=0.5, confidence=0.85, description="Intermittent hypoxia → sympathetic activation"),
    CausalRelation("sleep apnea", "heart failure", "risk_factor",
                   strength=0.3, confidence=0.75, description="Pulmonary hypertension → RV strain"),

    # ---- GI (expanded) ----
    CausalRelation("cirrhosis", "hepatorenal syndrome", "causes",
                   strength=0.4, confidence=0.85, description="Splanchnic vasodilation → renal vasoconstriction"),
    CausalRelation("cirrhosis", "coagulopathy", "risk_factor",
                   strength=0.5, confidence=0.9, description="Decreased clotting factor synthesis"),
    CausalRelation("gerd", "esophageal stricture", "risk_factor",
                   strength=0.2, confidence=0.8, description="Chronic inflammation → fibrosis"),
    CausalRelation("pancreatitis", "type 2 diabetes", "risk_factor",
                   strength=0.3, confidence=0.8, description="Beta cell destruction"),
    CausalRelation("peptic ulcer disease", "gi bleeding", "causes",
                   strength=0.4, confidence=0.9, description="Ulcer erosion into vessel"),
    CausalRelation("inflammatory bowel disease", "colorectal cancer", "risk_factor",
                   strength=0.3, confidence=0.8, description="Chronic inflammation → dysplasia"),

    # ---- Neurological (expanded) ----
    CausalRelation("epilepsy", "aspiration pneumonia", "risk_factor",
                   strength=0.2, confidence=0.7, description="Post-ictal aspiration"),
    CausalRelation("migraine", "stroke", "risk_factor",
                   strength=0.2, confidence=0.7, description="Migrainous infarction (rare)"),
    CausalRelation("parkinson disease", "aspiration pneumonia", "risk_factor",
                   strength=0.4, confidence=0.8, description="Dysphagia from rigidity"),
    CausalRelation("parkinson disease", "depression", "risk_factor",
                   strength=0.4, confidence=0.85, description="Neurodegeneration of serotonergic pathways"),
    CausalRelation("stroke", "epilepsy", "risk_factor",
                   strength=0.3, confidence=0.8, description="Post-stroke seizures"),
    CausalRelation("multiple sclerosis", "bladder dysfunction", "risk_factor",
                   strength=0.5, confidence=0.85, description="Demyelination of spinal pathways"),
    CausalRelation("depression", "coronary artery disease", "risk_factor",
                   strength=0.3, confidence=0.7, description="Behavioral + physiological mechanisms"),

    # ---- Renal (expanded) ----
    CausalRelation("chronic kidney disease", "anemia", "risk_factor",
                   strength=0.5, confidence=0.9, description="Decreased EPO production"),
    CausalRelation("chronic kidney disease", "hyperlipidemia", "risk_factor",
                   strength=0.3, confidence=0.7, description="Altered lipid metabolism"),
    CausalRelation("chronic kidney disease", "osteoporosis", "risk_factor",
                   strength=0.3, confidence=0.8, description="Renal osteodystrophy"),
    CausalRelation("nephrolithiasis", "chronic kidney disease", "risk_factor",
                   strength=0.2, confidence=0.7, description="Recurrent obstruction + infection"),

    # ---- Hematologic (expanded) ----
    CausalRelation("deep vein thrombosis", "post-thrombotic syndrome", "risk_factor",
                   strength=0.4, confidence=0.8, description="Venous valve damage"),
    CausalRelation("anemia", "heart failure", "risk_factor",
                   strength=0.3, confidence=0.75, description="High-output state → cardiomyopathy"),

    # ---- Musculoskeletal (expanded) ----
    CausalRelation("osteoporosis", "fracture", "causes",
                   strength=0.7, confidence=0.95, description="Decreased bone mineral density"),
    CausalRelation("rheumatoid arthritis", "cardiovascular disease", "risk_factor",
                   strength=0.4, confidence=0.8, description="Chronic systemic inflammation"),
    CausalRelation("gout", "chronic kidney disease", "risk_factor",
                   strength=0.3, confidence=0.75, description="Urate nephropathy"),

    # ---- Infectious (expanded) ----
    CausalRelation("sepsis", "acute kidney injury", "causes",
                   strength=0.5, confidence=0.9, description="Hypoperfusion + inflammatory damage"),
    CausalRelation("sepsis", "acute respiratory distress syndrome", "causes",
                   strength=0.4, confidence=0.85, description="Systemic inflammatory response"),

    # ---- Metabolic syndrome chain ----
    CausalRelation("obesity", "type 2 diabetes", "risk_factor",
                   strength=0.6, confidence=0.9, description="Insulin resistance"),
    CausalRelation("obesity", "hypertension", "risk_factor",
                   strength=0.5, confidence=0.9, description="Increased sympathetic activity + volume"),
    CausalRelation("obesity", "sleep apnea", "risk_factor",
                   strength=0.6, confidence=0.9, description="Upper airway fat deposition"),
    CausalRelation("metabolic syndrome", "coronary artery disease", "risk_factor",
                   strength=0.6, confidence=0.85, description="Combined risk factor clustering"),
]


# ============================================================
# Expanded Differential Diagnosis Requirements (25+ diseases)
# ============================================================

EXPANDED_DIFFERENTIAL_REQS = {
    # ---- Original 12 (kept for completeness, may override) ----
    # These are already in causal_graph.py CURATED_DIFFERENTIAL_REQS

    # ---- New: Endocrine ----
    "hyperthyroidism": {
        "must_rule_out": ["anxiety disorder", "pheochromocytoma", "mania"],
        "must_support_with": ["lab", "history"],
        "should_investigate_cause": ["graves disease", "toxic nodule", "thyroiditis"],
        "complications_to_check": ["atrial fibrillation", "osteoporosis", "thyroid storm"],
    },
    "hypothyroidism": {
        "must_rule_out": ["depression", "chronic fatigue syndrome", "anemia"],
        "must_support_with": ["lab"],
        "should_investigate_cause": ["hashimoto thyroiditis", "iodine deficiency", "medication-induced"],
        "complications_to_check": ["hyperlipidemia", "myxedema", "heart failure"],
    },
    "hyperlipidemia": {
        "must_rule_out": ["hypothyroidism", "nephrotic syndrome", "medication-induced"],
        "must_support_with": ["lab", "history"],
        "should_investigate_cause": ["familial hypercholesterolemia", "dietary", "metabolic syndrome"],
        "complications_to_check": ["coronary artery disease", "pancreatitis", "xanthomas"],
    },

    # ---- New: GI ----
    "cirrhosis": {
        "must_rule_out": ["heart failure", "bud-chiari syndrome", "metastatic disease"],
        "must_support_with": ["lab", "imaging"],
        "should_investigate_cause": ["alcohol", "hepatitis B", "hepatitis C", "nafld"],
        "complications_to_check": ["variceal bleeding", "hepatic encephalopathy", "hepatorenal syndrome"],
    },
    "gerd": {
        "must_rule_out": ["coronary artery disease", "esophageal spasm", "peptic ulcer disease"],
        "must_support_with": ["history"],
        "should_investigate_cause": ["hiatal hernia", "obesity", "medications"],
        "complications_to_check": ["esophagitis", "barrett esophagus", "stricture"],
    },
    "pancreatitis": {
        "must_rule_out": ["cholecystitis", "perforated ulcer", "aortic dissection"],
        "must_support_with": ["lab", "imaging"],
        "should_investigate_cause": ["gallstones", "alcohol", "hypertriglyceridemia"],
        "complications_to_check": ["pancreatic necrosis", "pseudocyst", "ards"],
    },

    # ---- New: Neurological ----
    "epilepsy": {
        "must_rule_out": ["syncope", "pseudoseizure", "hypoglycemia", "tia"],
        "must_support_with": ["lab", "history"],
        "should_investigate_cause": ["structural lesion", "genetic", "metabolic"],
        "complications_to_check": ["status epilepticus", "aspiration", "sudep"],
    },
    "migraine": {
        "must_rule_out": ["tension headache", "cluster headache", "subarachnoid hemorrhage"],
        "must_support_with": ["history"],
        "should_investigate_cause": ["triggers", "hormonal", "family history"],
        "complications_to_check": ["medication overuse headache", "status migrainosus"],
    },
    "parkinson disease": {
        "must_rule_out": ["essential tremor", "drug-induced parkinsonism", "multiple system atrophy"],
        "must_support_with": ["history", "exam"],
        "should_investigate_cause": ["idiopathic", "genetic"],
        "complications_to_check": ["dysphagia", "depression", "dementia", "falls"],
    },

    # ---- New: Musculoskeletal ----
    "rheumatoid arthritis": {
        "must_rule_out": ["osteoarthritis", "gout", "lupus", "psoriatic arthritis"],
        "must_support_with": ["lab", "imaging"],
        "should_investigate_cause": ["autoimmune", "genetic"],
        "complications_to_check": ["joint deformity", "cardiovascular disease", "osteoporosis"],
    },
    "gout": {
        "must_rule_out": ["septic arthritis", "pseudogout", "rheumatoid arthritis"],
        "must_support_with": ["lab", "history"],
        "should_investigate_cause": ["hyperuricemia", "diet", "renal impairment"],
        "complications_to_check": ["tophi", "chronic kidney disease", "joint damage"],
    },
    "osteoporosis": {
        "must_rule_out": ["multiple myeloma", "metastatic bone disease", "osteomalacia"],
        "must_support_with": ["lab", "imaging"],
        "should_investigate_cause": ["post-menopausal", "steroid use", "hyperthyroidism"],
        "complications_to_check": ["fracture", "chronic pain", "immobility"],
    },

    # ---- New: Psychiatric ----
    "depression": {
        "must_rule_out": ["hypothyroidism", "anemia", "bipolar disorder", "substance abuse"],
        "must_support_with": ["history"],
        "should_investigate_cause": ["psychosocial", "genetic", "medical"],
        "complications_to_check": ["suicide risk", "substance abuse", "functional impairment"],
    },
    "anxiety disorder": {
        "must_rule_out": ["hyperthyroidism", "pheochromocytoma", "caffeine excess", "cardiac arrhythmia"],
        "must_support_with": ["history"],
        "should_investigate_cause": ["psychosocial", "genetic", "substance"],
        "complications_to_check": ["panic disorder", "substance abuse", "functional impairment"],
    },

    # ---- New: Other ----
    "anemia": {
        "must_rule_out": ["acute bleeding", "hemolysis", "bone marrow failure"],
        "must_support_with": ["lab"],
        "should_investigate_cause": ["iron deficiency", "b12 deficiency", "chronic disease", "renal"],
        "complications_to_check": ["heart failure", "cognitive impairment", "fatigue"],
    },
    "pulmonary embolism": {
        "must_rule_out": ["pneumonia", "pneumothorax", "acs", "heart failure"],
        "must_support_with": ["lab", "imaging"],
        "should_investigate_cause": ["dvt", "immobilization", "malignancy", "thrombophilia"],
        "complications_to_check": ["right heart strain", "pulmonary infarction", "recurrence"],
    },
    "chronic kidney disease": {
        "must_rule_out": ["acute kidney injury", "pre-renal azotemia", "obstruction"],
        "must_support_with": ["lab"],
        "should_investigate_cause": ["diabetes", "hypertension", "glomerulonephritis"],
        "complications_to_check": ["anemia", "electrolyte imbalance", "cardiovascular disease"],
    },
    "benign prostatic hyperplasia": {
        "must_rule_out": ["prostate cancer", "uti", "urethral stricture", "neurogenic bladder"],
        "must_support_with": ["history", "lab"],
        "should_investigate_cause": ["aging", "hormonal"],
        "complications_to_check": ["urinary retention", "renal impairment", "uti"],
    },
    "fibromyalgia": {
        "must_rule_out": ["hypothyroidism", "rheumatoid arthritis", "lupus", "chronic fatigue syndrome"],
        "must_support_with": ["history", "lab"],
        "should_investigate_cause": ["central sensitization", "stress", "sleep disorder"],
        "complications_to_check": ["depression", "anxiety", "functional impairment"],
    },
    "nephrolithiasis": {
        "must_rule_out": ["appendicitis", "ectopic pregnancy", "aortic aneurysm", "pyelonephritis"],
        "must_support_with": ["lab", "imaging"],
        "should_investigate_cause": ["hypercalcemia", "hyperuricemia", "dehydration"],
        "complications_to_check": ["obstruction", "infection", "renal damage"],
    },
    "glaucoma": {
        "must_rule_out": ["cataract", "macular degeneration", "optic neuritis"],
        "must_support_with": ["exam"],
        "should_investigate_cause": ["intraocular pressure", "family history"],
        "complications_to_check": ["vision loss", "blindness"],
    },
}


# ============================================================
# Expanded Drug-Condition Interactions
# ============================================================

EXPANDED_DRUG_CONDITION: List[CausalRelation] = [
    # Cardiovascular drugs
    CausalRelation("warfarin", "gi bleeding", "risk_factor",
                   strength=0.3, confidence=0.9,
                   description="Anticoagulation risk — GI tract specific"),
    CausalRelation("statin", "myopathy", "risk_factor",
                   strength=0.1, confidence=0.9,
                   description="Dose-dependent, higher with drug interactions"),
    CausalRelation("ace inhibitor", "cough", "risk_factor",
                   strength=0.2, confidence=0.95,
                   description="Bradykinin accumulation — up to 20% of patients"),
    CausalRelation("digoxin", "arrhythmia", "risk_factor",
                   strength=0.3, confidence=0.85,
                   description="Narrow therapeutic index — toxicity causes arrhythmia"),
    CausalRelation("beta blocker", "bradycardia", "risk_factor",
                   strength=0.2, confidence=0.9,
                   description="Rate control — excessive bradycardia"),
    CausalRelation("diuretic", "hypokalemia", "risk_factor",
                   strength=0.3, confidence=0.9,
                   description="Loop and thiazide diuretics — potassium wasting"),

    # Endocrine drugs
    CausalRelation("insulin", "hypoglycemia", "causes",
                   strength=0.4, confidence=0.95,
                   description="Dose-dependent — most common adverse effect"),
    CausalRelation("metformin", "vitamin b12 deficiency", "risk_factor",
                   strength=0.2, confidence=0.8,
                   description="Reduced B12 absorption with long-term use"),
    CausalRelation("levothyroxine", "hyperthyroidism", "risk_factor",
                   strength=0.2, confidence=0.85,
                   description="Overtreatment — excessive dose"),

    # Psychiatric drugs
    CausalRelation("ssri", "hyponatremia", "risk_factor",
                   strength=0.2, confidence=0.8,
                   description="SIADH — especially in elderly"),
    CausalRelation("benzodiazepine", "respiratory depression", "risk_factor",
                   strength=0.3, confidence=0.9,
                   description="Dose-dependent — dangerous with opioids"),
    CausalRelation("lithium", "hypothyroidism", "risk_factor",
                   strength=0.3, confidence=0.85,
                   description="Inhibits thyroid hormone release"),

    # NSAID and pain
    CausalRelation("opioid", "respiratory depression", "causes",
                   strength=0.5, confidence=0.95,
                   description="Dose-dependent — mu-receptor mediated"),
    CausalRelation("nsaid", "hypertension worsening", "risk_factor",
                   strength=0.2, confidence=0.8,
                   description="Prostaglandin inhibition → sodium retention"),

    # Antibiotics
    CausalRelation("fluoroquinolone", "tendon rupture", "risk_factor",
                   strength=0.1, confidence=0.85,
                   description="Achilles tendon — increased risk with steroids"),
    CausalRelation("penicillin", "anaphylaxis", "risk_factor",
                   strength=0.05, confidence=0.9,
                   description="IgE-mediated — rare but potentially fatal"),
]
