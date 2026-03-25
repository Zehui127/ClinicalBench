"""
Example: Using Real HIS and Drug Database Interfaces

This example demonstrates how to use the real interface implementations
for accessing actual medical data via HAPI FHIR and OpenFDA APIs.

To run with real interfaces:
    export USE_REAL_INTERFACES=true
    export OPENFDA_API_KEY=your_api_key_here  # Optional but recommended
    python example_06_real_interfaces.py

To run with stub interfaces (default):
    python example_06_real_interfaces.py
"""

import os
from datetime import datetime

from medical_task_suite.tool_interfaces import (
    HISInterface,
    DrugDatabaseInterface,
    get_config
)
from medical_task_suite.tool_interfaces.real.his_fhir import RealHISInterface
from medical_task_suite.tool_interfaces.real.drug_openfda import RealDrugDatabase


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print('=' * 70)


def check_interface_mode():
    """Check and display which interface mode is active."""
    config = get_config()

    print_section("Interface Mode")
    if config.is_real_enabled():
        print("✓ Using REAL interfaces (HAPI FHIR + OpenFDA)")
        print(f"  - FHIR URL: {config.get_fhir_config().get('base_url')}")
        print(f"  - OpenFDA URL: {config.get_openfda_config().get('base_url')}")
        print(f"  - Fallback to stub: {config.should_fallback_to_stub()}")
    else:
        print("✓ Using STUB interfaces (mock data)")
        print("\nTo enable real interfaces:")
        print("  export USE_REAL_INTERFACES=true")


def example_his_interface():
    """Demonstrate HIS interface usage."""
    print_section("HIS Interface Example")

    # Create and connect to HIS
    his = HISInterface()

    print("\nConnecting to HIS...")
    if not his.connect():
        print("✗ Failed to connect to HIS")
        return

    print("✓ Connected to HIS")

    try:
        # Example 1: Get patient demographics
        print("\n1. Getting patient demographics...")
        patient = his.get_patient_demographics("example")

        print(f"   Patient ID: {patient.get('patient_id', 'N/A')}")
        print(f"   Name: {patient.get('name', 'N/A')}")
        print(f"   Age: {patient.get('age', 'N/A')}")
        print(f"   Gender: {patient.get('gender', 'N/A')}")
        print(f"   Birth Date: {patient.get('birth_date', 'N/A')}")

        # Example 2: Search for patients
        print("\n2. Searching for patients...")
        patients = his.search_patients(name="Smith")

        print(f"   Found {len(patients)} patients")
        for i, p in enumerate(patients[:3], 1):
            print(f"   {i}. {p.get('name', 'Unknown')} ({p.get('gender', 'N/A')})")

        # Example 3: Get lab results
        print("\n3. Getting lab results...")
        labs = his.get_lab_results("example")

        print(f"   Found {len(labs)} lab results")
        for i, lab in enumerate(labs[:3], 1):
            test_name = lab.get('test_name', 'Unknown')
            value = lab.get('value', 'N/A')
            unit = lab.get('unit', '')
            print(f"   {i}. {test_name}: {value} {unit}")

        # Example 4: Get medication history
        print("\n4. Getting medication history...")
        meds = his.get_medication_history("example")

        print(f"   Found {len(meds)} medications")
        for i, med in enumerate(meds[:3], 1):
            name = med.get('medication_name', 'Unknown')
            dosage = med.get('dosage', 'N/A')
            print(f"   {i}. {name} - {dosage}")

        # Example 5: Get appointments
        print("\n5. Getting appointments...")
        appointments = his.get_appointments("example")

        print(f"   Found {len(appointments)} appointments")
        for i, apt in enumerate(appointments[:3], 1):
            doctor = apt.doctor if hasattr(apt, 'doctor') else 'N/A'
            status = apt.status if hasattr(apt, 'status') else 'N/A'
            print(f"   {i}. Doctor: {doctor}, Status: {status}")

        # Example 6: Cache statistics
        print("\n6. Cache performance...")
        if hasattr(his, 'get_cache_stats'):
            stats = his.get_cache_stats()
            if stats:
                print(f"   Cache size: {stats['size']}/{stats['max_size']}")
                print(f"   Hit rate: {stats['hit_rate']}")
                print(f"   Total hits: {stats['hits']}")
                print(f"   Total misses: {stats['misses']}")

    finally:
        his.disconnect()
        print("\n✓ Disconnected from HIS")


