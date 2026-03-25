"""Knowledge Graph Adapter

Provides interface to PrimeKG knowledge graph for medical relationships
including disease-symptom, drug-disease, and treatment information.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Any

logger = logging.getLogger(__name__)


class KnowledgeGraphAdapter:
    """
    Adapter for PrimeKG Knowledge Graph

    PrimeKG is a biomedical knowledge graph that integrates:
    - Drugs, diseases, proteins, genes, side effects
    - Disease-symptom relationships
    - Drug-disease treatments
    - Drug-drug interactions
    """

    def __init__(self, kg_data_path: Optional[str] = None):
        """
        Initialize knowledge graph adapter

        Args:
            kg_data_path: Path to PrimeKG cache directory
        """
        if kg_data_path is None:
            # Try default location
            kg_data_path = Path(__file__).parents[4] / "data" / "primekg_cache"

        self.kg_path = Path(kg_data_path)

        # Knowledge graph data
        self._nodes: List[Dict] = []
        self._edges: List[Dict] = []
        self._node_map: Dict[str, Dict] = {}  # id -> node
        self._disease_nodes: List[str] = []
        self._drug_nodes: List[str] = []

        # Indexes for fast lookup
        self._disease_symptoms: Dict[str, Set[str]] = {}  # disease -> {symptoms}
        self._drug_diseases: Dict[str, Set[str]] = {}     # drug -> {diseases}

        # Load data if available
        self._load_kg_data()

    def _load_kg_data(self):
        """Load PrimeKG data from cache"""
        if not self.kg_path.exists():
            logger.warning(f"PrimeKG cache not found at {self.kg_path}")
            return

        logger.info(f"Loading PrimeKG data from {self.kg_path}")

        # Load nodes
        nodes_file = self.kg_path / "primekg_filtered_nodes.json"
        if nodes_file.exists():
            with open(nodes_file, 'r', encoding='utf-8') as f:
                self._nodes = json.load(f)

            # Build node map and extract diseases/drugs
            for node in self._nodes:
                node_id = node.get('id', '')
                self._node_map[node_id] = node

                # Categorize by type
                node_type = node.get('type', '')
                if 'disease' in node_type.lower():
                    self._disease_nodes.append(node_id)
                elif 'drug' in node_type.lower() or 'chemical' in node_type.lower():
                    self._drug_nodes.append(node_id)

        # Load edges
        edges_file = self.kg_path / "primekg_filtered_edges.json"
        if edges_file.exists():
            with open(edges_file, 'r', encoding='utf-8') as f:
                self._edges = json.load(f)

        # Build indexes
        self._build_indexes()

        logger.info(f"Loaded {len(self._nodes)} nodes and {len(self._edges)} edges")
        logger.info(f"Found {len(self._disease_nodes)} diseases and {len(self._drug_nodes)} drugs")

    def _build_indexes(self):
        """Build lookup indexes for common queries"""
        # Build disease-symptom index
        for edge in self._edges:
            source = edge.get('source', '')
            target = edge.get('target', '')
            relation = edge.get('relation', '').lower()

            if 'diseas' in self._node_map.get(source, {}).get('type', '').lower():
                # Source is a disease
                disease_id = source

                # Check if relation indicates symptom
                if 'symptom' in relation:
                    if target not in self._disease_symptoms:
                        self._disease_symptoms[disease_id] = set()

                    # Extract symptom name from target node
                    target_node = self._node_map.get(target, {})
                    symptom_name = target_node.get('name', target)

                    self._disease_symptoms[disease_id].add(symptom_name)

            # Build drug-disease index
            if 'drug' in self._node_map.get(source, {}).get('type', '').lower():
                drug_id = source

                if 'treats' in relation or 'indication' in relation:
                    if target not in self._drug_diseases:
                        self._drug_diseases[drug_id] = set()

                    self._drug_diseases[drug_id].add(target)

    def is_available(self) -> bool:
        """Check if knowledge graph data is available"""
        return len(self._nodes) > 0 and len(self._edges) > 0

    def get_all_diseases(self) -> List[str]:
        """Get all disease IDs"""
        return self._disease_nodes.copy()

    def get_all_drugs(self) -> List[str]:
        """Get all drug IDs"""
        return self._drug_nodes.copy()

    def get_disease_symptoms(self, disease_id: str) -> List[str]:
        """
        Get symptoms for a disease

        Args:
            disease_id: Disease identifier

        Returns:
            List of symptom names
        """
        if disease_id not in self._disease_symptoms:
            # Fallback: try to get from node directly
            node = self._node_map.get(disease_id, {})
            # This would need implementation based on PrimeKG structure
            return []

        return list(self._disease_symptoms[disease_id])

    def get_drug_treatments(self, disease_id: str) -> List[str]:
        """
        Get drugs that treat a disease

        Args:
            disease_id: Disease identifier

        Returns:
            List of drug IDs
        """
        treatments = []

        for drug_id, diseases in self._drug_diseases.items():
            if disease_id in diseases:
                treatments.append(drug_id)

        return treatments

    def get_drug_info(self, drug_id: str) -> Optional[Dict]:
        """
        Get information about a drug

        Args:
            drug_id: Drug identifier

        Returns:
            Drug information dictionary
        """
        return self._node_map.get(drug_id)

    def get_disease_info(self, disease_id: str) -> Optional[Dict]:
        """
        Get information about a disease

        Args:
            disease_id: Disease identifier

        Returns:
            Disease information dictionary
        """
        return self._node_map.get(disease_id)

    def search_diseases_by_keyword(self, keyword: str) -> List[Dict]:
        """
        Search diseases by keyword in name

        Args:
            keyword: Search keyword

        Returns:
            List of matching disease nodes
        """
        keyword_lower = keyword.lower()

        matches = []
        for disease_id in self._disease_nodes:
            node = self._node_map.get(disease_id, {})
            name = node.get('name', '')

            if keyword_lower in name.lower():
                matches.append(node)

        return matches

    def search_drugs_by_keyword(self, keyword: str) -> List[Dict]:
        """
        Search drugs by keyword in name

        Args:
            keyword: Search keyword

        Returns:
            List of matching drug nodes
        """
        keyword_lower = keyword.lower()

        matches = []
        for drug_id in self._drug_nodes:
            node = self._node_map.get(drug_id, {})
            name = node.get('name', '')

            if keyword_lower in name.lower():
                matches.append(node)

        return matches

    def check_drug_interactions(self, drug_ids: List[str]) -> List[Dict]:
        """
        Check for interactions between drugs

        Args:
            drug_ids: List of drug identifiers

        Returns:
            List of interaction records
        """
        interactions = []

        # This would require analyzing drug-drug edges in PrimeKG
        # Simplified implementation
        for i, drug1 in enumerate(drug_ids):
            for drug2 in drug_ids[i+1:]:
                # Check if there's an interaction edge
                # Implementation depends on PrimeKG structure
                pass

        return interactions

    def get_common_pathways(
        self,
        start_node: str,
        end_node: str,
        max_depth: int = 3
    ) -> List[List[str]]:
        """
        Find common pathways between two nodes in the knowledge graph

        Args:
            start_node: Starting node ID
            end_node: Ending node ID
            max_depth: Maximum path length

        Returns:
            List of paths (each path is a list of node IDs)
        """
        # This would implement a graph traversal algorithm
        # For now, return empty
        return []

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the knowledge graph"""
        return {
            "total_nodes": len(self._nodes),
            "total_edges": len(self._edges),
            "disease_count": len(self._disease_nodes),
            "drug_count": len(self._drug_nodes),
            "diseases_with_symptoms": len(self._disease_symptoms),
            "drugs_with_treatments": len(self._drug_diseases)
        }


def get_knowledge_graph_adapter(kg_data_path: Optional[str] = None) -> KnowledgeGraphAdapter:
    """Factory function to get knowledge graph adapter instance"""
    return KnowledgeGraphAdapter(kg_data_path)
