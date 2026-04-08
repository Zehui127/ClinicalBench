#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrimeKG Bridge — Translate PrimeKG data into structures for CausalGraphBuilder.

Problem: PrimeKG uses rare/genetic disease names ("trachoma"),
while ClinicalKnowledgeBase uses common names ("type 2 diabetes").
Most common diseases have NO exact match.

Solution: Multi-tier name normalization + data extraction layer.

Usage:
    from medical_task_suite.generation.core.kg_loader import PrimeKGLoader
    loader = PrimeKGLoader()
    nodes, edges, _ = loader.load()

    from .primekg_bridge import PrimeKGBridge
    bridge = PrimeKGBridge(nodes, edges, clinical_kb)
    builder = CausalGraphBuilder(bridge.get_nodes_for_builder(), bridge.get_edges_for_builder())
"""

import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict


# ============================================================
# Curated Name Mapping — Manual bridge for common diseases
# ============================================================

# PrimeKG name (or substring) → Clinical KB name
COMMON_DISEASE_MAP: Dict[str, str] = {
    # Cardiovascular
    "essential hypertension": "hypertension",
    "pulmonary hypertension, primary": "hypertension",
    "coronary atherosclerosis": "coronary artery disease",
    "coronary artery disease, autosomal dominant": "coronary artery disease",
    "myocardial infarction": "heart failure",
    "atrial fibrillation (disease)": "atrial fibrillation",
    "familial atrial fibrillation": "atrial fibrillation",
    "heart failure (disease)": "heart failure",
    "congestive heart failure": "heart failure",

    # Metabolic/Endocrine
    "type 1 diabetes mellitus": "type 1 diabetes",
    "type 2 diabetes mellitus": "type 2 diabetes",
    "diabetes mellitus": "type 2 diabetes",
    "hyperthyroidism (disease)": "hyperthyroidism",
    "familial hyperthyroidism due to mutations in tsh receptor": "hyperthyroidism",
    "congenital hypothyroidism": "hypothyroidism",
    "hypothyroidism (disease)": "hypothyroidism",
    "hyperlipidemia, familial combined, lpl related": "hyperlipidemia",
    "familial hypercholesterolemia": "hyperlipidemia",

    # Respiratory
    "chronic obstructive pulmonary disease": "copd",
    "copd, severe early onset": "copd",
    "intrinsic asthma": "asthma",
    "bronchial asthma": "asthma",
    "bacterial pneumonia": "pneumonia",
    "staphylococcal pneumonia": "pneumonia",
    "klebsiella pneumonia": "pneumonia",

    # Neurological
    "ischemic stroke": "stroke",
    "hemorrhagic stroke": "stroke",
    "obsolete susceptibility to ischemic stroke": "stroke",
    "progressive myoclonic epilepsy": "epilepsy",
    "myoclonic epilepsy, juvenile, susceptibility to": "epilepsy",
    "epilepsy, childhood absence, susceptibility to": "epilepsy",
    "migraine with or without aura, susceptibility to": "migraine",
    "familial hemiplegic migraine": "migraine",
    "familial or sporadic hemiplegic migraine": "migraine",
    "parkinson disease, late-onset": "parkinson disease",
    "parkinsonism": "parkinson disease",

    # Renal
    "chronic kidney disease": "chronic kidney disease",
    "kidney failure, chronic": "chronic kidney disease",
    "end-stage renal disease": "chronic kidney disease",
    "nephrolithiasis": "nephrolithiasis",
    "kidney stone": "nephrolithiasis",

    # Musculoskeletal
    "rheumatoid arthritis (disease)": "rheumatoid arthritis",
    "osteoarthritis (disease)": "osteoarthritis",
    "aneurysm-osteoarthritis syndrome": "osteoarthritis",
    "gout (disease)": "gout",

    # GI
    "gastroesophageal reflux disease": "gerd",
    "peptic ulcer": "peptic ulcer disease",
    "inflammatory bowel disease": "irritable bowel syndrome",
    "cirrhosis of liver": "cirrhosis",
    "liver cirrhosis": "cirrhosis",

    # Psychiatric
    "major depressive disorder": "depression",
    "anxiety disorder (disease)": "anxiety disorder",
    "generalized anxiety disorder": "anxiety disorder",
    "bipolar disorder (disease)": "bipolar disorder",
    "post-traumatic stress disorder": "PTSD",

    # Infectious
    "sepsis (disease)": "pneumonia",  # commonly confused
    "urinary tract infection": "nephrolithiasis",  # overlap symptoms

    # Hematologic
    "fanconi anemia complementation group": "anemia",
    "iron deficiency anemia": "anemia",
    "sickle cell anemia": "sickle cell anemia",
    "deep vein thrombosis": "pulmonary embolism",

    # Autoimmune
    "systemic lupus erythematosus (disease)": "systemic lupus erythematosus",
    "sjogren syndrome": "rheumatoid arthritis",  # similar presentation

    # Other
    "pulmonary embolism (disease)": "pulmonary embolism",
    "osteoporosis (disease)": "osteoporosis",
    "glaucoma (disease)": "glaucoma",
    "cataract": "glaucoma",  # overlap symptoms
    "benign prostatic hyperplasia (disease)": "benign prostatic hyperplasia",
    "fibromyalgia (disease)": "fibromyalgia",
    "chronic fatigue syndrome": "fibromyalgia",
    "meningitis (disease)": "meningitis",
    "bacterial meningitis": "meningitis",
}

# Words to strip when trying keyword matching
STRIP_WORDS = {
    "disease", "disorder", "syndrome", "type", "chronic", "acute",
    "familial", "congenital", "idiopathic", "essential", "primary",
    "secondary", "autosomal dominant", "autosomal recessive",
    "susceptibility to", "obsolete", "(disease)", "late-onset",
    "early onset", "severe",
}


class PrimeKGBridge:
    """
    Translate PrimeKG nodes/edges into structures consumable by CausalGraphBuilder.

    Handles:
    1. Name normalization (PrimeKG rare names → KB common names)
    2. Edge filtering and format conversion
    3. Disease-symptom/drug/overlap extraction
    """

    def __init__(
        self,
        primekg_nodes: Dict[str, Any],
        primekg_edges: List[Dict[str, Any]],
        clinical_kb=None,
    ):
        self.raw_nodes = primekg_nodes
        self.raw_edges = primekg_edges
        self.kb = clinical_kb

        # Build indices
        self._node_map: Dict[str, Dict] = {}  # id -> node info
        self._kb_diseases: set = set()
        self._normalized_names: Dict[str, str] = {}  # primekg_name -> kb_name

        # Data caches
        self._disease_symptoms: Dict[str, List[str]] = defaultdict(list)
        self._disease_drugs: Dict[str, List[str]] = defaultdict(list)
        self._drug_contraindications: Dict[str, List[str]] = defaultdict(list)
        self._drug_indications: Dict[str, List[str]] = defaultdict(list)

        self._build()

    def _build(self) -> None:
        """Build internal indices from PrimeKG data."""
        # Build node map
        for nid, ninfo in self.raw_nodes.items():
            self._node_map[nid] = ninfo

        # Get KB disease names for matching
        if self.kb:
            self._kb_diseases = {d.lower() for d in self.kb.get_covered_diseases()}

        # Pre-compute name normalization for all disease nodes
        for nid, ninfo in self.raw_nodes.items():
            if ninfo.get("type") == "disease":
                name = ninfo.get("name", "").lower().strip()
                normalized = self._normalize(name)
                if normalized:
                    self._normalized_names[name] = normalized

        # Extract edges into typed caches
        for edge in self.raw_edges:
            src = self._node_map.get(edge.get("source", ""))
            tgt = self._node_map.get(edge.get("target", ""))
            if not src or not tgt:
                continue

            etype = edge.get("edge_type", "")
            src_type = src.get("type", "")
            tgt_type = tgt.get("type", "")
            src_name = src.get("name", "").lower().strip()
            tgt_name = tgt.get("name", "").lower().strip()

            # Disease → Phenotype (symptom) edges
            if etype == "phenotype present" and src_type == "disease" and tgt_type == "effect/phenotype":
                norm = self._normalized_names.get(src_name, src_name)
                self._disease_symptoms[norm].append(tgt_name)

            # Disease ← Phenotype (negative) — phenotype absent
            if etype == "phenotype absent" and src_type == "disease" and tgt_type == "effect/phenotype":
                norm = self._normalized_names.get(src_name, src_name)
                # Store as exclusion symptom (prefixed)
                self._disease_symptoms[norm].append(f"!{tgt_name}")

            # Drug → Disease (indication)
            if etype == "indication" and src_type == "drug" and tgt_type == "disease":
                self._drug_indications[src_name].append(tgt_name)
                norm = self._normalized_names.get(tgt_name, tgt_name)
                self._disease_drugs[norm].append(src_name)

            # Drug → Disease (off-label)
            if etype == "off-label use" and src_type == "drug" and tgt_type == "disease":
                norm = self._normalized_names.get(tgt_name, tgt_name)
                self._disease_drugs[norm].append(src_name)

            # Drug contraindications
            if etype == "contraindication" and src_type == "drug":
                self._drug_contraindications[src_name].append(tgt_name)

    # ================================================================
    # Name Normalization (Multi-Tier)
    # ================================================================

    def _normalize(self, primekg_name: str) -> Optional[str]:
        """
        Multi-tier name normalization: PrimeKG name → KB name.

        Returns None if no match found (disease not in KB).
        """
        name = primekg_name.lower().strip()

        # Tier 1: Exact match in KB
        if name in self._kb_diseases:
            return name

        # Tier 2: Curated mapping
        if name in COMMON_DISEASE_MAP:
            mapped = COMMON_DISEASE_MAP[name]
            if mapped.lower() in self._kb_diseases:
                return mapped.lower()

        # Tier 3: Substring — check if any KB disease name contains this name or vice versa
        for kb_name in self._kb_diseases:
            if name in kb_name or kb_name in name:
                return kb_name

        # Tier 4: Keyword extraction — strip noise words and match
        stripped = name
        for word in STRIP_WORDS:
            stripped = stripped.replace(word, "")
        stripped = " ".join(stripped.split())  # collapse whitespace
        if stripped and len(stripped) > 3:
            for kb_name in self._kb_diseases:
                kb_stripped = kb_name
                for word in STRIP_WORDS:
                    kb_stripped = kb_stripped.replace(word, "")
                kb_stripped = " ".join(kb_stripped.split())
                if stripped == kb_stripped:
                    return kb_name

        # No match — return original (PrimeKG-only disease)
        return None

    def normalize_disease_name(self, primekg_name: str) -> Optional[str]:
        """Public API: normalize a PrimeKG disease name to KB name."""
        return self._normalized_names.get(primekg_name.lower().strip())

    # ================================================================
    # Data Extraction for CausalGraphBuilder
    # ================================================================

    def get_nodes_for_builder(self) -> Dict[str, Any]:
        """
        Return nodes dict with normalized disease names.
        Ready for CausalGraphBuilder consumption.
        """
        result = {}
        for nid, ninfo in self.raw_nodes.items():
            ntype = ninfo.get("type", "")
            name = ninfo.get("name", "").lower().strip()

            # Normalize disease names
            if ntype == "disease" and name in self._normalized_names:
                result[nid] = {
                    "id": nid,
                    "name": self._normalized_names[name],
                    "type": ntype,
                }
            else:
                result[nid] = ninfo

        return result

    def get_edges_for_builder(self) -> List[Dict[str, Any]]:
        """
        Return edges with only the types CausalGraphBuilder handles:
        - phenotype present → DiagnosticGraph (suggests)
        - phenotype absent → DiagnosticGraph (excludes)
        - indication → TreatmentGraph (treats)
        - off-label use → TreatmentGraph (treats)
        - contraindication → TreatmentGraph (contraindicated_with)
        """
        usable_types = {
            "phenotype present", "phenotype absent",
            "indication", "off-label use", "contraindication",
        }

        result = []
        for edge in self.raw_edges:
            etype = edge.get("edge_type", "")
            if etype in usable_types:
                result.append(edge)

        return result

    # ================================================================
    # Data Extraction for DiseaseSampler / SymptomGenerator
    # ================================================================

    def get_disease_symptom_map(self) -> Dict[str, List[str]]:
        """
        disease_name → [phenotype names] for ALL diseases with phenotype data.
        Includes both KB-matched and PrimeKG-only diseases.
        """
        return dict(self._disease_symptoms)

    def get_disease_drug_map(self) -> Dict[str, List[str]]:
        """disease_name → [drug names] for all diseases with indication edges."""
        return dict(self._disease_drugs)

    def get_drug_contraindication_map(self) -> Dict[str, List[str]]:
        """drug_name → [contraindicated conditions]."""
        return dict(self._drug_contraindications)

    def get_symptom_overlap_map(self, min_overlap: float = 0.2) -> Dict[str, Dict[str, float]]:
        """
        Compute Jaccard similarity of symptom sets between diseases.

        Returns:
            {disease_a: {disease_b: jaccard_score, ...}, ...}

        Only includes overlaps >= min_overlap.
        """
        # Build symptom sets (excluding negative markers)
        symptom_sets: Dict[str, set] = {}
        for disease, symptoms in self._disease_symptoms.items():
            positive = {s for s in symptoms if not s.startswith("!")}
            if len(positive) >= 3:  # Only diseases with enough symptoms
                symptom_sets[disease] = positive

        overlaps: Dict[str, Dict[str, float]] = {}
        disease_list = list(symptom_sets.keys())

        # For efficiency, only compute for diseases in KB or top PrimeKG diseases
        target_diseases = set()
        if self.kb:
            target_diseases = self._kb_diseases
        # Also add diseases with 5+ symptoms
        for d, s in symptom_sets.items():
            if len(s) >= 5:
                target_diseases.add(d)

        for disease in target_diseases:
            if disease not in symptom_sets:
                continue
            set_a = symptom_sets[disease]
            overlaps[disease] = {}

            for other in disease_list:
                if other == disease:
                    continue
                set_b = symptom_sets[other]
                if len(set_b) < 3:
                    continue

                intersection = len(set_a & set_b)
                union = len(set_a | set_b)
                if union == 0:
                    continue
                jaccard = intersection / union

                if jaccard >= min_overlap:
                    overlaps[disease][other] = round(jaccard, 3)

        return overlaps

    def get_kb_diseases_with_primekg_data(self) -> Dict[str, Dict[str, Any]]:
        """
        For each KB disease, return the PrimeKG data we could match.

        Returns:
            {kb_disease_name: {"symptoms": int, "drugs": int, "overlap_diseases": int}}
        """
        result = {}
        for kb_disease in self._kb_diseases:
            symptoms = self._disease_symptoms.get(kb_disease, [])
            drugs = self._disease_drugs.get(kb_disease, [])
            positive_symptoms = [s for s in symptoms if not s.startswith("!")]

            result[kb_disease] = {
                "symptoms": len(positive_symptoms),
                "negative_symptoms": len(symptoms) - len(positive_symptoms),
                "drugs": len(set(drugs)),
                "has_primekg_data": len(positive_symptoms) > 0 or len(drugs) > 0,
            }
        return result

    def get_statistics(self) -> Dict[str, Any]:
        """Get bridge statistics."""
        kb_diseases_with_data = sum(
            1 for d in self._kb_diseases
            if self._disease_symptoms.get(d) or self._disease_drugs.get(d)
        )
        total_diseases_with_symptoms = sum(
            1 for s in self._disease_symptoms.values() if s
        )
        total_diseases_with_drugs = sum(
            1 for d in self._disease_drugs.values() if d
        )

        return {
            "total_primekg_nodes": len(self.raw_nodes),
            "total_primekg_edges": len(self.raw_edges),
            "kb_diseases_total": len(self._kb_diseases),
            "kb_diseases_with_primekg_data": kb_diseases_with_data,
            "normalized_names": len(self._normalized_names),
            "diseases_with_symptoms": total_diseases_with_symptoms,
            "diseases_with_drugs": total_diseases_with_drugs,
            "drugs_with_contraindications": sum(
                1 for c in self._drug_contraindications.values() if c
            ),
        }
