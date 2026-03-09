"""Base adapter ABC for clinical data sources."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import importlib.util
from pathlib import Path

# Import from models.py file directly to avoid conflict with models/ directory
_models_spec = importlib.util.spec_from_file_location(
    "uni_clinical_models",
    Path(__file__).parent.parent / "models.py"
)
_models_module = importlib.util.module_from_spec(_models_spec)
_models_spec.loader.exec_module(_models_module)
ClinicalScenario = _models_module.ClinicalScenario
PatientRecord = _models_module.PatientRecord


class BaseAdapter(ABC):
    """Abstract base class for clinical data source adapters.

    Subclasses must implement three methods:
      - load_raw_data: load raw records from the data source
      - normalize_record: convert a raw record into a PatientRecord
      - build_scenario: convert a PatientRecord into a ClinicalScenario
    """

    def __init__(self, source_path: str, **kwargs: Any):
        self.source_path = source_path
        self.kwargs = kwargs
        self._task_processor = kwargs.get("task_processor")

    @abstractmethod
    def load_raw_data(self) -> List[Dict[str, Any]]:
        """Load raw records from the data source.

        Returns:
            List of raw record dictionaries.
        """
        ...

    @abstractmethod
    def normalize_record(self, raw_record: Dict[str, Any]) -> PatientRecord:
        """Convert a raw record into a normalized PatientRecord.

        Args:
            raw_record: A single raw record dictionary.

        Returns:
            A normalized PatientRecord.
        """
        ...

    @abstractmethod
    def build_scenario(self, record: PatientRecord, index: int) -> ClinicalScenario:
        """Convert a PatientRecord into a ClinicalScenario.

        Args:
            record: A normalized PatientRecord.
            index: The index of this record in the dataset.

        Returns:
            A ClinicalScenario ready for task building.
        """
        ...

    def extract_scenarios(self) -> List[ClinicalScenario]:
        """Template method: load -> normalize -> build for all records.

        Optionally applies post-processing (deduplication and merging) if
        a task_processor is configured.

        Returns:
            List of ClinicalScenarios.
        """
        raw_records = self.load_raw_data()
        scenarios = []
        for i, raw in enumerate(raw_records):
            record = self.normalize_record(raw)
            scenario = self.build_scenario(record, i)
            scenarios.append(scenario)

        # Apply post-processing if task processor is configured
        if self._task_processor is not None:
            scenarios = self._task_processor.process(scenarios)

        return scenarios
