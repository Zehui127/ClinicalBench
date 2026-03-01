"""Main orchestrator: adapter registry, pipeline execution, file output."""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from UniClinicalDataEngine.adapters.base import BaseAdapter
from UniClinicalDataEngine.adapters.csv_adapter import CSVAdapter
from UniClinicalDataEngine.adapters.json_adapter import JSONAdapter
from UniClinicalDataEngine.adapters.nhands_adapter import NHandsAdapter
from UniClinicalDataEngine.db_builder import ClinicalDBBuilder
from UniClinicalDataEngine.models import ClinicalScenario, EngineConfig
from UniClinicalDataEngine.policy_generator import ClinicalPolicyGenerator
from UniClinicalDataEngine.task_builder import ClinicalTaskBuilder
from UniClinicalDataEngine.tool_generator import (
    generate_tool_definitions,
    get_default_clinical_tools,
)


# Built-in adapter registry
_ADAPTER_REGISTRY: Dict[str, Type[BaseAdapter]] = {
    "nhands": NHandsAdapter,
    "csv": CSVAdapter,
    "json": JSONAdapter,
}


class UniClinicalDataEngine:
    """Orchestrates the clinical data pipeline.

    Takes raw clinical data through adapters, builds tau2-bench compatible
    tasks, database, tools, and policy files.
    """

    def __init__(self, config: EngineConfig):
        self.config = config
        self.adapter: Optional[BaseAdapter] = None
        self.scenarios: List[ClinicalScenario] = []

    @classmethod
    def register_adapter(cls, name: str, adapter_cls: Type[BaseAdapter]) -> None:
        """Register a custom adapter type.

        Args:
            name: The source type name to register.
            adapter_cls: The adapter class (must subclass BaseAdapter).
        """
        _ADAPTER_REGISTRY[name] = adapter_cls

    def _create_adapter(self) -> BaseAdapter:
        """Create an adapter instance based on the config."""
        source_type = self.config.source_type.lower()
        if source_type not in _ADAPTER_REGISTRY:
            raise ValueError(
                f"Unknown source type '{source_type}'. "
                f"Available: {list(_ADAPTER_REGISTRY.keys())}"
            )
        adapter_cls = _ADAPTER_REGISTRY[source_type]
        kwargs = self.config.adapter_kwargs or {}
        return adapter_cls(source_path=self.config.source_path, **kwargs)

    def run(self) -> Dict[str, Any]:
        """Execute the full pipeline: extract scenarios, build tasks/db/policy/tools.

        Returns:
            Dict with keys: tasks, db, policy, tools, scenarios
        """
        # 1. Create adapter and extract scenarios
        self.adapter = self._create_adapter()
        self.scenarios = self.adapter.extract_scenarios()

        if not self.scenarios:
            raise ValueError("No scenarios were extracted from the data source.")

        # 2. Build tau2 tasks
        task_builder = ClinicalTaskBuilder(domain_name=self.config.domain_name)
        tasks = task_builder.build_tasks(self.scenarios)

        # 3. Build database
        db_builder = ClinicalDBBuilder()
        db = db_builder.build_db(self.scenarios)

        # 4. Generate policy
        policy_gen = ClinicalPolicyGenerator(domain_name=self.config.domain_name)
        policy = policy_gen.generate()

        # 5. Generate tool definitions
        clinical_tools = get_default_clinical_tools()
        tool_defs = generate_tool_definitions(clinical_tools)

        return {
            "tasks": tasks,
            "db": db,
            "policy": policy,
            "tools": tool_defs,
            "scenarios": self.scenarios,
        }

    def run_and_save(self) -> Path:
        """Execute the pipeline and save all output files.

        Returns:
            Path to the output directory.
        """
        results = self.run()
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save tasks.json
        tasks_data = [t.model_dump(exclude_none=True) for t in results["tasks"]]
        tasks_path = output_dir / "tasks.json"
        with open(tasks_path, "w") as f:
            json.dump(tasks_data, f, indent=2, default=str)

        # Save db.json
        db_path = output_dir / "db.json"
        with open(db_path, "w") as f:
            json.dump(results["db"], f, indent=2, default=str)

        # Save policy.md
        policy_path = output_dir / "policy.md"
        with open(policy_path, "w") as f:
            f.write(results["policy"])

        # Save tools.json
        tools_path = output_dir / "tools.json"
        with open(tools_path, "w") as f:
            json.dump(results["tools"], f, indent=2)

        return output_dir
