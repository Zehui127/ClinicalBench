"""
Test script to verify clinical domains are working correctly
"""

from tau2.registry import registry


def test_clinical_domains_registration():
    """Test that all clinical domains are registered"""
    print("=" * 60)
    print("Testing Clinical Domains Registration")
    print("=" * 60)

    info = registry.get_info()
    clinical_domains = [d for d in info.domains if d.startswith('clinical_')]

    print(f"\n[OK] Found {len(clinical_domains)} clinical domains:")
    for domain in clinical_domains:
        print(f"   - {domain}")

    assert len(clinical_domains) == 5, f"Expected 5 clinical domains, got {len(clinical_domains)}"
    print(f"\n[OK] All 5 clinical domains registered successfully!")

    return clinical_domains


def test_clinical_tasks_loading():
    """Test that clinical domains can load tasks"""
    print("\n" + "=" * 60)
    print("Testing Clinical Tasks Loading")
    print("=" * 60)

    clinical_domains = [
        "clinical_cardiology",
        "clinical_endocrinology",
        "clinical_gastroenterology",
        "clinical_nephrology",
        "clinical_neurology",
    ]

    for domain_name in clinical_domains:
        try:
            tasks_loader = registry.get_tasks_loader(domain_name)
            tasks = tasks_loader()

            print(f"\n[OK] {domain_name}:")
            print(f"   - Loaded {len(tasks)} tasks")

            if len(tasks) > 0:
                print(f"   - First task ID: {tasks[0].task_id if hasattr(tasks[0], 'task_id') else 'N/A'}")

        except Exception as e:
            print(f"\n[ERROR] {domain_name}: Failed to load tasks - {str(e)}")
            raise

    print(f"\n[OK] All clinical domains loaded tasks successfully!")


def test_clinical_environments():
    """Test that clinical domains can create environments"""
    print("\n" + "=" * 60)
    print("Testing Clinical Environments")
    print("=" * 60)

    clinical_domains = [
        ("clinical_cardiology", "Cardiology"),
        ("clinical_endocrinology", "Endocrinology"),
        ("clinical_gastroenterology", "Gastroenterology"),
        ("clinical_nephrology", "Nephrology"),
        ("clinical_neurology", "Neurology"),
    ]

    for domain_name, display_name in clinical_domains:
        try:
            env_constructor = registry.get_env_constructor(domain_name)
            env = env_constructor()

            print(f"\n[OK] {display_name}:")
            print(f"   - Environment created successfully")
            print(f"   - Environment type: {type(env).__name__}")

        except Exception as e:
            print(f"\n[ERROR] {display_name}: Failed to create environment - {str(e)}")
            raise

    print(f"\n[OK] All clinical environments created successfully!")


def main():
    """Run all tests"""
    print("\n[TEST] Clinical Domains Test Suite")
    print("=" * 60)

    try:
        # Test 1: Registration
        clinical_domains = test_clinical_domains_registration()

        # Test 2: Tasks Loading
        test_clinical_tasks_loading()

        # Test 3: Environment Creation
        test_clinical_environments()

        print("\n" + "=" * 60)
        print("[SUCCESS] ALL TESTS PASSED!")
        print("=" * 60)
        print("\n[INFO] Clinical domains are fully functional!")
        print("\nRegistered clinical domains:")
        for domain in clinical_domains:
            print(f"   [+] {domain}")

    except Exception as e:
        print(f"\n[FAILED] TEST FAILED: {str(e)}")
        raise


if __name__ == "__main__":
    main()
