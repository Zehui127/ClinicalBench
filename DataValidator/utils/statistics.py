#!/usr/bin/env python3
"""
Statistics utilities for dataset validation.
"""

from typing import Dict, List, Any
from collections import defaultdict


def calculate_dataset_statistics(tasks: List[Dict[str, Any]], issues: List) -> Dict[str, Any]:
    """
    Calculate comprehensive dataset statistics.

    Args:
        tasks: List of task dictionaries
        issues: List of ValidationIssue objects

    Returns:
        Dictionary with various statistics
    """
    stats = defaultdict(int)

    # Count tasks with issues by level
    from ..models import ValidationLevel

    task_ids_with_errors = set()
    task_ids_with_warnings = set()

    for issue in issues:
        if issue.level == ValidationLevel.ERROR:
            if issue.task_id:
                task_ids_with_errors.add(issue.task_id)
            stats["errors"] += 1
        elif issue.level == ValidationLevel.WARNING:
            if issue.task_id:
                task_ids_with_warnings.add(issue.task_id)
            stats["warnings"] += 1
        elif issue.level == ValidationLevel.INFO:
            stats["info"] += 1

    stats["tasks_with_errors"] = len(task_ids_with_errors)
    stats["tasks_with_warnings"] = len(task_ids_with_warnings)

    # Calculate ticket length statistics
    ticket_lengths = []
    multi_turn_count = 0
    safety_related_count = 0
    total_evaluation_actions = 0

    # Domain distribution
    domains = defaultdict(int)

    for task in tasks:
        # Ticket length
        ticket = task.get("ticket", "")
        if ticket:
            ticket_lengths.append(len(ticket))

        # Domain
        domain = task.get("user_scenario", {}).get("instructions", {}).get("domain", "unknown")
        domains[domain] += 1

        # Evaluation actions
        eval_criteria = task.get("evaluation_criteria", {})
        if isinstance(eval_criteria, dict):
            actions = eval_criteria.get("actions", [])
            if isinstance(actions, list):
                total_evaluation_actions += len(actions)

        # Check if multi-turn (has task_instructions with dialogue structure)
        user_scenario = task.get("user_scenario", {})
        if isinstance(user_scenario, dict):
            instructions = user_scenario.get("instructions", {})
            task_instructions = instructions.get("task_instructions", "")
            if task_instructions and any(marker in task_instructions.lower() for marker in ["patient:", "患者:", "user:", "用户:"]):
                multi_turn_count += 1

        # Check safety-related
        if any(keyword in ticket.lower() for keyword in ["emergency", "urgent", "severe", "chest pain", "癫痫", "昏迷"]):
            safety_related_count += 1

    # Add computed statistics
    stats["total_evaluation_actions"] = total_evaluation_actions
    stats["multi_turn_tasks"] = multi_turn_count
    stats["safety_related_tasks"] = safety_related_count

    if ticket_lengths:
        stats["avg_ticket_length"] = sum(ticket_lengths) / len(ticket_lengths)
        stats["min_ticket_length"] = min(ticket_lengths)
        stats["max_ticket_length"] = max(ticket_lengths)
    else:
        stats["avg_ticket_length"] = 0
        stats["min_ticket_length"] = 0
        stats["max_ticket_length"] = 0

    # Convert domain counts to dict
    stats["domain_distribution"] = dict(domains)

    return dict(stats)