def example_drug_database():
    """Demonstrate drug database interface usage."""
    print_section("Drug Database Interface Example")

    # Create and connect to drug database
    drug_db = DrugDatabaseInterface()

    print("\nConnecting to Drug Database...")
    if not drug_db.connect():
        print("✗ Failed to connect to Drug Database")
        return

    print("✓ Connected to Drug Database")

    try:
        # Example 1: Get drug information
        print("\n1. Getting drug information for Aspirin...")
        drug_info = drug_db.get_drug_info("aspirin")

        if drug_info:
            print(f"   Generic Name: {drug_info.generic_name}")
            print(f"   Brand Names: {', '.join(drug_info.brand_names[:3])}")
            print(f"   Category: {drug_info.category.value if hasattr(drug_info.category, 'value') else drug_info.category}")
            print(f"   Pregnancy Category: {drug_info.pregnancy_category}")

            if drug_info.indications:
                print(f"   Indication: {drug_info.indications[0][:100]}...")
        else:
            print("   No drug information found")

        # Example 2: Search for drugs
        print("\n2. Searching for pain relievers...")
        results = drug_db.search_drugs("pain", search_type="indication")

        print(f"   Found {len(results)} drugs")
        for i, drug in enumerate(results[:3], 1):
            generic = drug.get('generic_name', 'Unknown')
            brands = drug.get('brand_names', [])
            print(f"   {i}. {generic} (brands: {', '.join(brands[:2])})")

        # Example 3: Check drug interactions
        print("\n3. Checking drug interactions (Aspirin + Warfarin)...")
        interactions = drug_db.check_interactions(["aspirin", "warfarin"])

        if interactions:
            print(f"   Found {len(interactions)} interactions")
            for i, interaction in enumerate(interactions[:2], 1):
                print(f"   {i}. Severity: {interaction.severity}")
                desc = interaction.description[:100]
                print(f"      {desc}...")
        else:
            print("   No interactions found")

        # Example 4: Check pregnancy safety
        print("\n4. Checking pregnancy safety for Lisinopril...")
        safety = drug_db.check_pregnancy_safety("lisinopril")

        print(f"   Category: {safety['category']}")
        print(f"   Recommendation: {safety['recommendation']}")

        # Example 5: Get side effects
        print("\n5. Getting side effects for Aspirin...")
        effects = drug_db.get_side_effects("aspirin")

        print(f"   Common effects: {len(effects.get('common', []))}")
        print(f"   Serious effects: {len(effects.get('serious', []))}")

        if effects.get('common'):
            print(f"   Example common effects: {', '.join(effects['common'][:2])}")

        # Example 6: Verify drug name
        print("\n6. Verifying drug name (with typo: 'asprin')...")
        matches = drug_db.verify_drug_name("asprin")

        if matches:
            print(f"   Did you mean:")
            for match in matches[:3]:
                print(f"   - {match['name']}? (confidence: {match['confidence']})")
        else:
            print("   No similar drugs found")

        # Example 7: Get dosage information
        print("\n7. Getting dosage information...")
        dosage = drug_db.get_dosage_info(
            "aspirin",
            patient_age=45,
            patient_weight=70.0,
            condition="pain"
        )

        print(f"   Standard dosage: {dosage.get('standard_dosage', 'N/A')}")
        print(f"   Frequency: {dosage.get('frequency', 'N/A')}")

        # Example 8: Cache statistics
        print("\n8. Cache performance...")
        if hasattr(drug_db, 'cache') and drug_db.cache:
            stats = drug_db.cache.get_stats()
            print(f"   Cache size: {stats['size']}/{stats['max_size']}")
            print(f"   Hit rate: {stats['hit_rate']}")

    finally:
        drug_db.disconnect()
        print("\n✓ Disconnected from Drug Database")


