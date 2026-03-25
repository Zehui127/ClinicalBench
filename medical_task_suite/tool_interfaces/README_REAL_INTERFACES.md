# Real HIS and Drug Database Interfaces

This document describes the real interface implementations for the Medical Task Suite, which provide access to actual medical APIs including HAPI FHIR and OpenFDA.

## Overview

The Medical Task Suite now supports two modes of operation:

1. **Stub Mode** (default): Uses mock/stub implementations for testing and development
2. **Real Mode**: Uses actual APIs (HAPI FHIR, OpenFDA) for production and research

Both modes use the same API, ensuring code compatibility without changes.

## Quick Start

### Using Stub Interfaces (Default)

```python
from medical_task_suite.tool_interfaces import HISInterface, DrugDatabaseInterface

# Create interfaces - automatically uses stub implementations
his = HISInterface()
drug_db = DrugDatabaseInterface()

# Use the interfaces
patient = his.get_patient_demographics("test_patient")
medications = drug_db.get_drug_info("aspirin")
```

### Using Real Interfaces

**Option 1: Environment Variable**

```bash
# Set environment variable
export USE_REAL_INTERFACES=true

# Optional: Set OpenFDA API key for higher rate limits
export OPENFDA_API_KEY=your_api_key_here

# Run your Python code
python your_script.py
```

**Option 2: Configuration File**

Edit `medical_task_suite/tool_interfaces/config/api_config.yaml`:

```yaml
interface:
  use_real: true  # Enable real interfaces
  fallback_to_stub: true  # Fallback to stub if API fails

openfda:
  api_key: your_api_key_here  # Optional but recommended
```

Then run your code normally - no changes needed!

## Supported Interfaces

### 1. HIS Interface (Hospital Information System)

**Implementation**: HAPI FHIR
**Base URL**: https://hapi.fhir.org/baseR4
**Documentation**: https://hapifhir.io/

#### Features

- Patient demographic information
- Medical records and encounters
- Lab results and observations
- Medication history
- Appointments scheduling
- Patient search

#### Example Usage

```python
from medical_task_suite.tool_interfaces import HISInterface

# Create interface
his = HISInterface()

# Connect to server
his.connect()

# Get patient demographics
patient = his.get_patient_demographics("example")
print(f"Patient: {patient['name']}, Age: {patient['age']}")

# Get lab results
labs = his.get_lab_results("example")
for lab in labs:
    print(f"{lab['test_name']}: {lab['value']} {lab['unit']}")

# Get medication history
meds = his.get_medication_history("example")
for med in meds:
    print(f"{med['medication_name']}: {med['dosage']}")

# Search for patients
patients = his.search_patients(name="Smith")
for p in patients:
    print(f"Found: {p['name']}")

# Disconnect when done
his.disconnect()
```

#### FHIR Resources Used

- **Patient**: Patient demographic information
- **Encounter**: Medical visits/encounters
- **Observation**: Lab results and clinical observations
- **MedicationRequest**: Medication orders and history
- **Appointment**: Appointment scheduling
- **Condition**: Diagnoses and conditions

### 2. Drug Database Interface

**Implementation**: OpenFDA API
**Base URL**: https://api.fda.gov
**Documentation**: https://open.fda.gov/

#### Features

- Drug information (brand/generic names, manufacturers)
- Indications and contraindications
- Drug interactions
- Side effects (adverse reactions)
- Dosage information
- Pregnancy safety categories
- Drug search and verification

#### Example Usage

