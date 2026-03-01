"""Base adapter ABC for clinical data sources."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from UniClinicalDataEngine.models import ClinicalScenario, PatientRecord


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

        Returns:
            List of ClinicalScenarios.
        """
        raw_records = self.load_raw_data()
        scenarios = []
        for i, raw in enumerate(raw_records):
            record = self.normalize_record(raw)
            scenario = self.build_scenario(record, i)
            scenarios.append(scenario)
        return scenarios
