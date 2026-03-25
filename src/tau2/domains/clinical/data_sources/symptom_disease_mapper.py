"""Symptom to Disease Mapper

Uses clinical data and knowledge graph to establish relationships
between symptoms and diseases for medical consultation tasks.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict, Counter
from enum import Enum

logger = logging.getLogger(__name__)


class SymptomSeverity(Enum):
    """Symptom severity levels"""
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


class SymptomDiseaseMapper:
    """
    Maps symptoms to diseases using clinical data and knowledge graph

    Provides:
    - Symptom to likely diseases mapping
    - Disease to typical symptoms mapping
    - Symptom co-occurrence statistics
    - Clinical consistency validation
    """

    def __init__(self, clinical_integration, knowledge_graph_adapter):
        """
        Initialize symptom-disease mapper

        Args:
            clinical_integration: ClinicalDataIntegration instance
            knowledge_graph_adapter: KnowledgeGraphAdapter instance
        """
        self.clinical = clinical_integration
        self.kg = knowledge_graph_adapter

        # Mappings
        self._symptom_to_diseases: Dict[str, List[Tuple[str, float]]] = {}  # symptom -> [(disease, score)]
        self._disease_to_symptoms: Dict[str, List[str]] = {}  # disease -> [symptoms]
        self._symptom_cooccurrence: Dict[Tuple[str, ...], int] = Counter()  # (symptom1, symptom2) -> count
        self._department_diseases: Dict[str, List[str]] = {}  # department -> [diseases]

        # Build mappings
        self._build_mappings()

    def _build_mappings(self):
        """Build all mappings from data sources"""
        logger.info("Building symptom-disease mappings...")

        # Build from clinical data (Chinese MedDialog)
        self._build_from_clinical_data()

        # Build from knowledge graph (PrimeKG)
        if self.kg.is_available():
            self._build_from_knowledge_graph()

        # Build co-occurrence statistics
        self._build_cooccurrence_stats()

        # Build department-disease mapping
        self._build_department_mappings()

        logger.info(f"Built mappings for {len(self._symptom_to_diseases)} symptoms "
                    f"and {len(self._disease_to_symptoms)} diseases")

    def _build_from_clinical_data(self):
        """Build symptom-disease mappings from Chinese MedDialog"""
        if not self.clinical.chinese_medialog_db:
            logger.warning("Chinese MedDialog DB not available")
            return

        # Extract disease-symptom patterns from QA pairs
        symptom_disease_counts = defaultdict(lambda: defaultdict(int))
        disease_symptom_counts = defaultdict(lambda: defaultdict(int))

        for qa_id, qa in self.clinical.chinese_medialog_db.items():
            question = qa.get('question', '')
            answer = qa.get('answer', '')

            # Extract symptoms and diseases
            symptoms = self.clinical.extract_symptoms_from_text(f"{question} {answer}")
            diseases = self._extract_diseases_from_text(answer)

            # Count co-occurrences
            for symptom in symptoms:
                for disease in diseases:
                    symptom_disease_counts[symptom][disease] += 1
                    disease_symptom_counts[disease][symptom] += 1

        # Convert to probability scores
        for symptom, disease_counts in symptom_disease_counts.items():
            total = sum(disease_counts.values())
            diseases_with_scores = [
                (disease, count / total)
                for disease, count in disease_counts.items()
            ]
            # Sort by score and take top diseases
            diseases_with_scores.sort(key=lambda x: x[1], reverse=True)
            self._symptom_to_diseases[symptom] = diseases_with_scores[:10]  # Top 10

        for disease, symptom_counts in disease_symptom_counts.items():
            # Sort by frequency and take top symptoms
            symptoms_sorted = sorted(
                symptom_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )
            self._disease_to_symptoms[disease] = [s for s, _ in symptoms_sorted[:10]]

    def _extract_diseases_from_text(self, text: str) -> List[str]:
        """Extract disease names from medical text"""
        # Common diseases in Chinese internal medicine
        common_diseases = [
            "高血压", "糖尿病", "冠心病", "感冒", "肺炎", "胃炎", "肠炎",
            "支气管炎", "哮喘", "偏头痛", "失眠", "便秘", "腹泻",
            "关节炎", "颈椎病", "腰椎间盘突出", "贫血", "心律失常",
            "心肌炎", "肾炎", "肾结石", "胆囊炎", "阑尾炎"
        ]

        diseases = []
        for disease in common_diseases:
            if disease in text:
                diseases.append(disease)

        return diseases

    def _build_from_knowledge_graph(self):
        """Build mappings from PrimeKG knowledge graph"""
        if not self.kg.is_available():
            return

        # Extract disease-symptom relationships from PrimeKG
        # PrimeKG has edges with relations like "has_symptom", "causes", "presents_as"

        # This is a simplified implementation
        # In production, parse the actual PrimeKG structure
        diseases = self.kg.get_all_diseases()

        for disease in diseases:
            # Get symptoms for this disease from KG
            symptoms = self.kg.get_disease_symptoms(disease)
            if symptoms:
                if disease not in self._disease_to_symptoms:
                    self._disease_to_symptoms[disease] = []
                self._disease_to_symptoms[disease].extend(symptoms)

                # Reverse mapping
                for symptom in symptoms:
                    if symptom not in self._symptom_to_diseases:
                        self._symptom_to_diseases[symptom] = []

                    # Add or update score
                    existing = [
                        (d, score) for d, score in self._symptom_to_diseases[symptom]
                        if d == disease
                    ]

                    if existing:
                        # Update score
                        # In production, this would use KG confidence
                        pass
                    else:
                        # Add with high confidence (from KG)
                        self._symptom_to_diseases[symptom].append((disease, 0.9))

    def _build_cooccurrence_stats(self):
        """Build symptom co-occurrence statistics"""
        if not self.clinical.chinese_medialog_db:
            return

        # Analyze Chinese MedDialog for symptom co-occurrence
        for qa_id, qa in self.clinical.chinese_medialog_db.items():
            text = f"{qa.get('question', '')} {qa.get('answer', '')}"
            symptoms = self.clinical.extract_symptoms_from_text(text)

            # Count co-occurrences
            for i, symptom1 in enumerate(symptoms):
                for symptom2 in symptoms[i+1:]:
                    pair = tuple(sorted([symptom1, symptom2]))
                    self._symptom_cooccurrence[pair] += 1

    def _build_department_mappings(self):
        """Build department to disease mappings"""
        departments = ["内科", "外科", "妇产科", "儿科", "男科", "肿瘤科"]

        for dept in departments:
            patterns = self.clinical.get_department_patterns(dept)
            diseases = patterns.get("common_diseases", [])
            self._department_diseases[dept] = diseases

    # === Query Methods ===

    def get_likely_diseases(
        self,
        symptoms: List[str],
        top_k: int = 5,
        min_score: float = 0.1
    ) -> List[Tuple[str, float]]:
        """
        Get likely diseases based on symptoms

        Args:
            symptoms: List of patient symptoms
            top_k: Number of top diseases to return
            min_score: Minimum confidence score

        Returns:
            List of (disease, score) tuples, sorted by score descending
        """
        disease_scores = defaultdict(float)

        # Aggregate scores from all symptoms
        for symptom in symptoms:
            if symptom in self._symptom_to_diseases:
                for disease, score in self._symptom_to_diseases[symptom]:
                    disease_scores[disease] += score

        # Normalize by number of symptoms
        for disease in disease_scores:
            disease_scores[disease] /= len(symptoms)

        # Sort and filter
        results = [
            (disease, score)
            for disease, score in disease_scores.items()
            if score >= min_score
        ]
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:top_k]

    def get_disease_symptoms(self, disease: str) -> List[str]:
        """Get typical symptoms for a disease"""
        return self._disease_to_symptoms.get(disease, [])

    def get_symptom_cooccurrence(self, symptom1: str, symptom2: str) -> int:
        """Get co-occurrence count of two symptoms"""
        pair = tuple(sorted([symptom1, symptom2]))
        return self._symptom_cooccurrence.get(pair, 0)

    def get_related_symptoms(self, symptom: str, top_k: int = 5) -> List[Tuple[str, int]]:
        """Get symptoms that often co-occur with a given symptom"""
        related = []

        for (s1, s2), count in self._symptom_cooccurrence.items():
            if s1 == symptom:
                related.append((s2, count))
            elif s2 == symptom:
                related.append((s1, count))

        related.sort(key=lambda x: x[1], reverse=True)
        return related[:top_k]

    def validate_consistency(
        self,
        symptoms: List[str],
        disease: str,
        threshold: float = 0.3
    ) -> Dict[str, Any]:
        """
        Validate if symptoms are consistent with the disease

        Args:
            symptoms: List of symptoms
            disease: Disease name
            threshold: Minimum overlap threshold

        Returns:
            Validation result with:
            - is_consistent: bool
            - overlap_score: float
            - missing_symptoms: List[str]
            - unexpected_symptoms: List[str]
        """
        expected_symptoms = set(self.get_disease_symptoms(disease))
        provided_symptoms = set(symptoms)

        overlap = expected_symptoms & provided_symptoms
        overlap_score = len(overlap) / len(expected_symptoms) if expected_symptoms else 0

        missing_symptoms = list(expected_symptoms - provided_symptoms)
        unexpected_symptoms = list(provided_symptoms - expected_symptoms)

        is_consistent = overlap_score >= threshold

        return {
            "is_consistent": is_consistent,
            "overlap_score": overlap_score,
            "missing_symptoms": missing_symptoms,
            "unexpected_symptoms": unexpected_symptoms,
            "coverage": f"{overlap_score:.1%}"
        }

    def get_symptom_severity(self, symptom: str, context: Optional[str] = None) -> str:
        """
        Get severity level for a symptom

        Args:
            symptom: Symptom name
            context: Additional context (optional)

        Returns:
            Severity level (mild/moderate/severe/critical)
        """
        # Critical symptoms that need immediate attention
        critical_symptoms = [
            "胸痛", "呼吸困难", "严重头痛", "意识障碍", "昏迷",
            "大出血", "休克"
        ]

        # Severe symptoms
        severe_symptoms = [
            "高热", "持续呕吐", "剧烈疼痛", "血便", "黑便"
        ]

        if symptom in critical_symptoms:
            return SymptomSeverity.CRITICAL.value
        elif symptom in severe_symptoms:
            return SymptomSeverity.SEVERE.value
        else:
            return SymptomSeverity.MODERATE.value

    def suggest_additional_inquiry(
        self,
        symptoms: List[str],
        department: Optional[str] = None
    ) -> List[str]:
        """
        Suggest additional questions to ask based on symptoms

        Args:
            symptoms: Current symptoms
            department: Medical department (optional)

        Returns:
            List of suggested questions
        """
        questions = []

        # Check for red flag symptoms
        for symptom in symptoms:
            severity = self.get_symptom_severity(symptom)
            if severity in [SymptomSeverity.CRITICAL.value, SymptomSeverity.SEVERE.value]:
                questions.append(f"{symptom}的严重程度和持续时间？")
                questions.append(f"{symptom}伴随的其他症状？")

        # Check for missing common info
        if "发热" not in symptoms:
            questions.append("是否有发热？")

        if "疼痛" not in " ".join(symptoms):
            # Check if any symptom mentions pain
            if not any("痛" in s for s in symptoms):
                questions.append("是否有疼痛症状？")

        return questions

    def expand_symptoms_from_department(
        self,
        department: str,
        presented_symptoms: List[str]
    ) -> List[str]:
        """
        Expand symptom list based on department patterns

        For example, if patient says "headache" in neurology,
        suggest asking about related symptoms

        Args:
            department: Medical department
            presented_symptoms: Symptoms patient mentions

        Returns:
            Additional symptoms to ask about
        """
        patterns = self.clinical.get_department_patterns(department)
        additional = []

        # If patient mentions one symptom, ask about related symptoms
        common_symptoms = patterns.get("common_symptoms", [])

        for symptom in common_symptoms:
            if symptom not in presented_symptoms:
                additional.append(symptom)

        return additional


def get_symptom_disease_mapper(clinical_integration, knowledge_graph_adapter) -> SymptomDiseaseMapper:
    """Factory function to get symptom-disease mapper instance"""
    return SymptomDiseaseMapper(clinical_integration, knowledge_graph_adapter)
