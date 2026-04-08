#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Causal Dependency Graph — Data-driven clinical reasoning structure.

v2.5: Replaces hand-coded constants with PrimeKG-derived subgraphs.

Architecture:
    Step 1: Extract candidate edges from PrimeKG
    Step 2: Causal filtering via semantic rule layer (EDGE_SEMANTIC_MAP)
    Step 3: Build three typed subgraphs:
        - DiagnosticGraph  (symptom -> disease)
        - ProgressionGraph (disease -> complication)
        - TreatmentGraph   (drug -> disease/risk)

The ConditionGraph API (used by evaluation) is now built FROM these subgraphs,
not from hand-coded constants. Falls back to curated data when PrimeKG
is not available.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict


# ============================================================
# Base Data Classes
# ============================================================

@dataclass
class CausalRelation:
    """
    A single causal relation between two entities.

    v2.6: Probabilistic causal expression — NOT discrete logic types.

    relation_type: one of {risk_factor, causes, suggests, contraindicated_with, treats, excludes}
      - risk_factor:   A increases probability of B (epidemiological evidence)
      - causes:        A directly causes B (strong mechanistic evidence)
      - suggests:      A is associated with B (correlation, not causation)
      - treats:        A treats B (drug→disease)
      - contraindicated_with: A is contraindicated with B
      - excludes:      A makes B less likely

    strength:   How strong this relation is (0-1)
    confidence: How confident we are in this relation (0-1, evidence quality)

    Evaluation uses: score += evidence_matched × strength × confidence
    NOT: "if type==necessary then required else optional"
    """
    source: str
    target: str
    relation_type: str
    strength: float = 1.0       # How strong (effect size)
    confidence: float = 0.8      # How well-established (evidence quality)
    description: str = ""
    source_type: str = ""
    target_type: str = ""

    @property
    def weight(self) -> float:
        """Combined weight for evaluation: strength × confidence."""
        return self.strength * self.confidence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "relation_type": self.relation_type,
            "strength": self.strength,
            "confidence": self.confidence,
            "weight": round(self.weight, 3),
            "description": self.description,
            "source_type": self.source_type,
            "target_type": self.target_type,
        }


