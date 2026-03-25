"""Clinical Data Sources Package

This package provides adapters and integrations for various medical data sources
including clinical dialogues and knowledge graphs.
"""

from .clinical_data_adapter import ClinicalDataAdapter
from .knowledge_graph_adapter import KnowledgeGraphAdapter

__all__ = [
    'ClinicalDataAdapter',
    'KnowledgeGraphAdapter',
]
