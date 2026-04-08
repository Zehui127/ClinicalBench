#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clinical Knowledge Layer — structured medical data for task generation.

Replaces hardcoded Python dictionaries with JSON-backed data files,
providing a single source of truth for disease profiles, drug data,
lab reference values, triage rules, and clinical questions.
"""

from .accessor import (
    ClinicalKnowledgeBase,
    DiseaseProfile,
    DrugInfo,
)

__all__ = [
    "ClinicalKnowledgeBase",
    "DiseaseProfile",
    "DrugInfo",
]