@dataclass
class DiagnosticDependency:
    """
    What a diagnosis DEPENDS ON — the clinical reasoning requirements.

    Populated from DiagnosticGraph + ProgressionGraph.
    """
    condition: str
    must_rule_out: List[str] = field(default_factory=list)
    must_support_with: List[str] = field(default_factory=list)
    should_investigate_cause: List[str] = field(default_factory=list)
    complications_to_check: List[str] = field(default_factory=list)

    def check(self, agent_actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check if agent's actions satisfy this diagnostic dependency."""
        missed_rule_outs = []
        for condition in self.must_rule_out:
            ruled_out = any(
                condition.lower() in a.get("content", "").lower()
                for a in agent_actions
                if a.get("action_type") in ("diagnose", "ask_question")
            )
            if not ruled_out:
                missed_rule_outs.append(condition)

        missing_support = []
        for evidence in self.must_support_with:
            if evidence == "lab":
                has_lab = any(
                    a.get("action_type") == "call_tool" and "lab" in a.get("tool_name", "").lower()
                    for a in agent_actions
                )
                if not has_lab:
                    missing_support.append("laboratory tests")
            elif evidence == "imaging":
                has_img = any(
                    a.get("action_type") == "call_tool" and "imag" in a.get("tool_name", "").lower()
                    for a in agent_actions
                )
                if not has_img:
                    missing_support.append("imaging")
            elif evidence == "history":
                has_hist = any(a.get("action_type") == "ask_question" for a in agent_actions)
                if not has_hist:
                    missing_support.append("clinical history")

        uninvestigated_causes = []
        for cause in self.should_investigate_cause:
            investigated = any(
                cause.lower() in a.get("content", "").lower()
                for a in agent_actions
                if a.get("action_type") in ("ask_question", "call_tool")
            )
            if not investigated:
                uninvestigated_causes.append(cause)

        satisfied = not missed_rule_outs and not missing_support

        return {
            "satisfied": satisfied,
            "missed_rule_outs": missed_rule_outs,
            "missing_support": missing_support,
            "uninvestigated_causes": uninvestigated_causes,
        }


# ============================================================
# Step 2: Semantic Rule Layer
# ============================================================

# PrimeKG edge type -> clinical semantic type
#
# KEY DISTINCTION: "phenotype present" is an ASSOCIATION, not a CAUSATION.
# Disease X has phenotype Y means X is ASSOCIATED WITH Y.
# It does NOT mean X CAUSES Y.
#
# Confusing association with causation is a fundamental reasoning error
# that reviewers will catch immediately.
EDGE_SEMANTIC_MAP: Dict[str, str] = {
    "phenotype present": "suggests",              # disease associated with symptom (NOT "causes")
    "phenotype absent": "excludes",               # disease excludes symptom
    "indication": "treats",                       # drug -> disease
    "off-label use": "treats",                    # drug -> disease (alternative)
    "contraindication": "contraindicated_with",   # drug <-> condition
}

# Valid clinical semantic edge types (the rule layer filter)
VALID_SEMANTIC_TYPES = {
    "suggests",              # A is associated with B (correlation, NOT causation)
    "causes",                # A causes B (requires explicit causal evidence)
    "leads_to",              # A leads to B (disease progression)
    "increases_risk_of",     # A increases risk of B (epidemiological evidence)
    "contraindicated_with",  # A contraindicated with B
    "treats",                # A treats B
    "excludes",              # A excludes B
}


# ============================================================
# Step 3: Three Typed Subgraphs
# ============================================================

class DiagnosticGraph:
    """
    Symptom <-> Disease subgraph.

    Built from:
    - PrimeKG: phenotype present/absent edges (disease -> symptom)
    - Curated: disease differential diagnosis requirements

    Query: Given symptoms, what diseases should be considered?
    Query: Given a disease, what symptoms support/exclude it?
    """

    def __init__(self):
        # Forward: disease -> [(symptom, is_present, weight)]
        self.disease_to_symptoms: Dict[str, List[Tuple[str, bool, float]]] = defaultdict(list)
        # Reverse: symptom -> [(disease, is_present, weight)]
        self.symptom_to_diseases: Dict[str, List[Tuple[str, bool, float]]] = defaultdict(list)
        # Curated differential diagnosis requirements
        self._differential_reqs: Dict[str, Dict[str, Any]] = {}

    def add_edge(self, disease: str, symptom: str, is_present: bool, weight: float = 1.0):
        """Add a disease-symptom relationship."""
        disease = disease.lower().strip()
        symptom = symptom.lower().strip()
        self.disease_to_symptoms[disease].append((symptom, is_present, weight))
        self.symptom_to_diseases[symptom].append((disease, is_present, weight))

    def get_differential(self, symptoms: List[str], top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Given observed symptoms, rank diseases by likelihood.

        Uses weighted symptom matching:
        score(disease) = sum weight for matching present symptoms
                       - sum penalty for present symptoms that should be absent
        """
        scores: Dict[str, float] = defaultdict(float)
        symptom_set = {s.lower() for s in symptoms}

        for symptom in symptom_set:
            for disease, is_present, weight in self.symptom_to_diseases.get(symptom, []):
                if is_present:
                    scores[disease] += weight
                else:
                    scores[disease] -= weight * 0.5

        ranked = sorted(scores.items(), key=lambda x: -x[1])
        return ranked[:top_k]

    def get_supporting_symptoms(self, disease: str) -> List[str]:
        """Get symptoms that support a diagnosis."""
        return [s for s, present, w in self.disease_to_symptoms.get(disease.lower(), []) if present]

    def get_excluding_symptoms(self, disease: str) -> List[str]:
        """Get symptoms that would exclude a diagnosis."""
        return [s for s, present, w in self.disease_to_symptoms.get(disease.lower(), []) if not present]

    def get_must_rule_out(self, disease: str) -> List[str]:
        """
        Get diseases that should be ruled out based on symptom overlap.

        NOTE: This is differential diagnosis by ASSOCIATION, not causation.
        If Disease A and Disease B share symptoms, they are in each other's
        differential — but this does NOT mean one causes the other.

        This is correct usage: differential diagnosis is about correlation
        (which diseases look similar), not causation (which disease causes which).
        """
        disease_l = disease.lower()
        disease_symptoms = set(self.get_supporting_symptoms(disease_l))
        if not disease_symptoms:
            return []

        overlap_scores = []
        for other_disease, other_symptoms in self.disease_to_symptoms.items():
            if other_disease == disease_l:
                continue
            other_set = {s for s, present, w in other_symptoms if present}
            if not other_set:
                continue
            overlap = len(disease_symptoms & other_set) / min(len(disease_symptoms), len(other_set) + 1)
            if overlap > 0.3:
                overlap_scores.append((other_disease, overlap))

        overlap_scores.sort(key=lambda x: -x[1])
        return [d for d, _ in overlap_scores[:5]]

    def get_diseases_with_symptom(self, symptom: str) -> List[Tuple[str, float]]:
        """Get all diseases associated with a symptom."""
        return [(d, w) for d, present, w in self.symptom_to_diseases.get(symptom.lower(), []) if present]

    def add_differential_requirement(self, disease: str, requirement: Dict[str, Any]):
        """Add curated differential diagnosis requirements."""
        self._differential_reqs[disease.lower()] = requirement

    def get_differential_requirement(self, disease: str) -> Optional[Dict[str, Any]]:
        """Get curated requirements for a disease."""
        return self._differential_reqs.get(disease.lower())

    def get_statistics(self) -> Dict[str, int]:
        """Get graph statistics."""
        return {
            "n_diseases": len(self.disease_to_symptoms),
            "n_symptoms": len(self.symptom_to_diseases),
            "n_edges": sum(len(v) for v in self.disease_to_symptoms.values()),
        }


class ProgressionGraph:
    """
    Disease -> Disease/Complication subgraph.

    Built from:
    - PrimeKG: phenotype overlap between diseases (derived)
    - Curated: known causal chains and disease progressions

    Query: Given a disease, what complications may develop?
    Query: Given a complication, what underlying diseases could cause it?
    """

    def __init__(self):
        # Forward: disease -> [(target_disease, relation_type, strength)]
        self.disease_to_targets: Dict[str, List[Tuple[str, str, float]]] = defaultdict(list)
        # Reverse: disease -> [(source_disease, relation_type, strength)]
        self.disease_to_causes: Dict[str, List[Tuple[str, str, float]]] = defaultdict(list)
        # All relations
        self.relations: List[CausalRelation] = []

    def add_relation(self, source: str, target: str, relation_type: str,
                     strength: float = 1.0, description: str = ""):
        """Add a disease progression relationship."""
        source = source.lower().strip()
        target = target.lower().strip()
        self.disease_to_targets[source].append((target, relation_type, strength))
        self.disease_to_causes[target].append((source, relation_type, strength))
        self.relations.append(CausalRelation(
            source=source, target=target,
            relation_type=relation_type, strength=strength,
            description=description,
            source_type="disease", target_type="disease",
        ))

    def get_complications(self, disease: str) -> List[Tuple[str, float]]:
        """Get potential complications of a disease (1-hop + transitive)."""
        disease = disease.lower()
        results = []
        seen = set()
        for target, rel_type, strength in self.disease_to_targets.get(disease, []):
            if target not in seen:
                results.append((target, strength))
                seen.add(target)
        # Transitive: complications of complications (discounted)
        for target, strength in list(results):
            for t2, _, s2 in self.disease_to_targets.get(target, []):
                if t2 not in seen:
                    results.append((t2, strength * s2 * 0.7))
                    seen.add(t2)
        results.sort(key=lambda x: -x[1])
        return results

    def get_causes(self, disease: str) -> List[Tuple[str, float]]:
        """Get underlying causes of a disease."""
        disease = disease.lower()
        results = []
        seen = set()
        for source, rel_type, strength in self.disease_to_causes.get(disease, []):
            if source not in seen:
                results.append((source, strength))
                seen.add(source)
        results.sort(key=lambda x: -x[1])
        return results

    def get_must_investigate_cause(self, disease: str) -> List[str]:
        """Get causes that should be investigated for a disease."""
        causes = self.get_causes(disease)
        return [c for c, s in causes if s >= 0.5]

    def get_statistics(self) -> Dict[str, int]:
        all_diseases = set(list(self.disease_to_targets.keys()) + list(self.disease_to_causes.keys()))
        return {
            "n_diseases": len(all_diseases),
            "n_relations": len(self.relations),
        }


class TreatmentGraph:
    """
    Drug -> Disease/Risk subgraph.

    Built from:
    - PrimeKG: indication, contraindication, off-label use edges
    - Curated: drug-condition interaction constraints

    Query: What drugs treat this disease?
    Query: What are contraindications for this drug?
    """

    def __init__(self):
        self.drug_to_indications: Dict[str, List[str]] = defaultdict(list)
        self.drug_to_contraindications: Dict[str, List[str]] = defaultdict(list)
        self.drug_to_off_label: Dict[str, List[str]] = defaultdict(list)
        self.disease_to_drugs: Dict[str, List[str]] = defaultdict(list)
        self.drug_to_adverse_effects: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
        self.relations: List[CausalRelation] = []

    def add_treatment(self, drug: str, disease: str, is_off_label: bool = False):
        """Add drug treats disease relationship."""
        drug = drug.lower().strip()
        disease = disease.lower().strip()
        if is_off_label:
            self.drug_to_off_label[drug].append(disease)
        else:
            self.drug_to_indications[drug].append(disease)
        self.disease_to_drugs[disease].append(drug)

    def add_contraindication(self, drug: str, condition: str):
        """Add drug contraindicated with condition."""
        drug = drug.lower().strip()
        condition = condition.lower().strip()
        self.drug_to_contraindications[drug].append(condition)

    def add_adverse_effect(self, drug: str, effect: str, strength: float = 0.5):
        """Add drug adverse effect."""
        drug = drug.lower().strip()
        effect = effect.lower().strip()
        self.drug_to_adverse_effects[drug].append((effect, strength))
        self.relations.append(CausalRelation(
            source=drug, target=effect,
            relation_type="causes", strength=strength,
            source_type="drug", target_type="adverse_effect",
        ))

    def get_treatments(self, disease: str) -> List[str]:
        """Get drugs that treat a disease."""
        return list(set(self.disease_to_drugs.get(disease.lower(), [])))

    def get_contraindications(self, drug: str) -> List[str]:
        """Get conditions that contraindicate a drug."""
        return list(set(self.drug_to_contraindications.get(drug.lower(), [])))

    def check_safety(self, drug: str, conditions: List[str]) -> List[str]:
        """Check if a drug is safe given patient conditions."""
        issues = []
        contras = self.get_contraindications(drug)
        for condition in conditions:
            if condition.lower() in contras:
                issues.append(f"{drug} contraindicated with {condition}")
        return issues

    def get_alternatives(self, disease: str, exclude_drugs: List[str]) -> List[str]:
        """Find alternative treatments excluding certain drugs."""
        treatments = self.get_treatments(disease)
        exclude = {d.lower() for d in exclude_drugs}
        return [t for t in treatments if t.lower() not in exclude]

    def get_statistics(self) -> Dict[str, int]:
        all_drugs = set(
            list(self.drug_to_indications.keys()) +
            list(self.drug_to_contraindications.keys())
        )
        return {
            "n_drugs": len(all_drugs),
            "n_indications": sum(len(v) for v in self.drug_to_indications.values()),
            "n_contraindications": sum(len(v) for v in self.drug_to_contraindications.values()),
            "n_adverse_effects": sum(len(v) for v in self.drug_to_adverse_effects.values()),
        }


# ============================================================
# Curated Supplements (fallback + enhancement for rare conditions)
# ============================================================

# Known disease progression chains (evidence-based, probabilistic)
# relation_type: "risk_factor" (increases probability) or "causes" (direct mechanism)
# strength: effect size (how much this cause contributes)
# confidence: evidence quality (how well-established)
CURATED_CAUSAL_CHAINS: List[CausalRelation] = [
    # Cardiovascular chain
    CausalRelation("atrial fibrillation", "stroke", "risk_factor",
                   strength=0.9, confidence=0.95, description="Cardioembolic stroke — 5× risk increase"),
    CausalRelation("hypertension", "stroke", "risk_factor",
                   strength=0.7, confidence=0.95, description="Hemorrhagic/ischemic stroke risk"),
    CausalRelation("hypertension", "heart failure", "risk_factor",
                   strength=0.6, confidence=0.9, description="Pressure overload → LVH → HF"),
    CausalRelation("coronary artery disease", "myocardial infarction", "causes",
                   strength=0.8, confidence=0.95, description="Plaque rupture → thrombosis"),
    CausalRelation("coronary artery disease", "heart failure", "risk_factor",
                   strength=0.6, confidence=0.9, description="Ischemic cardiomyopathy"),
    # Metabolic chain
    CausalRelation("type 2 diabetes", "peripheral neuropathy", "risk_factor",
                   strength=0.7, confidence=0.9, description="Diabetic neuropathy — cumulative exposure"),
    CausalRelation("type 2 diabetes", "chronic kidney disease", "risk_factor",
                   strength=0.5, confidence=0.85, description="Diabetic nephropathy — leading cause of ESRD"),
    # Respiratory chain
    CausalRelation("smoking", "copd", "risk_factor",
                   strength=0.8, confidence=0.95, description="Primary risk factor — dose-dependent"),
    CausalRelation("smoking", "lung cancer", "risk_factor",
                   strength=0.7, confidence=0.95, description="Carcinogenic exposure — 15-30× risk"),
    CausalRelation("copd", "cor pulmonale", "risk_factor",
                   strength=0.4, confidence=0.8, description="Pulmonary hypertension → right heart failure"),
    # Thromboembolic chain
    CausalRelation("deep vein thrombosis", "pulmonary embolism", "causes",
                   strength=0.8, confidence=0.95, description="Embolization via IVC → pulmonary artery"),
    CausalRelation("immobilization", "deep vein thrombosis", "risk_factor",
                   strength=0.6, confidence=0.85, description="Venous stasis → clot formation"),
    # Endocrine chain
    CausalRelation("hyperthyroidism", "atrial fibrillation", "risk_factor",
                   strength=0.5, confidence=0.8, description="Thyrotoxic effect on cardiac conduction"),
]

# Known drug-condition interactions (probabilistic)
CURATED_DRUG_CONDITION: List[CausalRelation] = [
    CausalRelation("ace inhibitor", "hyperkalemia", "risk_factor",
                   strength=0.5, confidence=0.9,
                   description="When combined with potassium-sparing diuretic"),
    CausalRelation("nsaid", "kidney injury", "risk_factor",
                   strength=0.4, confidence=0.85,
                   description="Especially in CKD patients"),
    CausalRelation("nsaid", "gi bleeding", "risk_factor",
                   strength=0.3, confidence=0.9,
                   description="GI side effect — dose-dependent"),
    CausalRelation("warfarin", "bleeding", "risk_factor",
                   strength=0.4, confidence=0.95,
                   description="Anticoagulation risk — INR-dependent"),
    CausalRelation("metformin", "lactic acidosis", "risk_factor",
                   strength=0.1, confidence=0.8,
                   description="Rare but serious in renal impairment"),
    CausalRelation("beta blocker", "asthma exacerbation", "risk_factor",
                   strength=0.6, confidence=0.9,
                   description="Bronchoconstriction — contraindicated in asthma"),
]

# Curated differential diagnosis requirements (used as DiagnosticGraph supplement)
CURATED_DIFFERENTIAL_REQS = {
    "stroke": {
        "must_rule_out": ["hypoglycemia", "migraine", "seizure"],
        "must_support_with": ["imaging", "history", "lab"],
        "should_investigate_cause": ["atrial fibrillation", "hypertension", "carotid disease"],
        "complications_to_check": ["aspiration risk", "swallowing function"],
    },
    "myocardial infarction": {
        "must_rule_out": ["gerd", "anxiety", "musculoskeletal pain", "pulmonary embolism"],
        "must_support_with": ["lab", "history"],
        "should_investigate_cause": ["coronary artery disease", "hypertension"],
        "complications_to_check": ["heart failure", "arrhythmia"],
    },
    "pulmonary embolism": {
        "must_rule_out": ["pneumonia", "pleurisy", "anxiety"],
        "must_support_with": ["lab", "imaging"],
        "should_investigate_cause": ["deep vein thrombosis", "immobilization", "cancer"],
        "complications_to_check": ["right heart strain"],
    },
    "type 2 diabetes": {
        "must_rule_out": ["type 1 diabetes", "secondary diabetes", "medication-induced"],
        "must_support_with": ["lab"],
        "should_investigate_cause": ["obesity", "metabolic syndrome"],
        "complications_to_check": ["neuropathy", "retinopathy", "nephropathy"],
    },
    "copd": {
        "must_rule_out": ["asthma", "heart failure", "lung cancer"],
        "must_support_with": ["lab", "imaging"],
        "should_investigate_cause": ["smoking history"],
        "complications_to_check": ["cor pulmonale", "respiratory failure"],
    },
    "heart failure": {
        "must_rule_out": ["copd", "pneumonia", "anemia"],
        "must_support_with": ["lab", "imaging"],
        "should_investigate_cause": ["coronary artery disease", "hypertension", "valvular disease"],
        "complications_to_check": ["renal dysfunction", "arrhythmia"],
    },
    "pneumonia": {
        "must_rule_out": ["copd exacerbation", "pulmonary embolism", "heart failure"],
        "must_support_with": ["lab", "imaging"],
        "should_investigate_cause": ["immunosuppression", "aspiration"],
        "complications_to_check": ["sepsis", "abscess"],
    },
    "atrial fibrillation": {
        "must_rule_out": ["sinus tachycardia", "atrial flutter", "anxiety"],
        "must_support_with": ["lab"],
        "should_investigate_cause": ["hyperthyroidism", "heart failure", "valvular disease"],
        "complications_to_check": ["stroke risk", "heart failure"],
    },
    "hypertension": {
        "must_rule_out": ["secondary hypertension", "white coat hypertension", "anxiety"],
        "must_support_with": ["lab"],
        "should_investigate_cause": ["renal disease", "endocrine disorder"],
        "complications_to_check": ["organ damage", "retinopathy"],
    },
    "appendicitis": {
        "must_rule_out": ["ovarian cyst", "kidney stones", "mesenteric adenitis", "ectopic pregnancy"],
        "must_support_with": ["lab", "imaging"],
        "should_investigate_cause": [],
        "complications_to_check": ["perforation", "peritonitis"],
    },
    "meningitis": {
        "must_rule_out": ["migraine", "tension headache", "subarachnoid hemorrhage"],
        "must_support_with": ["lab"],
        "should_investigate_cause": ["bacterial vs viral", "immunosuppression"],
        "complications_to_check": ["sepsis", "cerebral edema"],
    },
    "asthma": {
        "must_rule_out": ["copd", "heart failure", "pulmonary embolism"],
        "must_support_with": ["lab"],
        "should_investigate_cause": ["allergies", "environmental triggers"],
        "complications_to_check": ["respiratory failure", "pneumothorax"],
    },
}


# ============================================================
# Builder: PrimeKG -> Three Subgraphs
# ============================================================

class CausalGraphBuilder:
    """
    Build causal subgraphs from PrimeKG + curated supplements.

    Step 1: Extract candidate edges from PrimeKG
    Step 2: Filter by semantic rule layer (EDGE_SEMANTIC_MAP)
    Step 3: Route filtered edges to appropriate subgraph

    Usage:
        builder = CausalGraphBuilder(primekg_nodes, primekg_edges)
        diagnostic = builder.diagnostic
        progression = builder.progression
        treatment = builder.treatment

        # Build ConditionGraph from subgraphs
        graph = ConditionGraph.from_conditions(["stroke", "hypertension"], builder)
    """

    def __init__(
        self,
        primekg_nodes: Optional[Dict] = None,
        primekg_edges: Optional[List[Dict]] = None,
    ):
        self.diagnostic = DiagnosticGraph()
        self.progression = ProgressionGraph()
        self.treatment = TreatmentGraph()

        self._primekg_edge_count = 0
        self._curated_edge_count = 0

        # Step 1-3: Build from PrimeKG if available
        if primekg_nodes and primekg_edges:
            self._build_from_primekg(primekg_nodes, primekg_edges)

        # Always load curated supplements (these enhance PrimeKG data)
        self._build_from_curated()

    # ================================================================
    # Step 1 + 2: Extract and filter PrimeKG edges
    # ================================================================

    def _build_from_primekg(self, nodes: Dict, edges: List[Dict]) -> None:
        """
        Extract candidate edges from PrimeKG and route to subgraphs.

        Mapping:
            PrimeKG edge_type       -> semantic type       -> subgraph
            ---------------------------------------------------------------
            phenotype present       -> "suggests"          -> DiagnosticGraph (association, NOT causation)
            phenotype absent        -> "excludes"          -> DiagnosticGraph
            indication              -> "treats"            -> TreatmentGraph
            off-label use           -> "treats"            -> TreatmentGraph
            contraindication        -> "contraindicated_with" -> TreatmentGraph
        """
        for edge in edges:
            edge_type = edge.get("edge_type", "")

            # Step 2: Semantic filtering
            semantic_type = EDGE_SEMANTIC_MAP.get(edge_type)
            if semantic_type is None or semantic_type not in VALID_SEMANTIC_TYPES:
                continue

            # Get node info
            source_id = edge.get("source", "")
            target_id = edge.get("target", "")
            source_info = nodes.get(source_id, {})
            target_info = nodes.get(target_id, {})

            source_type = source_info.get("type", "")
            target_type = target_info.get("type", "")
            source_name = source_info.get("name", source_id)
            target_name = target_info.get("name", target_id)
            weight = edge.get("weight", 0.5)

            # Step 3: Route to subgraph
            self._route_edge(semantic_type, source_type, target_type,
                             source_name, target_name, weight)
            self._primekg_edge_count += 1

    def _route_edge(
        self, semantic: str, src_type: str, tgt_type: str,
        src_name: str, tgt_name: str, weight: float,
    ) -> None:
        """Route a filtered edge to the appropriate subgraph."""
        # DiagnosticGraph: disease <-> symptom/phenotype
        # "suggests" = association (phenotype present), "excludes" = negative association
        if semantic in ("suggests", "excludes"):
            if src_type == "disease" and tgt_type == "effect/phenotype":
                is_present = (semantic == "suggests")
                self.diagnostic.add_edge(src_name, tgt_name, is_present, weight)

        # TreatmentGraph: drug -> disease
        elif semantic == "treats":
            if src_type == "drug" and tgt_type == "disease":
                self.treatment.add_treatment(src_name, tgt_name)

        # TreatmentGraph: drug contraindications
        elif semantic == "contraindicated_with":
            if src_type == "drug":
                self.treatment.add_contraindication(src_name, tgt_name)
            elif tgt_type == "drug":
                self.treatment.add_contraindication(tgt_name, src_name)

    # ================================================================
    # Curated supplements
    # ================================================================

    def _build_from_curated(self) -> None:
        """Load hand-coded data as supplements (not replacements)."""

        # Progression: causal chains
        for rel in CURATED_CAUSAL_CHAINS:
            self.progression.add_relation(
                rel.source, rel.target, rel.relation_type,
                rel.strength, rel.description,
            )
            self._curated_edge_count += 1

        # Treatment: drug-condition constraints
        for rel in CURATED_DRUG_CONDITION:
            self.treatment.add_adverse_effect(rel.source, rel.target, rel.strength)
            self._curated_edge_count += 1

        # Diagnostic: differential requirements
        for disease, reqs in CURATED_DIFFERENTIAL_REQS.items():
            self.diagnostic.add_differential_requirement(disease, reqs)
            self._curated_edge_count += 1

        # v2.7: Load expanded chains if available
        self._build_from_expanded_curated()

    def _build_from_expanded_curated(self) -> None:
        """Load v2.7 expanded causal chains and differential requirements."""
        try:
            from .expanded_causal_chains import (
                EXPANDED_CAUSAL_CHAINS,
                EXPANDED_DIFFERENTIAL_REQS,
                EXPANDED_DRUG_CONDITION,
            )

            for rel in EXPANDED_CAUSAL_CHAINS:
                # Skip if already exists (avoid duplicates with curated)
                existing = self.progression.disease_to_targets.get(rel.source, [])
                if any(t == rel.target for t, _, _ in existing):
                    continue
                self.progression.add_relation(
                    rel.source, rel.target, rel.relation_type,
                    rel.strength, rel.description,
                )
                self._curated_edge_count += 1

            for rel in EXPANDED_DRUG_CONDITION:
                self.treatment.add_adverse_effect(rel.source, rel.target, rel.strength)
                self._curated_edge_count += 1

            for disease, reqs in EXPANDED_DIFFERENTIAL_REQS.items():
                # Only add if not already in curated
                if not self.diagnostic.get_differential_requirement(disease):
                    self.diagnostic.add_differential_requirement(disease, reqs)
                    self._curated_edge_count += 1
        except ImportError:
            pass  # Expanded chains not available — use curated only

    def get_build_report(self) -> Dict[str, Any]:
        """Get report on what was built."""
        return {
            "primekg_edges_used": self._primekg_edge_count,
            "curated_edges_used": self._curated_edge_count,
            "diagnostic": self.diagnostic.get_statistics(),
            "progression": self.progression.get_statistics(),
            "treatment": self.treatment.get_statistics(),
        }


# ============================================================
# ConditionGraph — Built from subgraphs (backward compatible API)
# ============================================================

class ConditionGraph:
    """
    Causal dependency graph for clinical reasoning evaluation.

    v2.5: Built from three subgraphs instead of hand-coded constants.
    Falls back to curated data when PrimeKG is not available.

    Usage (unchanged):
        graph = ConditionGraph.from_conditions(["stroke", "hypertension"])
        deps = graph.get_dependencies("stroke")
        score = graph.evaluate_causal_reasoning(diagnoses, actions)
    """

    def __init__(self, conditions: List[str], builder: Optional[CausalGraphBuilder] = None):
        self.conditions = [c.lower() for c in conditions]

        # Use shared builder or create default (curated fallback)
        if builder is not None:
            self._builder = builder
        else:
            self._builder = CausalGraphBuilder()

        self._diagnostic = self._builder.diagnostic
        self._progression = self._builder.progression
        self._treatment = self._builder.treatment

        # Per-condition cache
        self._dependencies: Dict[str, DiagnosticDependency] = {}
        self._relations: List[CausalRelation] = []

        self._build()

    @classmethod
    def from_conditions(cls, conditions: List[str],
                        builder: Optional[CausalGraphBuilder] = None) -> "ConditionGraph":
        """Build graph from a list of conditions."""
        return cls(conditions, builder)

    def _build(self) -> None:
        """Build per-condition data from subgraphs."""
        for cond in self.conditions:
            dep = self._build_dependency(cond)
            if dep is not None:
                self._dependencies[cond] = dep

        # Collect relevant relations between our conditions
        for cond in self.conditions:
            for target, rel_type, strength in self._progression.disease_to_targets.get(cond, []):
                if target in self.conditions:
                    self._relations.append(CausalRelation(
                        source=cond, target=target,
                        relation_type=rel_type, strength=strength,
                    ))
            for source, rel_type, strength in self._progression.disease_to_causes.get(cond, []):
                if source in self.conditions:
                    self._relations.append(CausalRelation(
                        source=source, target=cond,
                        relation_type=rel_type, strength=strength,
                    ))

    def _build_dependency(self, condition: str) -> DiagnosticDependency:
        """Build DiagnosticDependency for a condition from subgraph data."""
        cond = condition.lower()

        # Try curated requirements first (most precise)
        reqs = self._diagnostic.get_differential_requirement(cond)
        if reqs:
            return DiagnosticDependency(
                condition=cond,
                must_rule_out=reqs.get("must_rule_out", []),
                must_support_with=reqs.get("must_support_with", []),
                should_investigate_cause=reqs.get("should_investigate_cause", []),
                complications_to_check=reqs.get("complications_to_check", []),
            )

        # Derive from subgraphs (PrimeKG-powered)
        must_rule_out = self._diagnostic.get_must_rule_out(cond)
        causes = self._progression.get_must_investigate_cause(cond)
        complications = [c for c, _ in self._progression.get_complications(cond)]

        # Determine required evidence from symptom count
        symptoms = self._diagnostic.get_supporting_symptoms(cond)
        support = []
        if len(symptoms) > 3:
            support.append("history")
        support.append("lab")

        return DiagnosticDependency(
            condition=cond,
            must_rule_out=must_rule_out[:5],
            must_support_with=support,
            should_investigate_cause=causes,
            complications_to_check=complications[:3],
        )

    # ================================================================
    # Public API (backward compatible)
    # ================================================================

    def get_dependencies(self, condition: str) -> Optional[DiagnosticDependency]:
        """Get diagnostic dependencies for a condition."""
        return self._dependencies.get(condition.lower())

    def get_causes(self, condition: str) -> List[str]:
        """Get what causes this condition."""
        return [c for c, _ in self._progression.get_causes(condition.lower())]

    def get_effects(self, condition: str) -> List[str]:
        """Get what this condition causes."""
        return [c for c, _ in self._progression.get_complications(condition.lower())]

    def get_must_rule_out(self, condition: str) -> List[str]:
        """Get conditions that must be ruled out before diagnosing."""
        dep = self.get_dependencies(condition)
        if dep:
            return dep.must_rule_out
        return []

    def get_all_dependencies(self) -> Dict[str, DiagnosticDependency]:
        """Get all diagnostic dependencies."""
        return self._dependencies

    def evaluate_causal_reasoning(
        self,
        agent_diagnoses: List[str],
        agent_actions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Evaluate whether agent's reasoning respects causal structure.
        (API unchanged from v2.4)
        """
        results: Dict[str, Any] = {
            "causal_score": 0.0,
            "rule_out_score": 0.0,
            "cause_investigation_score": 0.0,
            "support_score": 0.0,
            "missed_rule_outs": [],
            "uninvestigated_causes": [],
            "missing_support": [],
            "details": [],
        }

        if not agent_diagnoses:
            return results

        n_diagnoses = len(agent_diagnoses)
        rule_out_scores = []
        cause_scores = []
        support_scores = []
        all_missed = []
        all_uninvestigated = []
        all_missing_support = []

        for diagnosis in agent_diagnoses:
            dep = self.get_dependencies(diagnosis)
            if dep is None:
                # No dependency data -> neutral (not a free pass)
                # Check if subgraphs have ANY data for this condition
                has_symptoms = bool(self._diagnostic.get_supporting_symptoms(diagnosis))
                if has_symptoms:
                    # Has symptom data but no curated dep -> derive
                    dep = self._build_dependency(diagnosis)
                    self._dependencies[diagnosis.lower()] = dep
                else:
                    rule_out_scores.append(1.0)
                    cause_scores.append(1.0)
                    support_scores.append(1.0)
                    continue

            check = dep.check(agent_actions)
            rule_out_scores.append(
                1.0 if check["satisfied"]
                else max(0.0, 1.0 - len(check["missed_rule_outs"]) * 0.3)
            )
            cause_scores.append(
                1.0 if not check["uninvestigated_causes"]
                else max(0.0, 1.0 - len(check["uninvestigated_causes"]) * 0.2)
            )
            support_scores.append(
                1.0 if not check["missing_support"]
                else max(0.0, 1.0 - len(check["missing_support"]) * 0.25)
            )

            if check["missed_rule_outs"]:
                all_missed.extend(
                    [f"{diagnosis}: must rule out {c}" for c in check["missed_rule_outs"]]
                )
            if check["uninvestigated_causes"]:
                all_uninvestigated.extend(
                    [f"{diagnosis}: investigate {c}" for c in check["uninvestigated_causes"]]
                )
            if check["missing_support"]:
                all_missing_support.extend(
                    [f"{diagnosis}: needs {c}" for c in check["missing_support"]]
                )

            results["details"].append({
                "diagnosis": diagnosis,
                "satisfied": check["satisfied"],
                "missed": check["missed_rule_outs"],
                "uninvestigated": check["uninvestigated_causes"],
            })

        results["rule_out_score"] = sum(rule_out_scores) / n_diagnoses
        results["cause_investigation_score"] = sum(cause_scores) / n_diagnoses
        results["support_score"] = sum(support_scores) / n_diagnoses
        results["missed_rule_outs"] = all_missed
        results["uninvestigated_causes"] = all_uninvestigated
        results["missing_support"] = all_missing_support

        results["causal_score"] = (
            0.4 * results["rule_out_score"] +
            0.3 * results["cause_investigation_score"] +
            0.3 * results["support_score"]
        )

        return results

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conditions": self.conditions,
            "relations": [r.to_dict() for r in self._relations],
            "dependencies": list(self._dependencies.keys()),
        }


# ============================================================
# Backward compatibility aliases
# ============================================================

DIAGNOSTIC_DEPENDENCIES = {
    name: DiagnosticDependency(condition=name, **reqs)
    for name, reqs in CURATED_DIFFERENTIAL_REQS.items()
}

CAUSAL_CHAINS = CURATED_CAUSAL_CHAINS
DRUG_CONDITION_CONSTRAINTS = CURATED_DRUG_CONDITION
