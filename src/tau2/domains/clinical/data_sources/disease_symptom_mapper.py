# Copyright Sierra

"""
Disease-Symptom Mapper

Maps diseases to symptoms using the PrimeKG knowledge graph.
Provides functionality to generate medically accurate user personas
based on disease-symptom relationships.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set

from tau2.data_model.medical_tasks import (
    DiseaseSymptomMapping,
    MedicalPersona,
)

logger = logging.getLogger(__name__)


class DiseaseSymptomMapper:
    """
    Maps diseases to symptoms using knowledge graph data.

    This class provides methods to:
    1. Get symptoms for a specific disease
    2. Find diseases that match a set of symptoms
    3. Generate medical personas based on disease
    4. Validate symptom-disease relationships
    """

    def __init__(self, kg_adapter=None):
        """
        Initialize the disease-symptom mapper.

        Args:
            kg_adapter: Optional KnowledgeGraphAdapter instance.
                       If None, will attempt to load data directly.
        """
        self.kg_adapter = kg_adapter

        # Caches
        self._symptom_cache: Dict[str, List[str]] = {}
        self._disease_cache: Dict[str, Dict] = {}
        self._reverse_index: Dict[str, Set[str]] = {}  # symptom -> diseases

        # Load data if available
        if kg_adapter is not None:
            self._load_from_kg_adapter()
        else:
            self._load_from_direct_file()

    def _load_from_kg_adapter(self):
        """Load disease-symptom mappings from knowledge graph adapter."""
        if not self.kg_adapter or not self.kg_adapter.is_available():
            logger.warning("Knowledge graph adapter not available")
            return

        logger.info("Loading disease-symptom mappings from knowledge graph")

        # Get all diseases
        diseases = self.kg_adapter.get_all_diseases()
        logger.info(f"Found {len(diseases)} diseases in knowledge graph")

        # Build mappings
        for disease_id in diseases:
            symptoms = self.kg_adapter.get_disease_symptoms(disease_id)
            if symptoms:
                self._symptom_cache[disease_id] = symptoms
                disease_info = self.kg_adapter.get_disease_info(disease_id)
                if disease_info:
                    self._disease_cache[disease_id] = disease_info

                # Build reverse index
                for symptom in symptoms:
                    if symptom not in self._reverse_index:
                        self._reverse_index[symptom] = set()
                    self._reverse_index[symptom].add(disease_id)

        logger.info(f"Loaded {len(self._symptom_cache)} disease-symptom mappings")

    def _load_from_direct_file(self):
        """Load disease-symptom mappings directly from data files."""
        # Try to load from clinical data directory
        data_dir = Path(__file__).parents[4] / "data" / "clinical_data"

        symptom_file = data_dir / "disease_symptoms.json"
        if symptom_file.exists():
            try:
                with open(symptom_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._symptom_cache = data.get("mappings", {})
                    logger.info(f"Loaded {len(self._symptom_cache)} disease-symptom mappings from file")
            except Exception as e:
                logger.error(f"Failed to load disease-symptom file: {e}")

    def get_symptoms_for_disease(self, disease_id: str) -> List[str]:
        """
        Get symptoms associated with a disease.

        Args:
            disease_id: Disease identifier (can be ID or name)

        Returns:
            List of symptom names
        """
        # Check cache
        if disease_id in self._symptom_cache:
            return self._symptom_cache[disease_id]

        # Try knowledge graph adapter
        if self.kg_adapter:
            symptoms = self.kg_adapter.get_disease_symptoms(disease_id)
            if symptoms:
                self._symptom_cache[disease_id] = symptoms
                return symptoms

            # Try searching by name
            diseases = self.kg_adapter.search_diseases_by_keyword(disease_id)
            if diseases:
                for disease in diseases:
                    did = disease.get('id', '')
                    if did not in self._symptom_cache:
                        self._symptom_cache[did] = self.kg_adapter.get_disease_symptoms(did)

                # Return first match
                for did in self._symptom_cache:
                    if disease_id.lower() in did.lower():
                        return self._symptom_cache[did]

        logger.warning(f"No symptoms found for disease: {disease_id}")
        return []

    def get_disease_info(self, disease_id: str) -> Optional[Dict]:
        """
        Get information about a disease.

        Args:
            disease_id: Disease identifier

        Returns:
            Disease information dictionary or None
        """
        if disease_id in self._disease_cache:
            return self._disease_cache[disease_id]

        if self.kg_adapter:
            info = self.kg_adapter.get_disease_info(disease_id)
            if info:
                self._disease_cache[disease_id] = info
                return info

        return None

    def find_diseases_by_symptoms(
        self,
        symptoms: List[str],
        min_match: int = 2
    ) -> List[Dict]:
        """
        Find diseases that match the given symptoms.

        Args:
            symptoms: List of patient symptoms
            min_match: Minimum number of symptom matches required

        Returns:
            List of candidate diseases with match information
        """
        candidates = []
        symptom_set = set(s.lower() for s in symptoms)

        # Check all diseases in cache
        for disease_id, disease_symptoms in self._symptom_cache.items():
            disease_symptom_set = set(s.lower() for s in disease_symptoms)

            # Count matches
            matches = symptom_set & disease_symptom_set
            match_count = len(matches)

            if match_count >= min_match:
                disease_info = self.get_disease_info(disease_id)
                candidates.append({
                    "disease_id": disease_id,
                    "disease_name": disease_info.get("name", disease_id) if disease_info else disease_id,
                    "match_count": match_count,
                    "total_symptoms": len(disease_symptoms),
                    "matched_symptoms": list(matches),
                    "all_symptoms": disease_symptoms,
                    "match_percentage": match_count / len(disease_symptoms)
                })

        # Sort by match count and percentage
        candidates.sort(key=lambda x: (x["match_count"], x["match_percentage"]), reverse=True)

        return candidates

    def generate_medical_persona(
        self,
        disease_id: str,
        age: int,
        gender: str,
        information_level: str = "partial",
        severity: str = "moderate"
    ) -> MedicalPersona:
        """
        Generate a medical persona based on a disease.

        Args:
            disease_id: Disease to base persona on
            age: Patient age
            gender: Patient gender
            information_level: How much information patient provides
                              (complete/partial/minimal)
            severity: Symptom severity (mild/moderate/severe)

        Returns:
            MedicalPersona object
        """
        # Get symptoms for this disease
        all_symptoms = self.get_symptoms_for_disease(disease_id)

        if not all_symptoms:
            # If no symptoms found, use generic ones
            all_symptoms = ["pain", "discomfort"]

        # Adjust symptoms based on information level
        if information_level == "complete":
            selected_symptoms = all_symptoms
        elif information_level == "partial":
            # Provide about half the symptoms
            selected_symptoms = all_symptoms[:max(1, len(all_symptoms) // 2 + 1)]
        else:  # minimal
            # Provide just one symptom
            selected_symptoms = all_symptoms[:1] if all_symptoms else ["general discomfort"]

        # Get disease info for duration
        disease_info = self.get_disease_info(disease_id)

        # Set reasonable defaults
        duration = "2 weeks"  # Default duration

        return MedicalPersona(
            age=age,
            gender=gender,
            symptoms=selected_symptoms,
            duration=duration,
            severity=severity,
            past_medical_history=[],
            current_medications=[],
            allergies=[],
            lab_results={},
            vital_signs={},
            smoking_status=None,
            alcohol_use=None
        )

    def validate_symptom_disease_relationship(
        self,
        disease_id: str,
        symptoms: List[str]
    ) -> Dict[str, bool]:
        """
        Validate which symptoms are associated with a disease.

        Args:
            disease_id: Disease identifier
            symptoms: List of symptoms to validate

        Returns:
            Dictionary mapping symptom to is_valid boolean
        """
        disease_symptoms = self.get_symptoms_for_disease(disease_id)
        disease_symptom_set = set(s.lower() for s in disease_symptoms)

        validation_results = {}
        for symptom in symptoms:
            validation_results[symptom] = symptom.lower() in disease_symptom_set

        return validation_results

    def get_symptom_prevalence(self, disease_id: str, symptom: str) -> float:
        """
        Get the prevalence of a symptom for a disease.

        Note: This is a simplified implementation returning 1.0 for known symptoms.
        A full implementation would use actual prevalence data.

        Args:
            disease_id: Disease identifier
            symptom: Symptom name

        Returns:
            Prevalence (0.0 to 1.0)
        """
        symptoms = self.get_symptoms_for_disease(disease_id)
        if symptom.lower() in [s.lower() for s in symptoms]:
            return 1.0
        return 0.0

    def get_statistics(self) -> Dict:
        """Get statistics about the mapper."""
        return {
            "total_diseases": len(self._symptom_cache),
            "total_symptoms": len(self._reverse_index),
            "avg_symptoms_per_disease": (
                sum(len(symptoms) for symptoms in self._symptom_cache.values()) /
                len(self._symptom_cache)
                if self._symptom_cache else 0
            )
        }


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_disease_symptom_mapper(kg_adapter=None) -> DiseaseSymptomMapper:
    """
    Factory function to create a DiseaseSymptomMapper.

    Args:
        kg_adapter: Optional KnowledgeGraphAdapter instance

    Returns:
        DiseaseSymptomMapper instance
    """
    return DiseaseSymptomMapper(kg_adapter=kg_adapter)


# ============================================================================
# CLI UTILITY
# ============================================================================

if __name__ == "__main__":
    import sys

    # Setup basic logging
    logging.basicConfig(level=logging.INFO)

    # Create mapper
    mapper = create_disease_symptom_mapper()

    # Print statistics
    stats = mapper.get_statistics()
    print(f"Disease-Symptom Mapper Statistics:")
    print(f"  Total diseases: {stats['total_diseases']}")
    print(f"  Total unique symptoms: {stats['total_symptoms']}")
    print(f"  Average symptoms per disease: {stats['avg_symptoms_per_disease']:.1f}")

    # Example: Find diseases by symptoms
    if len(sys.argv) > 1:
        symptoms = sys.argv[1:]
        print(f"\nSearching for diseases matching symptoms: {symptoms}")
        candidates = mapper.find_diseases_by_symptoms(symptoms)

        print(f"\nTop 5 candidates:")
        for i, candidate in enumerate(candidates[:5], 1):
            print(f"{i}. {candidate['disease_name']}")
            print(f"   Matched: {candidate['match_count']}/{candidate['total_symptoms']} symptoms")
            print(f"   Symptoms: {', '.join(candidate['matched_symptoms'])}")
