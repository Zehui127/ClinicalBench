"""
Base Module Class for Medical Task Suite

This module defines the abstract base class and data structures for all 13
core medical capability modules.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class DifficultyLevel(Enum):
    """Difficulty levels for medical tasks"""
    L1 = "cooperative"  # 配合型患者
    L2 = "forgetful"    # 记不清型患者
    L3 = "adversarial"  # 隐瞒/施压/拒绝型患者


class SeverityLevel(Enum):
    """Severity levels for red line violations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ModuleElement:
    """
    Represents a single element within a medical module.

    An element is a specific capability or behavior that the medical agent
    should demonstrate. Each element can have different difficulty levels.

    Attributes:
        element_id: Unique identifier for the element
        name: Human-readable name
        description: Detailed description of what this element tests
        difficulty_levels: Dictionary mapping difficulty to specific scenarios
        evaluation_criteria: How to evaluate this element (check_id, weight, etc.)
        red_line_triggers: List of conditions that trigger red line violations
    """
    element_id: str
    name: str
    description: str
    difficulty_levels: Dict[str, Dict[str, Any]]
    evaluation_criteria: Dict[str, Any]
    red_line_triggers: List[str] = field(default_factory=list)

    def get_scenario_for_difficulty(self, difficulty: str) -> Dict[str, Any]:
        """Get the scenario configuration for a specific difficulty level"""
        return self.difficulty_levels.get(difficulty, {})

    def get_evaluation_weight(self) -> float:
        """Get the evaluation weight for this element"""
        return self.evaluation_criteria.get('weight', 1.0)


@dataclass
class RedLineRule:
    """
    Represents a red line rule that medical agents must not violate.

    Red lines are critical safety boundaries - violations indicate potentially
    dangerous medical behavior.

    Attributes:
        rule_id: Unique identifier
        name: Human-readable name
        description: What this rule prevents
        severity: How severe violations are
        trigger_conditions: List of conditions that trigger this rule
        detection_patterns: Patterns to detect violations
        remediation: How to fix when violated
    """
    rule_id: str
    name: str
    description: str
    severity: SeverityLevel
    trigger_conditions: List[str]
    detection_patterns: List[Dict[str, Any]]
    remediation: str

    def check_violation(self, agent_response: str, context: Dict[str, Any]) -> Optional[Dict]:
        """
        Check if this red line rule is violated.

        Args:
            agent_response: The agent's response text
            context: Additional context about the conversation

        Returns:
            Violation details if violated, None otherwise
        """
        # Check if any trigger conditions are met
        for pattern in self.detection_patterns:
            if self._match_pattern(agent_response, pattern, context):
                return {
                    'rule_id': self.rule_id,
                    'severity': self.severity.value,
                    'matched_pattern': pattern,
                    'remediation': self.remediation
                }
        return None

    def _match_pattern(self, response: str, pattern: Dict, context: Dict) -> bool:
        """Check if response matches a violation pattern"""
        # This is a simplified implementation
        # In production, use more sophisticated NLP/rule matching
        keywords = pattern.get('keywords', [])
        for keyword in keywords:
            if keyword.lower() in response.lower():
                return True
        return False


@dataclass
class PatientBehavior:
    """
    Defines patient behavior patterns for different difficulty levels.

    Attributes:
        behavior_type: Type of behavior (cooperative, forgetful, concealing, etc.)
        difficulty_level: Associated difficulty level
        description: What the patient does
        triggers: What triggers this behavior
        responses: How the patient responds to different agent actions
        expected_agent_responses: What the agent should do in response
    """
    behavior_type: str
    difficulty_level: str
    description: str
    triggers: List[str]
    responses: Dict[str, List[str]]
    expected_agent_responses: List[str]


@dataclass
class ModuleConfig:
    """
    Configuration for a complete medical module.

    A module contains multiple elements that test related medical capabilities.

    Attributes:
        module_id: Unique identifier (e.g., "module_01")
        module_name: Human-readable name
        description: What this module tests
        elements: List of ModuleElement objects
        difficulty_distribution: Target distribution of difficulties (e.g., {"L1": 0.4, "L2": 0.4, "L3": 0.2})
        red_line_rules: List of red line rules specific to this module
        patient_behaviors: Dict of behavior templates by difficulty
        metadata: Additional module metadata
    """
    module_id: str
    module_name: str
    description: str
    elements: List[ModuleElement]
    difficulty_distribution: Dict[str, float]
    red_line_rules: List[RedLineRule]
    patient_behaviors: Dict[str, PatientBehavior]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_element(self, element_id: str) -> Optional[ModuleElement]:
        """Get an element by ID"""
        for element in self.elements:
            if element.element_id == element_id:
                return element
        return None

    def get_elements_for_difficulty(self, difficulty: str) -> List[ModuleElement]:
        """Get all elements that have scenarios for a given difficulty"""
        return [
            e for e in self.elements
            if difficulty in e.difficulty_levels
        ]


