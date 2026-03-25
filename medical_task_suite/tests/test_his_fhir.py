"""
Unit Tests for Real HIS FHIR Interface

This module contains tests for the HAPI FHIR HIS interface implementation.
"""

import pytest
from datetime import datetime

from medical_task_suite.tool_interfaces.real.his_fhir import RealHISInterface
from medical_task_suite.tool_interfaces.his_interface import RecordType
from medical_task_suite.tool_interfaces.config.settings import get_config


class TestRealHISInterface:
    """Test cases for RealHISInterface."""

    @pytest.fixture
    def fhir_config(self):
        """Get FHIR configuration for testing."""
        config = get_config()
        return config.get_fhir_config()

    @pytest.fixture
    def his_interface(self, fhir_config):
        """Create HIS interface instance for testing."""
        his = RealHISInterface(fhir_config)
        his.connect()
        yield his
        his.disconnect()

    def test_connection(self, fhir_config):
        """Test FHIR server connection."""
        his = RealHISInterface(fhir_config)
        assert his.connect() == True
        assert his.is_connected == True
        his.disconnect()

    def test_get_patient_demographics(self, his_interface):
        """Test getting patient demographics."""
        # Use a known test patient ID from HAPI FHIR
        patient = his_interface.get_patient_demographics("example")

        # Verify structure
        assert isinstance(patient, dict)
        assert 'patient_id' in patient
        assert 'name' in patient
        assert 'age' in patient
        assert 'gender' in patient

    def test_get_patient_demographics_cache(self, his_interface):
        """Test caching of patient demographics."""
        # First call
        patient1 = his_interface.get_patient_demographics("example")

        # Second call should use cache
        patient2 = his_interface.get_patient_demographics("example")

        assert patient1 == patient2

    def test_get_patient_record(self, his_interface):
        """Test getting patient records."""
        records = his_interface.get_patient_record("example")

        # Verify structure
        assert isinstance(records, list)

    def test_get_patient_record_with_type_filter(self, his_interface):
        """Test getting patient records with type filter."""
        records = his_interface.get_patient_record(
            "example",
            record_type=RecordType.OUTPATIENT
        )

        # Verify structure
        assert isinstance(records, list)

    def test_get_lab_results(self, his_interface):
        """Test getting lab results."""
        results = his_interface.get_lab_results("example")

        # Verify structure
        assert isinstance(results, list)

    def test_get_lab_results_with_test_type(self, his_interface):
        """Test getting lab results with test type filter."""
        results = his_interface.get_lab_results("example", test_type="CBC")

        # Verify structure
        assert isinstance(results, list)

    def test_get_medication_history(self, his_interface):
        """Test getting medication history."""
        medications = his_interface.get_medication_history("example")

        # Verify structure
        assert isinstance(medications, list)

    def test_get_appointments(self, his_interface):
        """Test getting appointments."""
        appointments = his_interface.get_appointments("example")

        # Verify structure
        assert isinstance(appointments, list)

    def test_get_appointments_with_status_filter(self, his_interface):
        """Test getting appointments with status filter."""
        appointments = his_interface.get_appointments("example", status="booked")

        # Verify structure
        assert isinstance(appointments, list)

    def test_search_patients(self, his_interface):
        """Test searching for patients."""
        patients = his_interface.search_patients(name="Smith")

        # Verify structure
        assert isinstance(patients, list)

    def test_cache_stats(self, his_interface):
        """Test cache statistics."""
        stats = his_interface.get_cache_stats()

        # Verify structure
        assert isinstance(stats, dict)
        assert 'size' in stats
        assert 'hits' in stats
        assert 'misses' in stats

    def test_clear_cache(self, his_interface):
        """Test clearing cache."""
        # Make some calls to populate cache
        his_interface.get_patient_demographics("example")

        # Clear cache
        his_interface.clear_cache()

        # Verify cache is cleared
        stats = his_interface.get_cache_stats()
        assert stats['size'] == 0

    def test_context_manager(self, fhir_config):
        """Test using interface as context manager."""
        with RealHISInterface(fhir_config) as his:
            assert his.is_connected == True
            patient = his.get_patient_demographics("example")
            assert isinstance(patient, dict)

    def test_invalid_patient_id(self, his_interface):
        """Test handling of invalid patient ID."""
        # Should not raise exception, return empty/default data
        demographics = his_interface.get_patient_demographics("invalid_id_12345")
        assert isinstance(demographics, dict)


class TestHISInterfaceCompatibility:
    """Test compatibility with stub HISInterface API."""

    @pytest.fixture
    def fhir_config(self):
        """Get FHIR configuration."""
        config = get_config()
        return config.get_fhir_config()

    def test_api_compatibility(self, fhir_config):
        """Test that real interface has same methods as stub."""
        from medical_task_suite.tool_interfaces.his_interface import HISInterface

        real_his = RealHISInterface(fhir_config)

        # Check that real interface has all required methods
        required_methods = [
            'connect',
            'disconnect',
            'get_patient_record',
            'get_patient_demographics',
            'get_appointments',
            'create_appointment',
            'get_lab_results',
            'get_medication_history',
            'search_patients',
            'get_doctor_schedule',
            'check_record_access_permission'
        ]

        for method in required_methods:
            assert hasattr(real_his, method)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
