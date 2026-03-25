"""
Dynamic Conversation Support for Medical Task Suite

This module provides state management and consistency verification
for multi-turn medical conversations.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ConversationState:
    """
    State tracking for multi-turn conversations.

    Attributes:
        conversation_id: Unique conversation identifier
        current_turn: Current turn number
        module_requirements: Module requirements for this conversation
        extracted_info: Information extracted so far
        checklist_progress: Progress on evaluation checklists
        red_line_violations: Violations detected so far
        consistency_issues: Consistency issues detected
        metadata: Additional metadata
    """
    conversation_id: str
    current_turn: int
    module_requirements: Dict[str, Any]
    extracted_info: Dict[str, Any]
    checklist_progress: Dict[str, bool]
    red_line_violations: List[Dict[str, Any]]
    consistency_issues: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConversationManager:
    """
    Manages multi-turn conversation state and consistency.

    This class:
    - Tracks conversation state across turns
    - Maintains checklist progress
    - Detects consistency issues
    - Preserves context
    """

    def __init__(self):
        """Initialize the conversation manager."""
        self.active_conversations: Dict[str, ConversationState] = {}

    def create_conversation(
        self,
        conversation_id: str,
        task_context: Dict[str, Any]
    ) -> ConversationState:
        """
        Create a new conversation state.

        Args:
            conversation_id: Unique identifier
            task_context: Initial task context

        Returns:
            ConversationState object
        """
        state = ConversationState(
            conversation_id=conversation_id,
            current_turn=0,
            module_requirements=task_context.get('module_requirements', {}),
            extracted_info={},
            checklist_progress={},
            red_line_violations=[],
            consistency_issues=[],
            metadata={
                'start_time': datetime.now().isoformat(),
                'task_context': task_context
            }
        )

        self.active_conversations[conversation_id] = state
        return state

    def update_conversation(
        self,
        conversation_id: str,
        agent_response: str,
        patient_message: str,
        additional_info: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Update conversation state after a turn.

        Args:
            conversation_id: Conversation identifier
            agent_response: Agent's response
            patient_message: Patient's message
            additional_info: Additional extracted info

        Returns:
            Update summary
        """
        if conversation_id not in self.active_conversations:
            raise ValueError(f"Conversation {conversation_id} not found")

        state = self.active_conversations[conversation_id]
        state.current_turn += 1

        # Update extracted info
        if additional_info:
            state.extracted_info.update(additional_info)

        # Check for consistency issues
        new_issues = self._check_consistency(state, agent_response)
        state.consistency_issues.extend(new_issues)

        return {
            'turn': state.current_turn,
            'new_issues': len(new_issues),
            'total_issues': len(state.consistency_issues)
        }

    def _check_consistency(
        self,
        state: ConversationState,
        new_response: str
    ) -> List[Dict[str, Any]]:
        """
        Check for consistency issues in the conversation.

        Args:
            state: Current conversation state
            new_response: New agent response

        Returns:
            List of consistency issues found
        """
        issues = []

        # Check for contradictory statements
        if 'extracted_info' in state.extracted_info:
            for key, value in state.extracted_info.items():
                # Simple check: did agent contradict previously extracted info?
                # In production, use more sophisticated NLP
                pass

        # Check for repeated questions (may indicate memory issues)
        # In production, track what was asked before

        return issues

    def get_conversation_summary(
        self,
        conversation_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get summary of conversation state.

        Args:
            conversation_id: Conversation identifier

        Returns:
            Conversation summary
        """
        if conversation_id not in self.active_conversations:
            return None

        state = self.active_conversations[conversation_id]

        return {
            'conversation_id': conversation_id,
            'current_turn': state.current_turn,
            'modules_tested': list(state.module_requirements.keys()),
            'extracted_info': state.extracted_info,
            'checklist_completion': sum(state.checklist_progress.values()) / len(state.checklist_progress) if state.checklist_progress else 0,
            'red_line_violations': len(state.red_line_violations),
            'consistency_issues': len(state.consistency_issues),
            'duration': datetime.now() - datetime.fromisoformat(state.metadata['start_time'])
        }

    def check_red_lines_ongoing(
        self,
        conversation_id: str,
        agent_response: str,
        modules: List[Any]
    ) -> List[Dict[str, Any]]:
        """
        Check for red line violations across all active modules.

        Args:
            conversation_id: Conversation identifier
            agent_response: Latest agent response
            modules: List of module instances

        Returns:
            List of violations
        """
        if conversation_id not in self.active_conversations:
            return []

        state = self.active_conversations[conversation_id]
        all_violations = []

        for module_id, module_reqs in state.module_requirements.items():
            # Find corresponding module instance
            # In production, this would be more sophisticated
            pass

        return all_violations

    def end_conversation(
        self,
        conversation_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        End conversation and return final summary.

        Args:
            conversation_id: Conversation identifier

        Returns:
            Final conversation summary
        """
        summary = self.get_conversation_summary(conversation_id)

        if conversation_id in self.active_conversations:
            del self.active_conversations[conversation_id]

        return summary


class ConsistencyVerifier:
    """
    Verifies consistency across conversation turns.

    This class:
    - Checks for contradictions
    - Validates information consistency
    - Tracks information changes
    """

    def __init__(self):
        """Initialize the consistency verifier."""
        self.info_history: Dict[str, List[Any]] = {}

    def verify_consistency(
        self,
        conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Verify consistency across entire conversation.

        Args:
            conversation_history: List of conversation turns

        Returns:
            Consistency report
        """
        issues = []

        # Check for temporal consistency
        issues.extend(self._check_temporal_consistency(conversation_history))

        # Check for factual consistency
        issues.extend(self._check_factual_consistency(conversation_history))

        # Check for diagnostic consistency
        issues.extend(self._check_diagnostic_consistency(conversation_history))

        return {
            'is_consistent': len(issues) == 0,
            'issues': issues,
            'issue_count': len(issues)
        }

    def _check_temporal_consistency(
        self,
        conversation_history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Check for temporal consistency."""
        issues = []
        # Implementation would check timestamps, sequence of events
        return issues

    def _check_factual_consistency(
        self,
        conversation_history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Check for factual consistency."""
        issues = []
        # Implementation would check for contradictory facts
        return issues

    def _check_diagnostic_consistency(
        self,
        conversation_history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Check for diagnostic consistency."""
        issues = []
        # Implementation would check for changing diagnoses
        return issues


def create_conversation_manager() -> ConversationManager:
    """Factory function to create conversation manager."""
    return ConversationManager()


def create_consistency_verifier() -> ConsistencyVerifier:
    """Factory function to create consistency verifier."""
    return ConsistencyVerifier()
