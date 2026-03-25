"""
Unit Tests for Real OpenFDA Drug Database Interface

This module contains tests for the OpenFDA drug database interface implementation.
"""

import pytest

from medical_task_suite.tool_interfaces.real.drug_openfda import RealDrugDatabase
from medical_task_suite.tool_interfaces.drug_database_interface import DrugCategory
from medical_task_suite.tool_interfaces.config.settings import get_config


class TestRealDrugDatabase:
    """Test cases for RealDrugDatabase."""

    @pytest.fixture
    def openfda_config(self):
        """Get OpenFDA configuration for testing."""
        config = get_config()
        return config.get_openfda_config()

    @pytest.fixture
    def drug_db(self, openfda_config):
        """Create drug database instance for testing."""
        db = RealDrugDatabase(openfda_config)
        db.connect()
        yield db
        db.disconnect()

    def test_connection(self, openfda_config):
        """Test OpenFDA connection."""
        db = RealDrugDatabase(openfda_config)
        assert db.connect() == True
        assert db.is_connected == True
        db.disconnect()

    def test_get_drug_info(self, drug_db):
        """Test getting drug information."""
        # Test with a common drug
        drug_info = drug_db.get_drug_info("aspirin")

        if drug_info:
            # Verify structure
            assert drug_info.generic_name != ""
            assert isinstance(drug_info.brand_names, list)
            assert isinstance(drug_info.indications, list)
            assert isinstance(drug_info.side_effects, list)

    def test_search_drugs_by_name(self, drug_db):
        """Test searching drugs by name."""
        results = drug_db.search_drugs("aspirin", search_type="name")

        # Verify structure
        assert isinstance(results, list)
        if results:
            assert 'generic_name' in results[0]
            assert 'brand_names' in results[0]

    def test_search_drugs_by_indication(self, drug_db):
        """Test searching drugs by indication."""
        results = drug_db.search_drugs("pain", search_type="indication")

        # Verify structure
        assert isinstance(results, list)

    def test_check_interactions(self, drug_db):
        """Test checking drug interactions."""
        # Test with known interacting drugs
        interactions = drug_db.check_interactions(["aspirin", "warfarin"])

        # Verify structure
        assert isinstance(interactions, list)

    def test_check_allergy(self, drug_db):
        """Test allergy checking."""
        result = drug_db.check_allergy("aspirin", ["aspirin"])

        # Verify structure
        assert isinstance(result, dict)
        assert 'has_allergy' in result

    def test_check_contraindications(self, drug_db):
        """Test contraindication checking."""
        result = drug_db.check_contraindications(
            "aspirin",
            ["peptic ulcer", "bleeding disorder"]
        )

        # Verify structure
        assert isinstance(result, list)

    def test_get_dosage_info(self, drug_db):
        """Test getting dosage information."""
        result = drug_db.get_dosage_info(
            "aspirin",
            patient_age=45,
            patient_weight=70.0,
            condition="pain"
        )

        # Verify structure
        assert isinstance(result, dict)
        assert 'standard_dosage' in result
        assert 'frequency' in result

    def test_find_alternatives(self, drug_db):
        """Test finding alternative drugs."""
        alternatives = drug_db.find_alternatives("aspirin")

        if alternatives:
            # Verify structure
            assert alternatives.original_drug == "aspirin"
            assert isinstance(alternatives.alternatives, list)

    def test_get_side_effects(self, drug_db):
        """Test getting side effects."""
        side_effects = drug_db.get_side_effects("aspirin")

        # Verify structure
        assert isinstance(side_effects, dict)
        assert 'common' in side_effects
        assert 'serious' in side_effects

    def test_check_pregnancy_safety(self, drug_db):
        """Test pregnancy safety check."""
        result = drug_db.check_pregnancy_safety("aspirin")

        # Verify structure
        assert isinstance(result, dict)
        assert 'category' in result
        assert 'recommendation' in result

    def test_verify_drug_name(self, drug_db):
        """Test drug name verification."""
        matches = drug_db.verify_drug_name("aspirin")

        # Verify structure
        assert isinstance(matches, list)

    def test_get_drug_price(self, drug_db):
        """Test getting drug price (placeholder)."""
        result = drug_db.get_drug_price("aspirin", "100mg", 30)

        # Verify structure (returns placeholder)
        assert isinstance(result, dict)
        assert 'price' in result

    def test_get_formulary_status(self, drug_db):
        """Test getting formulary status (placeholder)."""
        result = drug_db.get_formulary_status("aspirin", "private")

        # Verify structure (returns placeholder)
        assert isinstance(result, dict)
        assert 'on_formulary' in result

    def test_cache_stats(self, drug_db):
        """Test cache statistics."""
        stats = drug_db.cache.get_stats() if drug_db.cache else None

        if stats:
            # Verify structure
            assert isinstance(stats, dict)
            assert 'size' in stats
            assert 'hits' in stats

    def test_cache_effectiveness(self, drug_db):
        """Test that caching reduces API calls."""
        # First call - should hit API
        drug_db.cache.clear() if drug_db.cache else None
        result1 = drug_db.get_drug_info("aspirin")

        # Get initial stats
        stats1 = drug_db.cache.get_stats() if drug_db.cache else None

        # Second call - should use cache
        result2 = drug_db.get_drug_info("aspirin")

        # Get final stats
        stats2 = drug_db.cache.get_stats() if drug_db.cache else None

        # Verify cache was used
        if stats1 and stats2:
            assert stats2['hits'] > stats1['hits']

    def test_context_manager(self, openfda_config):
        """Test using interface as context manager."""
        with RealDrugDatabase(openfda_config) as db:
            assert db.is_connected == True
            info = db.get_drug_info("aspirin")

    def test_invalid_drug_name(self, drug_db):
        """Test handling of invalid drug name."""
        result = drug_db.get_drug_info("xyz_invalid_drug_123")

        # Should return None for invalid drug
        assert result is None