```python
from medical_task_suite.tool_interfaces import DrugDatabaseInterface

# Create interface
drug_db = DrugDatabaseInterface()

# Connect to API
drug_db.connect()

# Get drug information
info = drug_db.get_drug_info("aspirin")
print(f"Generic: {info.generic_name}")
print(f"Brand names: {', '.join(info.brand_names)}")
print(f"Indications: {info.indications}")

# Check drug interactions
interactions = drug_db.check_interactions(["aspirin", "warfarin"])
for interaction in interactions:
    print(f"{interaction.drug1} + {interaction.drug2}: {interaction.severity}")
    print(f"  {interaction.description}")

# Check pregnancy safety
safety = drug_db.check_pregnancy_safety("lisinopril")
print(f"Pregnancy category: {safety['category']}")
print(f"Recommendation: {safety['recommendation']}")

# Search for drugs
results = drug_db.search_drugs("pain reliever", search_type="indication")
for drug in results:
    print(f"{drug['generic_name']} - {drug['brand_names']}")

# Get side effects
effects = drug_db.get_side_effects("aspirin")
print(f"Common side effects: {effects['common']}")
print(f"Serious side effects: {effects['serious']}")

# Verify drug name (for typos)
matches = drug_db.verify_drug_name("asprin")  # Note: typo
for match in matches:
    print(f"Did you mean: {match['name']}? (confidence: {match['confidence']})")

# Disconnect
drug_db.disconnect()
```

#### OpenFDA Endpoints Used

- **Drug Label**: `/drug/label.json` - Drug labeling information
- **Drug Event**: `/drug/event.json` - Adverse event reports

## Configuration

### API Configuration File

Location: `medical_task_suite/tool_interfaces/config/api_config.yaml`

```yaml
# FHIR API Configuration
fhir:
  base_url: "https://hapi.fhir.org/baseR4"
  timeout: 30
  max_retries: 3
  retry_delay: 1
  cache_ttl: 3600

# OpenFDA API Configuration
openfda:
  base_url: "https://api.fda.gov"
  drug_label_endpoint: "/drug/label.json"
  drug_event_endpoint: "/drug/event.json"
  api_key: null  # Set via environment variable
  timeout: 30
  max_retries: 3
  retry_delay: 1
  rate_limit: 240  # Requests per minute
  rate_limit_burst: 10
  cache_ttl: 3600

# Cache Configuration
cache:
  enabled: true
  default_ttl: 3600
  max_size: 1000

# Logging Configuration
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Interface Selection
interface:
  use_real: false  # Set to true for real APIs
  fallback_to_stub: true  # Fallback to stub on API failure
  timeout_fallback: 5  # Seconds before fallback
```

### Environment Variables