def example_combined_workflow():
    """Demonstrate a combined workflow using both interfaces."""
    print_section("Combined Workflow Example")

    print("\nScenario: Prescribing medication for a patient with allergies")

    # Create interfaces
    his = HISInterface()
    drug_db = DrugDatabaseInterface()

    # Connect to both
    print("\nConnecting to systems...")
    his.connect()
    drug_db.connect()
    print("✓ Connected to both systems")

    try:
        # Step 1: Get patient information
        print("\n1. Getting patient information...")
        patient = his.get_patient_demographics("example")
        print(f"   Patient: {patient.get('name', 'Unknown')}, Age: {patient.get('age', 'N/A')}")

        # Step 2: Get patient allergies (from medication history)
        print("\n2. Checking patient allergies...")
        patient_allergies = ["penicillin", "sulfa"]  # Example allergies
        print(f"   Known allergies: {', '.join(patient_allergies)}")

        # Step 3: Consider prescribing a medication
        print("\n3. Checking medication safety...")
        medication = "amoxicillin"

        # Check for allergies
        allergy_check = drug_db.check_allergy(medication, patient_allergies)

        if allergy_check['has_allergy']:
            print(f"   ⚠ ALLERGY ALERT: {allergy_check['description']}")
            print(f"   Severity: {allergy_check['severity']}")
        else:
            print(f"   ✓ No allergy conflict detected")

        # Step 4: Check for drug interactions
        print("\n4. Checking for drug interactions...")
        current_meds = ["lisinopril", "metformin"]

        interactions = drug_db.check_interactions([medication] + current_meds)

        if interactions:
            print(f"   ⚠ Found {len(interactions)} potential interactions")
            for interaction in interactions[:2]:
                print(f"   - {interaction.drug1} + {interaction.drug2}: {interaction.severity}")
        else:
            print("   ✓ No significant interactions found")

        # Step 5: Get dosage information
        print("\n5. Getting dosage recommendations...")
        dosage = drug_db.get_dosage_info(
            medication,
            patient_age=patient.get('age', 45),
            patient_weight=70.0,
            condition="infection"
        )

        print(f"   Standard dosage: {dosage.get('standard_dosage', 'Consult doctor')}")
        print(f"   Frequency: {dosage.get('frequency', 'N/A')}")

        # Step 6: Check pregnancy safety if applicable
        if patient.get('gender') == 'female':
            print("\n6. Checking pregnancy safety...")
            safety = drug_db.check_pregnancy_safety(medication)
            print(f"   Category: {safety['category']}")
            print(f"   {safety['recommendation']}")

        print("\n✓ Medication safety check complete")

    finally:
        his.disconnect()
        drug_db.disconnect()
        print("\n✓ Disconnected from both systems")


def example_context_managers():
    """Demonstrate using context managers for automatic cleanup."""
    print_section("Context Manager Example")

    print("\nUsing context managers for automatic connection cleanup...")

    # HIS with context manager
    with HISInterface() as his:
        print("\n✓ Automatically connected to HIS")
        patient = his.get_patient_demographics("example")
        print(f"   Retrieved patient: {patient.get('name', 'Unknown')}")
    print("✓ Automatically disconnected from HIS")

    # Drug database with context manager
    with DrugDatabaseInterface() as drug_db:
        print("\n✓ Automatically connected to Drug Database")
        info = drug_db.get_drug_info("aspirin")
        if info:
            print(f"   Retrieved drug: {info.generic_name}")
    print("✓ Automatically disconnected from Drug Database")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("  Medical Task Suite - Real Interfaces Examples")
    print("=" * 70)

    # Check which mode we're running in
    check_interface_mode()

    # Run examples
    try:
        example_his_interface()
        example_drug_database()
        example_combined_workflow()
        example_context_managers()

        print_section("Summary")
        print("\n✓ All examples completed successfully!")
        print("\nKey Takeaways:")
        print("  - Same code works with both stub and real interfaces")
        print("  - Use environment variable to switch between modes")
        print("  - Real interfaces provide actual medical data")
        print("  - Caching improves performance automatically")
        print("  - Context managers ensure proper cleanup")

        # Show performance stats if available
        config = get_config()
        if config.is_real_enabled():
            print("\nNote: Running in REAL mode")
            print("  - API calls are being made to HAPI FHIR and OpenFDA")
            print("  - Enable OPENFDA_API_KEY for higher rate limits")
            print("  - Monitor cache statistics to optimize performance")
        else:
            print("\nNote: Running in STUB mode (mock data)")
            print("  - Set USE_REAL_INTERFACES=true to use real APIs")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
