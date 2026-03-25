"""
Real Interface Implementations

This module contains real implementations of medical tool interfaces
using actual APIs like HAPI FHIR and OpenFDA.
"""

from .base_real_interface import BaseRealInterface
from .his_fhir import RealHISInterface
from .drug_openfda import RealDrugDatabase

__all__ = [
    'BaseRealInterface',
    'RealHISInterface',
    'RealDrugDatabase'
]
