"""
Tool Interfaces Module for Medical Task Suite

This module provides both stub and real implementations of various medical
system interfaces that medical agents may interact with, including:
- HIS (Hospital Information System)
- Drug Database
- Insurance System
- OCR (Optical Character Recognition)

The module automatically selects between stub and real implementations based
on the USE_REAL_INTERFACES environment variable or configuration file.

Usage:
    # Default: uses stub implementations
    from medical_task_suite.tool_interfaces import HISInterface
    his = HISInterface()

    # To use real implementations:
    # 1. Set environment variable: export USE_REAL_INTERFACES=true
    # 2. Or configure in api_config.yaml: interface.use_real: true
    # 3. Then import and use the same way
    from medical_task_suite.tool_interfaces import HISInterface
    his = HISInterface()  # Automatically uses real implementation
"""

import os
from typing import Union

from .his_interface import HISInterface as StubHISInterface
from .drug_database_interface import DrugDatabaseInterface as StubDrugDatabaseInterface
from .insurance_interface import InsuranceInterface as StubInsuranceInterface
from .ocr_interface import OCRInterface as StubOCRInterface

# Import configuration
from .config.settings import get_config

# Import real implementations (available but not loaded by default)
from .real.his_fhir import RealHISInterface
from .real.drug_openfda import RealDrugDatabase

# Type aliases for backward compatibility (for type checking)
# Note: These are overwritten by factory functions below
HISInterfaceType = Union[StubHISInterface, RealHISInterface]
DrugDatabaseInterfaceType = Union[StubDrugDatabaseInterface, RealDrugDatabase]
InsuranceInterfaceType = StubInsuranceInterface
OCRInterfaceType = StubOCRInterface


def _create_his_interface(hospital_id: str = "DEFAULT_HOSPITAL") -> Union[StubHISInterface, RealHISInterface]:
    """
    Factory function for creating HIS interface.

    Automatically selects stub or real implementation based on configuration.

    Args:
        hospital_id: Hospital identifier

    Returns:
        HIS interface instance (stub or real)
    """
    config = get_config()

    if config.is_real_enabled():
        try:
            fhir_config = config.get_fhir_config()
            return RealHISInterface(fhir_config)
        except Exception as e:
            if config.should_fallback_to_stub():
                import warnings
                warnings.warn(
                    f"Failed to initialize real HIS interface, falling back to stub: {e}"
                )
                return StubHISInterface(hospital_id)
            else:
                raise

    return StubHISInterface(hospital_id)


def _create_drug_database_interface(database_id: str = "DEFAULT_DRUG_DB") -> Union[StubDrugDatabaseInterface, RealDrugDatabase]:
    """
    Factory function for creating drug database interface.

    Automatically selects stub or real implementation based on configuration.

    Args:
        database_id: Database identifier

    Returns:
        Drug database interface instance (stub or real)
    """
    config = get_config()

    if config.is_real_enabled():
        try:
            openfda_config = config.get_openfda_config()
            return RealDrugDatabase(openfda_config)
        except Exception as e:
            if config.should_fallback_to_stub():
                import warnings
                warnings.warn(
                    f"Failed to initialize real drug database interface, falling back to stub: {e}"
                )
                return StubDrugDatabaseInterface(database_id)
            else:
                raise

    return StubDrugDatabaseInterface(database_id)


def _create_insurance_interface() -> StubInsuranceInterface:
    """
    Factory function for creating insurance interface.

    Currently only stub implementation is available.

    Returns:
        Insurance interface instance
    """
    return StubInsuranceInterface()


def _create_ocr_interface() -> StubOCRInterface:
    """
    Factory function for creating OCR interface.

    Currently only stub implementation is available.

    Returns:
        OCR interface instance
    """
    return StubOCRInterface()


# Create factory instances
HISInterface = _create_his_interface
DrugDatabaseInterface = _create_drug_database_interface
InsuranceInterface = _create_insurance_interface
OCRInterface = _create_ocr_interface

__all__ = [
    'HISInterface',
    'DrugDatabaseInterface',
    'InsuranceInterface',
    'OCRInterface',
    # Export real implementations for direct access if needed
    'StubHISInterface',
    'StubDrugDatabaseInterface',
    'StubInsuranceInterface',
    'StubOCRInterface',
    'RealHISInterface',
    'RealDrugDatabase',
    # Export config
    'get_config'
]