- `USE_REAL_INTERFACES`: Set to "true" to enable real interfaces
- `OPENFDA_API_KEY`: Optional API key for higher rate limits (get from https://open.fda.gov/api/reference/)

## API Rate Limits

### HAPI FHIR

The public HAPI FHIR test server has no strict rate limits but requests moderate usage.

**Best Practices**:
- Use caching to reduce redundant requests
- Implement appropriate delays between batch requests
- Consider setting up your own FHIR server for production use

### OpenFDA

**Without API Key**:
- 240 requests per minute
- 1,200 requests per day

**With API Key** (free):
- 1,200 requests per minute
- 120,000 requests per day

**Get an API Key**: https://open.fda.gov/api/reference/

## Caching

Both real interfaces implement caching to reduce API calls and improve performance:

```python
# Get cache statistics
his = HISInterface()
his.connect()

# Make some requests...
his.get_patient_demographics("example")

# Check cache stats
stats = his.get_cache_stats()
print(f"Cache hit rate: {stats['hit_rate']}")
print(f"Cache size: {stats['size']}/{stats['max_size']}")

# Clear cache if needed
his.clear_cache()
```

## Rate Limiting

The interfaces include built-in rate limiting to comply with API limits:

```python
# Check rate limiter status
drug_db = DrugDatabaseInterface()
drug_db.connect()

# Make requests - rate limiter automatically handles delays
for drug in ["aspirin", "ibuprofen", "acetaminophen"]:
    info = drug_db.get_drug_info(drug)

# Get rate limiter stats
stats = drug_db.get_rate_limiter_stats()
print(f"Calls in period: {stats['calls_in_period']}")
print(f"Available slots: {stats['available_slots']}")
```

## Error Handling

The interfaces include comprehensive error handling:

```python
from medical_task_suite.tool_interfaces import HISInterface

his = HISInterface()

try:
    his.connect()
    patient = his.get_patient_demographics("example")
except RuntimeError as e:
    print(f"Connection error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
finally:
    his.disconnect()
```

With `fallback_to_stub` enabled, API failures automatically fall back to stub implementations:

```python
# If API fails, automatically uses stub data
config = get_config()
if config.should_fallback_to_stub():
    print("API failures will use stub data")
```

## Performance Considerations

### For Evaluation/Research

1. **Enable caching**: Reduces API calls by ~50-80%
2. **Use batch operations**: Request multiple items at once when possible
3. **Get API key**: Dramatically increases OpenFDA rate limits
4. **Use context managers**: Ensures proper cleanup

```python
# Efficient pattern using context manager
from medical_task_suite.tool_interfaces import HISInterface

with HISInterface() as his:
    # All operations benefit from pooled connections
    patients = his.search_patients(name="Smith")
    for patient in patients:
        data = his.get_patient_demographics(patient['patient_id'])
```

### Cache Performance

Monitor cache effectiveness:

```python
his = HISInterface()
his.connect()

# Make various requests...
# ... make requests ...

# Check performance
stats = his.get_cache_stats()
target_hit_rate = 50.0  # Aim for 50%+

if float(stats['hit_rate'].rstrip('%')) < target_hit_rate:
    print("Warning: Low cache hit rate. Consider increasing TTL.")
```

## Testing

Run unit tests for real interfaces:

```bash
# Test HIS FHIR interface
pytest medical_task_suite/tests/test_his_fhir.py -v

# Test OpenFDA interface
pytest medical_task_suite/tests/test_drug_openfda.py -v

# Test all interfaces
pytest medical_task_suite/tests/ -v
```

## Troubleshooting

### Connection Issues

**Problem**: Cannot connect to FHIR server

**Solution**:
```python
his = HISInterface()
if not his.connect():
    print("FHIR server unavailable")
    # Enable fallback to stub
```

**Problem**: OpenFDA rate limit exceeded

**Solution**:
- Get an API key from https://open.fda.gov/
- Set `OPENFDA_API_KEY` environment variable
- Increase `rate_limit` in configuration if using API key

### Data Quality Issues

**Problem**: Missing or incomplete data

**Reason**: Public test servers have limited data

**Solution**:
- Use specific patient IDs known to exist (e.g., "example" on HAPI FHIR)
- For production, set up your own FHIR server
- Consider hybrid approach: stub for testing, real for specific queries

### Performance Issues

**Problem**: Slow response times

**Solutions**:
1. Enable caching (default: on)
2. Increase cache TTL in configuration
3. Use API keys for higher rate limits
4. Implement batch processing

## Production Deployment

For production use, consider:

1. **Private FHIR Server**: Set up your own HAPI FHIR instance
2. **API Keys**: Obtain and configure OpenFDA API key
3. **Monitoring**: Enable logging and monitor API usage
4. **Scaling**: Consider Redis for distributed caching
5. **Error Tracking**: Integrate with error tracking (Sentry, etc.)

```yaml
# Production configuration example
interface:
  use_real: true
  fallback_to_stub: false  # Don't fall back in production

fhir:
  base_url: "https://your-fhir-server.com/fhir/R4"

openfda:
  api_key: "${OPENFDA_API_KEY}"  # From environment
  rate_limit: 1200  # With API key

logging:
  level: "WARNING"
  file: "/var/log/medical_task_suite.log"
```

## References

- **FHIR Specification**: https://hl7.org/fhir/
- **HAPI FHIR**: https://hapifhir.io/
- **OpenFDA API**: https://open.fda.gov/
- **OpenFDA Documentation**: https://open.fda.gov/api/reference/

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review unit tests for usage examples
3. Consult API documentation (links above)
4. Check GitHub issues for the project