class TestDrugDatabaseCompatibility:
    """Test compatibility with stub DrugDatabaseInterface API."""

    @pytest.fixture
    def openfda_config(self):
        """Get OpenFDA configuration."""
        config = get_config()
        return config.get_openfda_config()

    def test_api_compatibility(self, openfda_config):
        """Test that real interface has same methods as stub."""
        from medical_task_suite.tool_interfaces.drug_database_interface import DrugDatabaseInterface

        real_db = RealDrugDatabase(openfda_config)

        # Check that real interface has all required methods
        required_methods = [
            'connect',
            'disconnect',
            'get_drug_info',
            'search_drugs',
            'check_interactions',
            'check_allergy',
            'check_contraindications',
            'get_dosage_info',
            'find_alternatives',
            'get_side_effects',
            'check_pregnancy_safety',
            'verify_drug_name',
            'get_drug_price',
            'get_formulary_status'
        ]

        for method in required_methods:
            assert hasattr(real_db, method)


class TestDrugDataExtraction:
    """Test data extraction from OpenFDA responses."""

    @pytest.fixture
    def openfda_config(self):
        """Get OpenFDA configuration."""
        config = get_config()
        return config.get_openfda_config()

    @pytest.fixture
    def drug_db(self, openfda_config):
        """Create drug database instance."""
        db = RealDrugDatabase(openfda_config)
        db.connect()
        yield db
        db.disconnect()

    def test_pregnancy_category_extraction(self, drug_db):
        """Test pregnancy category is extracted correctly."""
        result = drug_db.check_pregnancy_safety("aspirin")

        # Category should be one of the valid categories
        valid_categories = ['A', 'B', 'C', 'D', 'X', 'N', '']
        assert result['category'] in valid_categories

    def test_drug_category_determination(self, drug_db):
        """Test drug category (OTC/prescription) determination."""
        info = drug_db.get_drug_info("aspirin")

        if info:
            # Should have a valid category
            assert isinstance(info.category, DrugCategory)

    def test_side_effect_categorization(self, drug_db):
        """Test side effects are categorized by severity."""
        effects = drug_db.get_side_effects("aspirin")

        # Should have categorized effects
        assert 'common' in effects
        assert 'serious' in effects
        assert 'rare' in effects


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
