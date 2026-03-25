"""
HAPI FHIR HIS Interface Implementation

This module provides a real implementation of the HIS interface using
the HAPI FHIR public test server (https://hapi.fhir.org).

FHIR (Fast Healthcare Interoperability Resources) is a standard for
exchanging healthcare data electronically.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, replace

from medical_task_suite.tool_interfaces.real.base_real_interface import BaseRealInterface
from medical_task_suite.tool_interfaces.his_interface import (
    HISInterface,
    PatientRecord,
    Appointment,
    RecordType
)
from medical_task_suite.utils.logger import get_logger


class RealHISInterface(HISInterface):
    """
    Real HIS interface implementation using HAPI FHIR.

    This class connects to a FHIR server and provides real patient data,
    appointments, lab results, and medication history.

    It maintains compatibility with the stub HISInterface API.
    """

    # FHIR resource type mappings
    RESOURCE_PATIENT = "Patient"
    RESOURCE_OBSERVATION = "Observation"
    RESOURCE_MEDICATION_REQUEST = "MedicationRequest"
    RESOURCE_APPOINTMENT = "Appointment"
    RESOURCE_CONDITION = "Condition"
    RESOURCE_ENCOUNTER = "Encounter"

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the real HIS interface.

        Args:
            config: Configuration dictionary with FHIR settings
        """
        # Initialize base interface
        super().__init__(config)

        # FHIR-specific settings
        self.base_url = config.get('base_url', 'https://hapi.fhir.org/baseR4')
        self.fhir_version = "R4"

        # Use base class components
        from medical_task_suite.utils.cache_manager import CacheManager
        from medical_task_suite.utils.rate_limiter import RateLimiter

        self.cache = CacheManager(ttl=config.get('cache_ttl', 3600))
        self.timeout = config.get('timeout', 30)

        # Override logger
        self.logger = get_logger(self.__class__.__name__)

        # Initialize session via base class method
        import requests
        self.session = requests.Session()

        # Connection state
        self.is_connected = False

    def connect(self) -> bool:
        """
        Connect to the FHIR server and verify it's accessible.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Test connection by fetching server metadata
            url = f"{self.base_url}/metadata"
            response = self.session.get(url, timeout=self.timeout)

            if response.status_code == 200:
                self.is_connected = True
                self.logger.info(f"Connected to FHIR server: {self.base_url}")
                return True
            else:
                self.logger.error(f"Failed to connect: HTTP {response.status_code}")
                return False

        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            return False

    def disconnect(self):
        """Disconnect from the FHIR server."""
        self.is_connected = False
        if self.session:
            self.session.close()
        self.logger.info("Disconnected from FHIR server")

    def _search_fhir_resource(
        self,
        resource_type: str,
        params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Search for FHIR resources.

        Args:
            resource_type: FHIR resource type (Patient, Observation, etc.)
            params: Search parameters

        Returns:
            List of FHIR resources
        """
        if not self.is_connected:
            raise RuntimeError("Not connected to FHIR server")

        url = f"{self.base_url}/{resource_type}"

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            # FHIR Bundle response
            if 'entry' in data:
                return [entry['resource'] for entry in data['entry']]
            return []

        except Exception as e:
            self.logger.error(f"Error searching {resource_type}: {e}")
            return []

    def _read_fhir_resource(self, resource_type: str, resource_id: str) -> Optional[Dict[str, Any]]:
        """
        Read a specific FHIR resource by ID.

        Args:
            resource_type: FHIR resource type
            resource_id: Resource ID

        Returns:
            FHIR resource or None if not found
        """
        if not self.is_connected:
            raise RuntimeError("Not connected to FHIR server")

        url = f"{self.base_url}/{resource_type}/{resource_id}"

        try:
            response = self.session.get(url, timeout=self.timeout)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()

        except Exception as e:
            self.logger.error(f"Error reading {resource_type}/{resource_id}: {e}")
            return None

    def get_patient_demographics(self, patient_id: str) -> Dict[str, Any]:
        """
        Get patient demographic information.

        Args:
            patient_id: Patient identifier

        Returns:
            Dictionary with demographic information
        """
        # Try cache first
        cache_key = f"patient_demographics:{patient_id}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        patient = self._read_fhir_resource(self.RESOURCE_PATIENT, patient_id)

        if not patient:
            return {
                'patient_id': patient_id,
                'name': '',
                'age': 0,
                'gender': '',
                'phone': '',
                'address': '',
                'insurance': ''
            }

        # Extract demographic data
        demographics = {
            'patient_id': patient_id,
            'name': self._extract_patient_name(patient),
            'age': self._calculate_age(patient),
            'gender': patient.get('gender', ''),
            'phone': self._extract_phone(patient),
            'address': self._extract_address(patient),
            'insurance': self._extract_insurance(patient),
            'birth_date': patient.get('birthDate', ''),
            'marital_status': self._extract_marital_status(patient),
            'identifier': self._extract_identifiers(patient)
        }

        # Cache result
        self.cache.set(demographics, cache_key)

        return demographics

    def get_patient_record(
        self,
        patient_id: str,
        record_type: Optional[RecordType] = None,
        date_range: Optional[tuple] = None
    ) -> List[PatientRecord]:
        """
        Retrieve patient medical records.

        Args:
            patient_id: Patient identifier
            record_type: Type of records to retrieve (optional)
            date_range: Date range filter (start, end) (optional)

        Returns:
            List of PatientRecord objects
        """
        # Search for encounters
        params = {'patient': patient_id}

        if date_range:
            start_date, end_date = date_range
            params['date'] = f"ge{start_date}&le{end_date}"

        encounters = self._search_fhir_resource(self.RESOURCE_ENCOUNTER, params)

        records = []
        for encounter in encounters:
            # Convert encounter to PatientRecord
            record = self._fhir_encounter_to_record(encounter)
            if record_type is None or record.record_type == record_type:
                records.append(record)

        return records

    def get_lab_results(
        self,
        patient_id: str,
        test_type: Optional[str] = None,
        date_range: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        """
        Get patient lab results.

        Args:
            patient_id: Patient identifier
            test_type: Specific test type (optional)
            date_range: Date range filter (optional)

        Returns:
            List of lab result dictionaries
        """
        # Build search parameters
        params = {'patient': patient_id, 'category': 'laboratory'}

        if test_type:
            params['code'] = test_type

        if date_range:
            start_date, end_date = date_range
            params['date'] = f"ge{start_date}&le{end_date}"

        observations = self._search_fhir_resource(self.RESOURCE_OBSERVATION, params)

        # Convert to lab results format
        results = []
        for obs in observations:
            result = {
                'test_name': self._extract_observation_name(obs),
                'test_code': self._extract_observation_code(obs),
                'value': self._extract_observation_value(obs),
                'unit': self._extract_observation_unit(obs),
                'reference_range': self._extract_reference_range(obs),
                'status': obs.get('status', ''),
                'date': obs.get('effectiveDateTime', ''),
                'interpretation': self._extract_interpretation(obs)
            }
            results.append(result)

        return results

    def get_medication_history(
        self,
        patient_id: str,
        date_range: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        """
        Get patient medication history.

        Args:
            patient_id: Patient identifier
            date_range: Date range filter (optional)

        Returns:
            List of medication records
        """
        params = {'patient': patient_id}

        if date_range:
            start_date, end_date = date_range
            params['authoredon'] = f"ge{start_date}&le{end_date}"

        med_requests = self._search_fhir_resource(
            self.RESOURCE_MEDICATION_REQUEST,
            params
        )

        # Convert to medication history format
        medications = []
        for med in med_requests:
            medication = {
                'medication_name': self._extract_medication_name(med),
                'dosage': self._extract_dosage(med),
                'frequency': self._extract_frequency(med),
                'status': med.get('status', ''),
                'intent': med.get('intent', ''),
                'authored_on': med.get('authoredOn', ''),
                'requester': self._extract_requester(med)
            }
            medications.append(medication)

        return medications

    def get_appointments(
        self,
        patient_id: str,
        status: Optional[str] = None
    ) -> List[Appointment]:
        """
        Get patient appointments.

        Args:
            patient_id: Patient identifier
            status: Filter by status (optional)

        Returns:
            List of Appointment objects
        """
        params = {'patient': patient_id}

        if status:
            params['status'] = status

        appointments = self._search_fhir_resource(self.RESOURCE_APPOINTMENT, params)

        # Convert to Appointment format
        result = []
        for apt in appointments:
            appointment = self._fhir_appointment_to_appointment(apt)
            if appointment:
                result.append(appointment)

        return result

    def create_appointment(
        self,
        patient_id: str,
        department: str,
        doctor: str,
        appointment_time: datetime,
        purpose: str
    ) -> Optional[str]:
        """
        Create a new appointment.

        Args:
            patient_id: Patient identifier
            department: Department
            doctor: Doctor name
            appointment_time: Appointment time
            purpose: Purpose of visit

        Returns:
            Appointment ID if successful, None otherwise
        """
        if not self.is_connected:
            raise RuntimeError("Not connected to FHIR server")

        # Create FHIR Appointment resource
        appointment_resource = {
            'resourceType': 'Appointment',
            'status': 'booked',
            'participant': [
                {
                    'actor': {
                        'reference': f"Patient/{patient_id}"
                    },
                    'status': 'accepted'
                }
            ],
            'start': appointment_time.isoformat(),
            'description': purpose,
            'comment': f"Department: {department}, Doctor: {doctor}"
        }

        try:
            url = f"{self.base_url}/Appointment"
            response = self.session.post(url, json=appointment_resource, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            appointment_id = data.get('id')

            self.logger.info(f"Created appointment: {appointment_id}")
            return appointment_id

        except Exception as e:
            self.logger.error(f"Error creating appointment: {e}")
            return None

    def search_patients(
        self,
        name: Optional[str] = None,
        id_number: Optional[str] = None,
        phone: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for patients by various criteria.

        Args:
            name: Patient name (optional)
            id_number: ID number (optional)
            phone: Phone number (optional)

        Returns:
            List of matching patients
        """
        params = {}

        if name:
            params['name'] = name
        if id_number:
            params['identifier'] = id_number
        if phone:
            params['phone'] = phone

        patients = self._search_fhir_resource(self.RESOURCE_PATIENT, params)

        # Convert to search result format
        results = []
        for patient in patients:
            result = {
                'patient_id': patient.get('id', ''),
                'name': self._extract_patient_name(patient),
                'gender': patient.get('gender', ''),
                'birth_date': patient.get('birthDate', '')
            }
            results.append(result)

        return results

    # Helper methods for extracting data from FHIR resources

    def _extract_patient_name(self, patient: Dict) -> str:
        """Extract patient name from FHIR Patient resource."""
        names = patient.get('name', [])
        if names:
            name_entry = names[0]
            given = name_entry.get('given', [''])[0]
            family = name_entry.get('family', '')
            return f"{given} {family}".strip()
        return ''

    def _calculate_age(self, patient: Dict) -> int:
        """Calculate age from birth date."""
        birth_date_str = patient.get('birthDate')
        if birth_date_str:
            try:
                birth_date = datetime.fromisoformat(birth_date_str.replace('Z', '+00:00'))
                today = datetime.now()
                age = today.year - birth_date.year
                if (today.month, today.day) < (birth_date.month, birth_date.day):
                    age -= 1
                return age
            except:
                pass
        return 0

    def _extract_phone(self, patient: Dict) -> str:
        """Extract phone number from patient."""
        telecoms = patient.get('telecom', [])
        for telecom in telecoms:
            if telecom.get('system') == 'phone':
                return telecom.get('value', '')
        return ''

    def _extract_address(self, patient: Dict) -> str:
        """Extract address from patient."""
        addresses = patient.get('address', [])
        if addresses:
            address = addresses[0]
            parts = [
                address.get('line', [''])[0] if address.get('line') else '',
                address.get('city', ''),
                address.get('state', ''),
                address.get('postalCode', '')
            ]
            return ', '.join(p for p in parts if p).strip()
        return ''

    def _extract_insurance(self, patient: Dict) -> str:
        """Extract insurance information."""
        # FHIR uses Coverage resources for insurance
        # This is a simplified version
        return ''

    def _extract_marital_status(self, patient: Dict) -> str:
        """Extract marital status."""
        marital = patient.get('maritalStatus', {})
        coding = marital.get('coding', [])
        if coding:
            return coding[0].get('display', '')
        return ''

    def _extract_identifiers(self, patient: Dict) -> List[str]:
        """Extract patient identifiers."""
        identifiers = patient.get('identifier', [])
        return [id.get('value', '') for id in identifiers if 'value' in id]

    def _extract_observation_name(self, obs: Dict) -> str:
        """Extract observation test name."""
        code = obs.get('code', {})
        coding = code.get('coding', [])
        if coding:
            return coding[0].get('display', '')
        return code.get('text', '')

    def _extract_observation_code(self, obs: Dict) -> str:
        """Extract observation test code."""
        code = obs.get('code', {})
        coding = code.get('coding', [])
        if coding:
            return coding[0].get('code', '')
        return ''

    def _extract_observation_value(self, obs: Dict) -> Any:
        """Extract observation value."""
        if 'valueQuantity' in obs:
            return obs['valueQuantity'].get('value')
        if 'valueCodeableConcept' in obs:
            return obs['valueCodeableConcept'].get('text', '')
        if 'valueString' in obs:
            return obs['valueString']
        return None

    def _extract_observation_unit(self, obs: Dict) -> str:
        """Extract observation unit."""
        if 'valueQuantity' in obs:
            return obs['valueQuantity'].get('unit', '')
        return ''

    def _extract_reference_range(self, obs: Dict) -> str:
        """Extract reference range."""
        ref_ranges = obs.get('referenceRange', [])
        if ref_ranges:
            range_info = ref_ranges[0]
            low = range_info.get('low', {}).get('value')
            high = range_info.get('high', {}).get('value')
            unit = range_info.get('low', {}).get('unit', '')

            if low and high:
                return f"{low} - {high} {unit}"
            elif low:
                return f">= {low} {unit}"
            elif high:
                return f"<= {high} {unit}"
        return ''

    def _extract_interpretation(self, obs: Dict) -> str:
        """Extract interpretation."""
        interpretations = obs.get('interpretation', [])
        if interpretations:
            coding = interpretations[0].get('coding', [])
            if coding:
                return coding[0].get('display', '')
        return ''

    def _extract_medication_name(self, med_req: Dict) -> str:
        """Extract medication name."""
        med_ref = med_req.get('medicationReference', {})
        if 'display' in med_ref:
            return med_ref['display']

        med_code = med_req.get('medicationCodeableConcept', {})
        coding = med_code.get('coding', [])
        if coding:
            return coding[0].get('display', '')
        return ''

    def _extract_dosage(self, med_req: Dict) -> str:
        """Extract dosage instruction."""
        dosages = med_req.get('dosageInstruction', [])
        if dosages:
            dose = dosages[0]
            dose_qty = dose.get('doseAndRate', [{}])[0].get('doseQuantity', {})
            value = dose_qty.get('value', '')
            unit = dose_qty.get('unit', '')
            if value and unit:
                return f"{value} {unit}"
        return ''

    def _extract_frequency(self, med_req: Dict) -> str:
        """Extract medication frequency."""
        dosages = med_req.get('dosageInstruction', [])
        if dosages:
            timing = dosages[0].get('timing', {})
            code = timing.get('code', {})
            coding = code.get('coding', [])
            if coding:
                return coding[0].get('display', '')
        return ''

    def _extract_requester(self, med_req: Dict) -> str:
        """Extract medication requester."""
        req = med_req.get('requester', {})
        if 'display' in req:
            return req['display']
        return ''

    def _fhir_encounter_to_record(self, encounter: Dict) -> PatientRecord:
        """Convert FHIR Encounter to PatientRecord."""
        # Extract basic info
        patient_ref = encounter.get('subject', {}).get('reference', '')
        patient_id = patient_ref.split('/')[-1] if patient_ref else ''

        # Convert encounter type to record type
        fhir_type = encounter.get('type', [])
        record_type = RecordType.OUTPATIENT  # default

        # Try to determine record type from FHIR data
        type_codings = []
        for t in fhir_type:
            codings = t.get('coding', [])
            type_codings.extend(codings)

        for coding in type_codings:
            code = coding.get('code', '').lower()
            if 'imp' in code or 'inpatient' in code:
                record_type = RecordType.INPATIENT
                break
            elif 'emerg' in code or 'emergency' in code:
                record_type = RecordType.EMERGENCY
                break

        # Extract other fields
        period = encounter.get('period', {})
        visit_date = datetime.fromisoformat(
            period.get('start', datetime.now().isoformat())
        ) if period.get('start') else datetime.now()

        participant = encounter.get('participant', [])
        doctor = participant[0].get('individual', {}).get('display', '') if participant else ''

        service_type = encounter.get('serviceType', {})
        department = service_type.get('coding', [{}])[0].get('display', '') if service_type else ''

        # Get diagnosis from Condition resources
        diagnosis_texts = encounter.get('diagnosis', [])
        diagnoses = []
        for diag in diagnosis_texts:
            condition_ref = diag.get('condition', {}).get('reference', '')
            if condition_ref:
                # Try to get the actual condition
                parts = condition_ref.split('/')
                if len(parts) == 2 and parts[0] == 'Condition':
                    condition = self._read_fhir_resource('Condition', parts[1])
                    if condition:
                        code = condition.get('code', {})
                        coding = code.get('coding', [{}])[0]
                        diagnoses.append(coding.get('display', ''))

        return PatientRecord(
            patient_id=patient_id,
            name='',  # Would need to fetch Patient resource
            age=0,
            gender='',
            record_type=record_type,
            visit_date=visit_date,
            department=department,
            doctor=doctor,
            chief_complaint='',
            diagnosis=diagnoses,
            treatments=[],
            medications=[],
            lab_results=[],
            notes=encounter.get('text', {}).get('div', '') or ''
        )

    def _fhir_appointment_to_appointment(self, apt: Dict) -> Optional[Appointment]:
        """Convert FHIR Appointment to Appointment object."""
        try:
            apt_id = apt.get('id', '')

            # Get patient reference
            participants = apt.get('participant', [])
            patient_id = ''
            for p in participants:
                actor = p.get('actor', {})
                ref = actor.get('reference', '')
                if ref.startswith('Patient/'):
                    patient_id = ref.split('/')[-1]
                    break

            start_str = apt.get('start', '')
            appointment_time = datetime.fromisoformat(start_str.replace('Z', '+00:00')) if start_str else datetime.now()

            status = apt.get('status', 'unknown')

            purpose = apt.get('description', '')

            # Try to get department/doctor from comments or participants
            department = ''
            doctor = ''
            for p in participants:
                actor = p.get('actor', {})
                ref = actor.get('reference', '')
                display = actor.get('display', '')
                if ref.startswith('Practitioner/'):
                    doctor = display
                elif ref.startswith('Location/'):
                    department = display

            return Appointment(
                appointment_id=apt_id,
                patient_id=patient_id,
                department=department,
                doctor=doctor,
                appointment_time=appointment_time,
                status=status,
                purpose=purpose
            )

        except Exception as e:
            self.logger.error(f"Error converting appointment: {e}")
            return None