class BaseModule(ABC):
    """
    Abstract base class for all 13 medical capability modules.

    All modules must inherit from this class and implement the required methods.
    This ensures consistent interfaces across all modules.
    """

    def __init__(self, config: ModuleConfig):
        """
        Initialize the module with its configuration.

        Args:
            config: ModuleConfig object containing module definition
        """
        self.config = config
        self.module_id = config.module_id
        self.module_name = config.module_name

    @abstractmethod
    def generate_task_requirements(
        self,
        difficulty: str,
        patient_behavior: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate task requirements for a specific difficulty level.

        This method creates the specific requirements that should be included
        in a task to test this module at the given difficulty level.

        Args:
            difficulty: Difficulty level (L1, L2, or L3)
            patient_behavior: Type of patient behavior to simulate
            context: Additional context (medical condition, scenario type, etc.)

        Returns:
            Dictionary containing:
                - module_requirements: Specific requirements for this module
                - patient_scenario: How the patient should behave
                - evaluation_criteria: How to evaluate performance
                - red_lines: Which red lines to check
        """
        pass

    @abstractmethod
    def generate_evaluation_criteria(
        self,
        task_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate evaluation criteria for a task.

        This creates the specific evaluation metrics and checklists that
        should be used to evaluate agent performance on this task.

        Args:
            task_requirements: Requirements from generate_task_requirements()

        Returns:
            Dictionary containing:
                - checklist: List of specific checks to perform
                - scoring: How to score each check
                - pass_threshold: Minimum score to pass
                - red_line_checks: Which red lines to check
        """
        pass

    @abstractmethod
    def check_red_line_violation(
        self,
        agent_response: str,
        task_context: Dict[str, Any],
        conversation_history: Optional[List[Dict]] = None
    ) -> List[Dict[str, Any]]:
        """
        Check if the agent violated any red lines for this module.

        Red lines are critical safety boundaries. Violations indicate
        potentially dangerous medical behavior.

        Args:
            agent_response: The agent's latest response
            task_context: Context about the current task
            conversation_history: Full conversation history (optional)

        Returns:
            List of violation dictionaries, each containing:
                - rule_id: Which rule was violated
                - severity: How severe the violation is
                - description: What was violated
                - remediation: How to fix it
        """
        pass

    def get_module_summary(self) -> Dict[str, Any]:
        """
        Get a summary of this module.

        Returns:
            Dictionary with module information
        """
        return {
            'module_id': self.module_id,
            'module_name': self.module_name,
            'description': self.config.description,
            'num_elements': len(self.config.elements),
            'num_red_lines': len(self.config.red_line_rules),
            'difficulty_distribution': self.config.difficulty_distribution
        }

    def validate_task_for_module(
        self,
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate that a task properly tests this module.

        Args:
            task: Task definition to validate

        Returns:
            Dictionary with validation results:
                - is_valid: Whether the task is valid
                - issues: List of any issues found
                - suggestions: Suggestions for improvement
        """
        issues = []
        suggestions = []

        # Check if task has module requirements
        if 'module_requirements' not in task:
            issues.append("Missing 'module_requirements' field")
            suggestions.append("Add module_requirements with this module's requirements")

        # Check if difficulty is specified
        if task.get('difficulty') not in ['L1', 'L2', 'L3']:
            issues.append(f"Invalid or missing difficulty: {task.get('difficulty')}")

        # Check if evaluation criteria include this module
        eval_criteria = task.get('evaluation_criteria', {})
        if self.module_id not in str(eval_criteria):
            suggestions.append(f"Consider adding {self.module_id} to evaluation criteria")

        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'suggestions': suggestions
        }


class ModuleRegistry:
    """
    Registry for all medical modules.

    This class maintains a registry of all available modules and provides
    convenience methods for accessing them.
    """

    _instance = None
    _modules: Dict[str, BaseModule] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, module: BaseModule):
        """Register a module"""
        cls._modules[module.module_id] = module

    @classmethod
    def get_module(cls, module_id: str) -> Optional[BaseModule]:
        """Get a module by ID"""
        return cls._modules.get(module_id)

    @classmethod
    def get_all_modules(cls) -> Dict[str, BaseModule]:
        """Get all registered modules"""
        return cls._modules.copy()

    @classmethod
    def list_module_ids(cls) -> List[str]:
        """List all registered module IDs"""
        return list(cls._modules.keys())

    @classmethod
    def clear(cls):
        """Clear all registered modules (mainly for testing)"""
        cls._modules.clear()
