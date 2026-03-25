"""
Behavior Simulation Module for Medical Task Suite

This module simulates different patient behavior patterns for testing
medical agents at various difficulty levels (L1, L2, L3).
"""

from .behavior_templates import (
    BehaviorScenario,
    BehaviorTemplates,
    CooperativeBehavior,
    ForgetfulBehavior,
    ConcealingBehavior,
    PressuringBehavior,
    RefusingBehavior
)

__all__ = [
    'BehaviorScenario',
    'BehaviorTemplates',
    'CooperativeBehavior',
    'ForgetfulBehavior',
    'ConcealingBehavior',
    'PressuringBehavior',
    'RefusingBehavior'
]
