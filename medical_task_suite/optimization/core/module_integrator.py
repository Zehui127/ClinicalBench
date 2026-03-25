"""
Module Integrator for Medical Task Suite

This module integrates the 13 core medical capability modules into the
task generation and optimization pipeline.
"""

import os
import yaml
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import random

# Removed dependency on optimization.models - loading configs directly


@dataclass
class ModuleRecommendation:
    """
    Represents a recommended module for a task.

    Attributes:
        module_id: Module identifier
        module_name: Human-readable name
        priority: P0, P1, P2, or P3
        relevance_score: How relevant this module is (0-1)
        confidence: Confidence in the recommendation (0-1)
        reason: Why this module is recommended
    """
    module_id: str
    module_name: str
    priority: str
    relevance_score: float
    confidence: float
    reason: str


@dataclass
class IntegratedRequirements:
    """
    Represents integrated requirements from multiple modules.

    Attributes:
        selected_modules: List of selected module IDs
        module_requirements: Requirements from each module
        evaluation_criteria: Integrated evaluation criteria
        red_line_rules: Applicable red line rules
        patient_behavior_spec: Patient behavior specification
        difficulty_level: Difficulty level
        metadata: Additional metadata
    """
    selected_modules: List[str]
    module_requirements: Dict[str, Dict[str, Any]]
    evaluation_criteria: Dict[str, Any]
    red_line_rules: List[Dict[str, Any]]
    patient_behavior_spec: Dict[str, Any]
    difficulty_level: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class ModuleIntegrator:
    """
    Integrates 13 core medical modules into task generation and optimization.

    This class:
    1. Loads module definitions from configuration files
    2. Selects appropriate modules for tasks based on context
    3. Generates module-specific requirements
    4. Integrates evaluation criteria
    5. Applies red line rules
    """

    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the ModuleIntegrator.

        Args:
            config_dir: Directory containing module configuration files.
                       Defaults to medical_task_suite/config/
        """
        if config_dir is None:
            # Default to medical_task_suite/config
            # Current file: optimization/core/module_integrator.py
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_dir = os.path.join(
                os.path.dirname(os.path.dirname(current_dir)),  # Go up to medical_task_suite/
                'config'
            )

        self.config_dir = config_dir
        self.module_definitions = self._load_module_definitions()
        self.difficulty_levels = self._load_difficulty_levels()
        self.red_line_rules = self._load_red_line_rules()

        # Build indexes for quick lookups
        self._build_indexes()

    def _load_yaml_file(self, filename: str) -> Dict:
        """Load a YAML configuration file."""
        filepath = os.path.join(self.config_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Warning: Config file not found: {filepath}")
            return {}
        except yaml.YAMLError as e:
            print(f"Error loading YAML file {filepath}: {e}")
            return {}

    def _load_module_definitions(self) -> Dict:
        """Load module definitions from module_definitions.yaml."""
        data = self._load_yaml_file('module_definitions.yaml')
        return data.get('modules', {})

    def _load_difficulty_levels(self) -> Dict:
        """Load difficulty level configurations."""
        data = self._load_yaml_file('difficulty_levels.yaml')
        return data.get('difficulty_levels', {})

    def _load_red_line_rules(self) -> Dict:
        """Load red line rules."""
        data = self._load_yaml_file('red_line_rules.yaml')
        return {
            'global': data.get('global_red_lines', []),
            'module_specific': data.get('module_specific_red_lines', {})
        }

    def _build_indexes(self):
        """Build indexes for quick lookups."""
        # Module priority index
        self.priority_groups = {
            'P0': [],
            'P1': [],
            'P2': [],
            'P3': []
        }

        # Scenario-to-module mapping index
        self.scenario_module_map = {}

        # Build name-to-ID and ID-to-config mappings
        self.name_to_id_map = {}
        self.id_to_config_map = {}

        # Build indexes from module definitions
        if self.module_definitions:
            # Get scenario mapping from module_definitions if available
            scenario_mapping = self._load_yaml_file('module_definitions.yaml').get(
                'scenario_module_mapping', {}
            )

            for module_key, module_config in self.module_definitions.items():
                # Build name-to-ID and ID-to-config mappings
                module_id = module_config.get('module_id', module_key)
                self.name_to_id_map[module_key] = module_id
                self.id_to_config_map[module_id] = module_config

                priority = module_config.get('priority', 'P2')
                if priority in self.priority_groups:
                    self.priority_groups[priority].append(module_id)

            # Convert scenario mapping from names to IDs
            self.scenario_module_map = {}
            for scenario, mapping in scenario_mapping.items():
                self.scenario_module_map[scenario] = {
                    'primary_modules': [
                        self.name_to_id_map.get(name, name)
                        for name in mapping.get('primary_modules', [])
                    ],
                    'secondary_modules': [
                        self.name_to_id_map.get(name, name)
                        for name in mapping.get('secondary_modules', [])
                    ]
                }

    def select_modules_for_task(
        self,
        task_context: Dict[str, Any],
        max_modules: int = 3,
        min_coverage: bool = False
    ) -> List[ModuleRecommendation]:
        """
        Select appropriate modules for a task based on context.

        Args:
            task_context: Task context including:
                - scenario_type: Type of scenario (information_query, etc.)
                - difficulty: L1, L2, or L3
                - medical_domain: Medical domain (cardiology, etc.)
                - symptoms: List of symptoms
                - other context
            max_modules: Maximum number of modules to select
            min_coverage: If True, ensure minimum coverage across priorities

        Returns:
            List of ModuleRecommendation objects, sorted by priority and relevance
        """
        scenario_type = task_context.get('scenario_type', 'information_query')
        difficulty = task_context.get('difficulty', 'L1')

        # Get module recommendations based on scenario type
        recommended_module_ids = self._get_module_recommendations(scenario_type)

        # Score each module
        scored_modules = []
        for module_id in recommended_module_ids:
            # Use id_to_config_map to get module config by ID
            if module_id in self.id_to_config_map:
                module_config = self.id_to_config_map[module_id]
                score = self._calculate_module_relevance(
                    module_config, task_context
                )
                priority = module_config.get('priority', 'P2')

                recommendation = ModuleRecommendation(
                    module_id=module_id,
                    module_name=module_config.get('module_name', ''),
                    priority=priority,
                    relevance_score=score['relevance'],
                    confidence=score['confidence'],
                    reason=score['reason']
                )
                scored_modules.append(recommendation)

        # Sort by priority (P0 > P1 > P2 > P3) then by relevance score
        priority_order = {'P0': 0, 'P1': 1, 'P2': 2, 'P3': 3}
        scored_modules.sort(
            key=lambda m: (priority_order.get(m.priority, 4), -m.relevance_score)
        )

        # Select top modules
        selected = scored_modules[:max_modules]

        # If min_coverage is True, ensure we have modules from different priorities
        if min_coverage and len(selected) < max_modules:
            selected = self._ensure_priority_coverage(selected, scored_modules, max_modules)

        return selected

    def _get_module_recommendations(self, scenario_type: str) -> List[str]:
        """Get recommended module IDs for a scenario type."""
        # Use scenario_module_map if available
        if self.scenario_module_map:
            scenario_config = self.scenario_module_map.get(scenario_type, {})
            primary = scenario_config.get('primary_modules', [])
            secondary = scenario_config.get('secondary_modules', [])
            return primary + secondary

        # Fallback: return all module IDs
        return list(self.module_definitions.keys())

    def _calculate_module_relevance(
        self,
        module_config: Dict,
        task_context: Dict
    ) -> Dict[str, Any]:
        """
        Calculate relevance score for a module.

        Returns dict with:
            - relevance: float (0-1)
            - confidence: float (0-1)
            - reason: str
        """
        scenario_type = task_context.get('scenario_type', '')
        difficulty = task_context.get('difficulty', 'L1')

        # Base relevance from priority
        priority = module_config.get('priority', 'P2')
        priority_scores = {'P0': 0.9, 'P1': 0.7, 'P2': 0.5, 'P3': 0.3}
        base_relevance = priority_scores.get(priority, 0.5)

        # Check if module is suitable for this difficulty
        difficulty_matrix = self._load_yaml_file('difficulty_levels.yaml').get(
            'module_difficulty_matrix', {}
        )

        module_id = module_config.get('module_id', '')
        suitability = 0.0
        if module_id in difficulty_matrix:
            difficulty_config = difficulty_matrix[module_id].get(difficulty, {})
            suitability = 1.0 if difficulty_config.get('enable', True) else 0.0

        # Check scenario-specific relevance
        scenario_relevance = 0.5
        if self.scenario_module_map:
            scenario_config = self.scenario_module_map.get(scenario_type, {})
            primary = scenario_config.get('primary_modules', [])
            secondary = scenario_config.get('secondary_modules', [])

            if module_id in primary:
                scenario_relevance = 1.0
            elif module_id in secondary:
                scenario_relevance = 0.7

        # Calculate final relevance
        relevance = (base_relevance * 0.4 + suitability * 0.3 +
                    scenario_relevance * 0.3)

        # Confidence based on how well the module matches the context
        confidence = min(relevance + 0.1, 1.0)

        # Generate reason
        reason = f"{module_config.get('module_name', '')} is "
        if priority == 'P0':
            reason += "a critical safety module"
        elif priority == 'P1':
            reason += "a core clinical module"
        elif priority == 'P2':
            reason += "a quality enhancement module"
        else:
            reason += "an advanced capability module"

        if scenario_type and scenario_relevance > 0.7:
            reason += f" highly relevant for {scenario_type} scenarios"

        return {
            'relevance': relevance,
            'confidence': confidence,
            'reason': reason
        }

    def _ensure_priority_coverage(
        self,
        selected: List[ModuleRecommendation],
        available: List[ModuleRecommendation],
        max_modules: int
    ) -> List[ModuleRecommendation]:
        """Ensure we have modules from different priority levels."""
        priorities_covered = set(m.priority for m in selected)

        # If we already have P0 and at least one other, we're good
        if 'P0' in priorities_covered and len(priorities_covered) >= 2:
            return selected

        # Add missing priorities
        result = selected.copy()
        for module in available:
            if len(result) >= max_modules:
                break
            if module.priority not in priorities_covered:
                result.append(module)
                priorities_covered.add(module.priority)

        return result

    def generate_module_requirements(
        self,
        selected_modules: List[str],
        task_context: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Generate requirements for selected modules.

        Args:
            selected_modules: List of module IDs
            task_context: Task context

        Returns:
            Dictionary mapping module_id to its requirements
        """
        difficulty = task_context.get('difficulty', 'L1')
        patient_behavior = task_context.get('patient_behavior', 'cooperative')

        requirements = {}
        for module_id in selected_modules:
            # Use id_to_config_map to get module config by ID
            if module_id in self.id_to_config_map:
                module_config = self.id_to_config_map[module_id]

                # Get module-specific behavior template
                behavior_spec = self._get_behavior_spec(
                    module_id, difficulty, patient_behavior
                )

                # Generate element requirements
                element_requirements = self._generate_element_requirements(
                    module_config, difficulty
                )

                # Get red line rules for this module
                red_line_rules = self._get_module_red_lines(module_id)

                requirements[module_id] = {
                    'module_name': module_config.get('module_name', ''),
                    'module_id': module_config.get('module_id', ''),
                    'priority': module_config.get('priority', 'P2'),
                    'elements': element_requirements,
                    'patient_behavior': behavior_spec,
                    'red_line_rules': red_line_rules,
                    'description': module_config.get('description', '')
                }

        return requirements

    def _get_behavior_spec(
        self,
        module_id: str,
        difficulty: str,
        patient_behavior: str
    ) -> Dict[str, Any]:
        """Get patient behavior specification for a module."""
        module_config = self.module_definitions.get(module_id, {})
        behaviors = module_config.get('patient_behaviors', {})

        # Get behavior for this difficulty
        behavior_config = behaviors.get(patient_behavior, behaviors.get('cooperative', {}))

        return {
            'behavior_type': patient_behavior,
            'difficulty_level': difficulty,
            'description': behavior_config.get('description', ''),
            'patient_says': behavior_config.get('patient_says', []),
            'required_agent_responses': behavior_config.get('required_agent_responses', []),
            'behaviors': behavior_config.get('behaviors', [])
        }

    def _generate_element_requirements(
        self,
        module_config: Dict,
        difficulty: str
    ) -> List[Dict[str, Any]]:
        """Generate requirements for module elements."""
        elements = module_config.get('elements', [])
        element_requirements = []

        for element in elements:
            element_id = element.get('element_id', '')
            difficulty_levels = element.get('difficulty_levels', {})

            # Get scenario for this difficulty
            scenario_config = difficulty_levels.get(difficulty, {})

            element_requirements.append({
                'element_id': element_id,
                'name': element.get('name', ''),
                'description': element.get('description', ''),
                'scenario': scenario_config.get('scenario', ''),
                'patient_behavior': scenario_config.get('patient_behavior', ''),
                'evaluation_points': scenario_config.get('evaluation_points', []),
                'evaluation_criteria': element.get('evaluation_criteria', {}),
                'red_line_triggers': element.get('red_line_triggers', [])
            })

        return element_requirements

    def _get_module_red_lines(self, module_id: str) -> List[Dict[str, Any]]:
        """Get red line rules for a module."""
        # Get module-specific rules
        module_rules = self.red_line_rules['module_specific'].get(module_id, [])

        # Always include global red lines
        all_rules = self.red_line_rules['global'] + module_rules

        return all_rules

    def integrate_evaluation_criteria(
        self,
        module_requirements: Dict[str, Dict[str, Any]],
        task_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Integrate evaluation criteria from multiple modules.

        Args:
            module_requirements: Requirements from selected modules
            task_context: Task context

        Returns:
            Integrated evaluation criteria
        """
        difficulty = task_context.get('difficulty', 'L1')

        # Collect all checklists
        all_checklists = []
        all_red_lines = []
        module_weights = {}

        for module_id, reqs in module_requirements.items():
            # Get module weight
            module_config = self.module_definitions.get(module_id, {})
            weight = module_config.get('coverage_weight', 1.0)
            module_weights[module_id] = weight

            # Collect element checklists
            for element in reqs.get('elements', []):
                eval_criteria = element.get('evaluation_criteria', {})
                if eval_criteria:
                    checklist_item = {
                        'check_id': eval_criteria.get('check_id', ''),
                        'description': element.get('description', ''),
                        'module_id': module_id,
                        'weight': eval_criteria.get('weight', 1.0) * weight,
                        'evaluation_points': element.get('evaluation_points', [])
                    }
                    all_checklists.append(checklist_item)

            # Collect red lines
            for red_line in reqs.get('red_line_rules', []):
                if red_line not in all_red_lines:
                    all_red_lines.append(red_line)

        # Calculate score thresholds
        difficulty_config = self.difficulty_levels.get(difficulty, {})
        expected_performance = difficulty_config.get('expected_agent_performance', {})
        min_completion = expected_performance.get('min_checklist_completion', 0.8)

        # Build integrated criteria
        integrated = {
            'checklist': all_checklists,
            'red_line_rules': all_red_lines,
            'scoring': {
                'difficulty': difficulty,
                'min_checklist_completion': min_completion,
                'module_weights': module_weights,
                'difficulty_multiplier': self._get_difficulty_multiplier(difficulty)
            },
            'modules_tested': list(module_requirements.keys()),
            'total_checklist_items': len(all_checklists)
        }

        return integrated

    def _get_difficulty_multiplier(self, difficulty: str) -> float:
        """Get difficulty score multiplier."""
        scoring_config = self._load_yaml_file('difficulty_levels.yaml').get(
            'scoring_system', {}
        )
        multipliers = scoring_config.get('difficulty_multipliers', {})
        return multipliers.get(difficulty, 1.0)

    def create_integrated_task(
        self,
        base_task: Dict[str, Any],
        selected_modules: List[str],
        target_difficulty: str = None
    ) -> Dict[str, Any]:
        """
        Create a task with integrated module requirements.

        Args:
            base_task: Original task definition
            selected_modules: List of module IDs to integrate
            target_difficulty: Target difficulty (overrides base_task difficulty)

        Returns:
            Enhanced task with module requirements
        """
        # Determine difficulty
        difficulty = target_difficulty or base_task.get('difficulty', 'L1')

        # Build task context
        task_context = {
            'scenario_type': base_task.get('scenario_type', 'information_query'),
            'difficulty': difficulty,
            'medical_domain': base_task.get('medical_domain', 'general'),
            'symptoms': base_task.get('symptoms', [])
        }

        # Select modules if not provided
        if not selected_modules:
            recommendations = self.select_modules_for_task(task_context)
            selected_modules = [r.module_id for r in recommendations]

        # Generate module requirements
        module_requirements = self.generate_module_requirements(
            selected_modules, task_context
        )

        # Integrate evaluation criteria
        evaluation_criteria = self.integrate_evaluation_criteria(
            module_requirements, task_context
        )

        # Create enhanced task
        enhanced_task = base_task.copy()
        enhanced_task['module_requirements'] = module_requirements
        enhanced_task['evaluation_criteria'] = evaluation_criteria
        enhanced_task['difficulty'] = difficulty
        enhanced_task['modules_tested'] = selected_modules

        # Add metadata
        enhanced_task['metadata'] = enhanced_task.get('metadata', {})
        enhanced_task['metadata']['module_integrated'] = True
        enhanced_task['metadata']['num_modules'] = len(selected_modules)
        enhanced_task['metadata']['integration_timestamp'] = self._get_timestamp()

        return enhanced_task

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

    def get_module_coverage_summary(
        self,
        tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze module coverage across a list of tasks.

        Args:
            tasks: List of task definitions

        Returns:
            Coverage summary statistics
        """
        total_tasks = len(tasks)
        module_counts = {module_id: 0 for module_id in self.module_definitions.keys()}
        priority_counts = {'P0': 0, 'P1': 0, 'P2': 0, 'P3': 0}
        difficulty_counts = {'L1': 0, 'L2': 0, 'L3': 0}

        for task in tasks:
            # Count modules
            modules_tested = task.get('modules_tested', [])
            for module_id in modules_tested:
                if module_id in module_counts:
                    module_counts[module_id] += 1

                # Count priorities
                if module_id in self.id_to_config_map:
                    priority = self.id_to_config_map[module_id].get('priority', 'P2')
                    priority_counts[priority] += 1

            # Count difficulties
            difficulty = task.get('difficulty', 'L1')
            if difficulty in difficulty_counts:
                difficulty_counts[difficulty] += 1

        # Calculate percentages
        coverage_percentage = {
            module_id: (count / total_tasks * 100) if total_tasks > 0 else 0
            for module_id, count in module_counts.items()
        }

        return {
            'total_tasks': total_tasks,
            'module_counts': module_counts,
            'module_coverage_percentage': coverage_percentage,
            'priority_counts': priority_counts,
            'difficulty_distribution': difficulty_counts,
            'average_modules_per_task': sum(len(t.get('modules_tested', [])) for t in tasks) / total_tasks if total_tasks > 0 else 0
        }

    def recommend_modules_for_coverage(
        self,
        current_coverage: Dict[str, int],
        target_tasks: int,
        target_distribution: Dict[str, float] = None
    ) -> List[Tuple[str, int]]:
        """
        Recommend modules to add to achieve target coverage.

        Args:
            current_coverage: Current module counts
            target_tasks: Target total number of tasks
            target_distribution: Target distribution by priority

        Returns:
            List of (module_id, recommended_count) tuples
        """
        if target_distribution is None:
            target_distribution = {'P0': 0.35, 'P1': 0.35, 'P2': 0.20, 'P3': 0.10}

        recommendations = []

        for priority, target_pct in target_distribution.items():
            target_count = int(target_tasks * target_pct)
            current_count = sum(
                current_coverage.get(m, 0)
                for m in self.priority_groups[priority]
            )

            needed = max(0, target_count - current_count)

            if needed > 0:
                # Distribute among modules in this priority
                modules = self.priority_groups[priority]
                per_module = needed // len(modules)
                remainder = needed % len(modules)

                for i, module_id in enumerate(modules):
                    count = per_module + (1 if i < remainder else 0)
                    if count > 0:
                        recommendations.append((module_id, count))

        return sorted(recommendations, key=lambda x: x[1], reverse=True)
