"""
OpenFDA Drug Database Interface Implementation

This module provides a real implementation of the drug database interface
using the OpenFDA API (https://api.fda.gov).

OpenFDA is a public API that provides access to FDA drug, device, and food data.
"""

from typing import Dict, List, Any, Optional
from urllib.parse import quote

from medical_task_suite.tool_interfaces.real.base_real_interface import BaseRealInterface
from medical_task_suite.tool_interfaces.drug_database_interface import (
    DrugDatabaseInterface,
    DrugInfo,
    DrugCategory,
    DrugInteraction,
    DrugAlternatives
)
from medical_task_suite.utils.logger import get_logger


class RealDrugDatabase(DrugDatabaseInterface):
    """
    Real drug database interface implementation using OpenFDA.

    This class connects to the OpenFDA API and provides real drug information,
    including indications, contraindications, interactions, and dosage guidelines.

    It maintains compatibility with the stub DrugDatabaseInterface API.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the real drug database interface.

        Args:
            config: Configuration dictionary with OpenFDA settings
        """
        # Initialize base interface
        super().__init__(database_id="OpenFDA")

        # OpenFDA-specific settings
        self.base_url = config.get('base_url', 'https://api.fda.gov')
        self.drug_label_endpoint = config.get(
            'drug_label_endpoint',
            '/drug/label.json'
        )
        self.drug_event_endpoint = config.get(
            'drug_event_endpoint',
            '/drug/event.json'
        )
        self.api_key = config.get('api_key')

        # Use base class components
        from medical_task_suite.utils.cache_manager import CacheManager
        from medical_task_suite.utils.rate_limiter import RateLimiter

        cache_config = config.get('cache', {})
        if cache_config.get('enabled', True):
            self.cache = CacheManager(
                ttl=config.get('cache_ttl', 3600),
                max_size=cache_config.get('max_size', 1000)
            )
        else:
            self.cache = None

        # Initialize rate limiter (OpenFDA has rate limits)
        rate_limit = config.get('rate_limit', 240)
        self.rate_limiter = RateLimiter(max_calls=rate_limit, period=60.0)

        # Override logger
        self.logger = get_logger(self.__class__.__name__)

        # Initialize session
        import requests
        self.session = requests.Session()
        self.timeout = config.get('timeout', 30)

        # Connection state
        self.is_connected = False

    def connect(self) -> bool:
        """
        Connect to the OpenFDA API and verify it's accessible.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Test connection by searching for a common drug
            url = f"{self.base_url}{self.drug_label_endpoint}"
            params = {
                'search': 'openfda.brand_name:aspirin',
                'limit': 1
            }

            if self.api_key:
                params['api_key'] = self.api_key

            response = self.session.get(url, params=params, timeout=self.timeout)

            if response.status_code == 200:
                self.is_connected = True
                self.logger.info(f"Connected to OpenFDA: {self.base_url}")
                return True
            else:
                self.logger.error(f"Failed to connect: HTTP {response.status_code}")
                return False

        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            return False

    def disconnect(self):
        """Disconnect from the OpenFDA API."""
        self.is_connected = False
        if self.session:
            self.session.close()
        self.logger.info("Disconnected from OpenFDA")

    def _query_openfda(
        self,
        endpoint: str,
        search_params: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Query the OpenFDA API.

        Args:
            endpoint: API endpoint to query
            search_params: Search query string
            limit: Maximum number of results

        Returns:
            List of results
        """
        if not self.is_connected:
            raise RuntimeError("Not connected to OpenFDA")

        url = f"{self.base_url}{endpoint}"
        params = {'limit': limit}

        if search_params:
            params['search'] = search_params

        if self.api_key:
            params['api_key'] = self.api_key

        # Check cache first
        if self.cache:
            import hashlib
            cache_key = f"openfda:{endpoint}:{search_params}:{limit}"
            cache_key = hashlib.md5(cache_key.encode()).hexdigest()

            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        # Rate limiting
        if self.rate_limiter:
            wait_time = self.rate_limiter.get_wait_time()
            if wait_time > 0:
                self.logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
                import time
                time.sleep(wait_time)

            self.rate_limiter.acquire()

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            results = data.get('results', [])

            # Cache the results
            if self.cache and results:
                self.cache.set(results, cache_key)

            return results

        except Exception as e:
            self.logger.error(f"Error querying OpenFDA: {e}")
            return []

    def get_drug_info(self, drug_name: str) -> Optional[DrugInfo]:
        """
        Get comprehensive information about a drug.

        Args:
            drug_name: Generic or brand name of the drug

        Returns:
            DrugInfo object if found, None otherwise
        """
        # Search by brand name or generic name
        search_query = f"openfda.brand_name:{drug_name.lower()}+OR+openfda.generic_name:{drug_name.lower()}"

        results = self._query_openfda(self.drug_label_endpoint, search_query, limit=1)

        if not results:
            return None

        result = results[0]

        # Extract drug information
        openfda = result.get('openfda', {})

        generic_name = (openfda.get('generic_name', [''])[0]
                       if openfda.get('generic_name') else '')
        brand_names = openfda.get('brand_name', [])
        manufacturer = openfda.get('manufacturer_name', [''])[0] if openfda.get('manufacturer_name') else ''

        # Extract indications
        indications = self._extract_indications(result)

        # Extract contraindications
        contraindications = self._extract_contraindications(result)

        # Extract dosage forms
        dosage_forms = openfda.get('dosage_form', [])

        # Extract side effects
        adverse_reactions = result.get('adverse_reactions', [])
        side_effects = self._extract_side_effects(adverse_reactions)

        # Extract pregnancy category
        pregnancy_category = self._extract_pregnancy_category(result)

        # Determine category
        category = self._determine_drug_category(result)

        # Build dosage info
        standard_dosage = self._extract_dosage_info(result)

        # Build interactions list
        interactions = self._extract_interactions(result)

        # Storage conditions
        storage = result.get('storage', [''])[0] if result.get('storage') else ''

        return DrugInfo(
            generic_name=generic_name,
            brand_names=brand_names,
            category=category,
            indications=indications,
            contraindications=contraindications,
            dosage_forms=dosage_forms,
            standard_dosage=standard_dosage,
            side_effects=side_effects,
            interactions=interactions,
            pregnancy_category=pregnancy_category,
            storage_conditions=storage
        )

    def search_drugs(
        self,
        query: str,
        search_type: str = "name"
    ) -> List[Dict[str, str]]:
        """
        Search for drugs by name or indication.

        Args:
            query: Search query
            search_type: Type of search ('name', 'indication', 'category')

        Returns:
            List of matching drugs with basic info
        """
        if search_type == "name":
            search_query = f"openfda.brand_name:{query.lower()}*+OR+openfda.generic_name:{query.lower()}*"
        elif search_type == "indication":
            search_query = f"indications_and_usage:{query}"
        else:
            search_query = query

        results = self._query_openfda(self.drug_label_endpoint, search_query, limit=20)

        drugs = []
        for result in results:
            openfda = result.get('openfda', {})

            drug = {
                'generic_name': (openfda.get('generic_name', [''])[0]
                               if openfda.get('generic_name') else ''),
                'brand_names': openfda.get('brand_name', []),
                'manufacturer': (openfda.get('manufacturer_name', [''])[0]
                               if openfda.get('manufacturer_name') else ''),
                'dosage_forms': openfda.get('dosage_form', [])
            }
            drugs.append(drug)

        return drugs

    def check_interactions(self, drugs: List[str]) -> List[DrugInteraction]:
        """
        Check for drug interactions among a list of drugs.

        Args:
            drugs: List of drug names

        Returns:
            List of DrugInteraction objects
        """
        interactions = []

        # Query each drug's interaction information
        for i, drug1 in enumerate(drugs):
            for drug2 in drugs[i+1:]:
                # Search for interactions between drug1 and drug2
                search_query = f"openfda.brand_name:{drug1.lower()}+openfda.brand_name:{drug2.lower()}"

                results = self._query_openfda(
                    self.drug_label_endpoint,
                    search_query,
                    limit=1
                )

                if results:
                    result = results[0]

                    # Extract drug interactions section
                    drug_interactions = result.get('drug_interactions', [])

                    if drug_interactions:
                        # Determine severity (simplified heuristic)
                        severity = 'moderate'

                        interaction_text = ' '.join(drug_interactions[:2])  # First few paragraphs

                        # Check for severity keywords
                        if any(word in interaction_text.lower() for word in
                               ['contraindicated', 'life-threatening', 'fatal']):
                            severity = 'major'
                        elif any(word in interaction_text.lower() for word in
                                ['minor', 'not significant']):
                            severity = 'minor'

                        interaction = DrugInteraction(
                            drug1=drug1,
                            drug2=drug2,
                            severity=severity,
                            description=interaction_text[:500],  # Truncate if too long
                            management=self._extract_management(interaction_text)
                        )

                        interactions.append(interaction)

        return interactions

    def check_allergy(
        self,
        drug_name: str,
        patient_allergies: List[str]
    ) -> Dict[str, Any]:
        """
        Check if a drug interacts with patient allergies.

        Args:
            drug_name: Drug name
            patient_allergies: List of patient allergies

        Returns:
            Dictionary with allergy check results
        """
        # Get drug information
        drug_info = self.get_drug_info(drug_name)

        if not drug_info:
            return {
                'has_allergy': False,
                'severity': None,
                'description': None
            }

        # Check for allergen matches
        # This is a simplified check - in reality would need more sophisticated matching
        allergens = []

        # Check against known drug classes
        active_ingredients = drug_info.generic_name.lower()

        for allergy in patient_allergies:
            allergy_lower = allergy.lower()

            # Direct match
            if allergy_lower in active_ingredients:
                allergens.append({
                    'allergen': allergy,
                    'severity': 'high',
                    'description': f"{drug_name} contains {allergy}"
                })

        if allergens:
            return {
                'has_allergy': True,
                'severity': 'high' if any(a['severity'] == 'high' for a in allergens) else 'moderate',
                'description': f"Potential allergen found in {drug_name}",
                'allergens': allergens
            }

        return {
            'has_allergy': False,
            'severity': None,
            'description': None
        }

    def check_contraindications(
        self,
        drug_name: str,
        patient_conditions: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Check if a drug is contraindicated for patient conditions.

        Args:
            drug_name: Drug name
            patient_conditions: List of patient medical conditions

        Returns:
            List of contraindications
        """
        # Get drug information
        drug_info = self.get_drug_info(drug_name)

        if not drug_info:
            return []

        contraindications = []

        # Check each patient condition
        for condition in patient_conditions:
            condition_lower = condition.lower()

            # Check if condition appears in drug contraindications
            for contra in drug_info.contraindications:
                if condition_lower in contra.lower():
                    contraindications.append({
                        'condition': condition,
                        'contraindication': contra,
                        'severity': 'major'
                    })

        return contraindications

    def get_dosage_info(
        self,
        drug_name: str,
        patient_age: int,
        patient_weight: float,
        condition: str
    ) -> Dict[str, Any]:
        """
        Get dosage information for a specific patient.

        Args:
            drug_name: Drug name
            patient_age: Patient age in years
            patient_weight: Patient weight in kg
            condition: Medical condition being treated

        Returns:
            Dictionary with dosage recommendations
        """
        # Get drug label
        search_query = f"openfda.brand_name:{drug_name.lower()}+OR+openfda.generic_name:{drug_name.lower()}"

        results = self._query_openfda(self.drug_label_endpoint, search_query, limit=1)

        if not results:
            return {
                'standard_dosage': '',
                'min_dosage': '',
                'max_dosage': '',
                'frequency': '',
                'duration': '',
                'special_instructions': []
            }

        result = results[0]

        # Extract dosage information
        dosage_info = self._extract_dosage_info(result)

        # Extract frequency
        frequency = self._extract_frequency(result)

        # Extract duration
        duration = self._extract_duration(result)

        # Extract special instructions
        special_instructions = []
        if 'warnings_and_cautions' in result:
            special_instructions.extend(result['warnings_and_cautions'][:3])

        return {
            'standard_dosage': dosage_info.get('adult', ''),
            'min_dosage': dosage_info.get('minimum', ''),
            'max_dosage': dosage_info.get('maximum', ''),
            'frequency': frequency,
            'duration': duration,
            'special_instructions': special_instructions
        }

    def find_alternatives(
        self,
        drug_name: str,
        reason: str = "availability"
    ) -> Optional[DrugAlternatives]:
        """
        Find alternative drugs.

        Args:
            drug_name: Original drug name
            reason: Reason for finding alternatives

        Returns:
            DrugAlternatives object if alternatives found
        """
        # Get original drug info to find therapeutic class
        original_info = self.get_drug_info(drug_name)

        if not original_info:
            return None

        # Find drugs with similar indications
        alternatives = []

        if original_info.indications:
            # Search for drugs with similar indications
            indication = original_info.indications[0].split(' ')[0]  # First word

            similar_drugs = self.search_drugs(indication, search_type="indication")

            # Limit results and filter out original drug
            for drug in similar_drugs[:10]:
                if (drug['generic_name'].lower() != drug_name.lower() and
                    drug_name.lower() not in str(drug['brand_names']).lower()):
                    alternatives.append({
                        'generic_name': drug['generic_name'],
                        'brand_names': drug['brand_names'],
                        'reason': 'similar_indication'
                    })

        if alternatives:
            return DrugAlternatives(
                original_drug=drug_name,
                alternatives=alternatives,
                reason=reason
            )

        return None

    def get_side_effects(self, drug_name: str) -> Dict[str, List[str]]:
        """
        Get side effects for a drug.

        Args:
            drug_name: Drug name

        Returns:
            Dictionary with categorized side effects
        """
        # Get drug information
        drug_info = self.get_drug_info(drug_name)

        if not drug_info:
            return {
                'common': [],
                'uncommon': [],
                'rare': [],
                'serious': []
            }

        # Categorize side effects by severity
        # This is a simplified categorization
        common = []
        uncommon = []
        rare = []
        serious = []

        for effect in drug_info.side_effects:
            effect_lower = effect.lower()

            # Check for serious keywords
            if any(word in effect_lower for word in
                   ['fatal', 'life-threatening', 'severe', 'serious']):
                serious.append(effect)

            # Check for rare keywords
            elif any(word in effect_lower for word in ['rare', 'infrequently']):
                rare.append(effect)

            # Check for common keywords
            elif any(word in effect_lower for word in ['common', 'frequently']):
                common.append(effect)

            else:
                uncommon.append(effect)

        return {
            'common': list(set(common)),
            'uncommon': list(set(uncommon)),
            'rare': list(set(rare)),
            'serious': list(set(serious))
        }

    def check_pregnancy_safety(self, drug_name: str) -> Dict[str, str]:
        """
        Check pregnancy safety category.

        Args:
            drug_name: Drug name

        Returns:
            Dictionary with pregnancy category and description
        """
        # Get drug information
        drug_info = self.get_drug_info(drug_name)

        if not drug_info:
            return {
                'category': '',
                'description': '',
                'recommendation': ''
            }

        category = drug_info.pregnancy_category

        # Generate recommendation based on category
        recommendations = {
            'A': 'Adequate and well-controlled studies have failed to demonstrate a risk to the fetus.',
            'B': 'Animal reproduction studies have failed to demonstrate a risk to the fetus and there are no adequate and well-controlled studies in pregnant women.',
            'C': 'Animal reproduction studies have shown an adverse effect on the fetus and there are no adequate and well-controlled studies in humans, but potential benefits may warrant use of the drug in pregnant women despite potential risks.',
            'D': 'There is positive evidence of human fetal risk based on adverse reaction data from investigational or marketing experience or studies in humans, but potential benefits may warrant use of the drug in pregnant women despite potential risks.',
            'X': 'Studies in animals or humans have demonstrated fetal abnormalities and/or there is positive evidence of human fetal risk based on adverse reaction data from investigational or marketing experience, and the risks involved in use of the drug in pregnant women clearly outweigh potential benefits.',
            'N': 'FDA has not classified the drug.'
        }

        description = recommendations.get(category, '')

        return {
            'category': category,
            'description': description,
            'recommendation': self._generate_pregnancy_recommendation(category)
        }

    def verify_drug_name(self, user_input: str) -> List[Dict[str, str]]:
        """
        Verify and correct drug name input.

        Args:
            user_input: User's drug name input

        Returns:
            List of possible matches with confidence scores
        """
        # Search for similar drug names
        search_query = f"openfda.brand_name:{user_input.lower()}*+OR+openfda.generic_name:{user_input.lower()}*"

        results = self._query_openfda(self.drug_label_endpoint, search_query, limit=5)

        matches = []
        for result in results:
            openfda = result.get('openfda', {})

            brand_names = openfda.get('brand_name', [])
            generic_names = openfda.get('generic_name', [])

            # Calculate confidence score based on similarity
            for name in brand_names + generic_names:
                similarity = self._calculate_similarity(user_input, name)

                if similarity > 0.3:  # Threshold for similarity
                    matches.append({
                        'name': name,
                        'confidence': f'{similarity:.2f}',
                        'type': 'brand' if name in brand_names else 'generic'
                    })

        # Sort by confidence
        matches.sort(key=lambda x: float(x['confidence']), reverse=True)

        return matches[:5]

    def get_drug_price(
        self,
        drug_name: str,
        dosage: str,
        quantity: int
    ) -> Dict[str, Any]:
        """
        Get drug pricing information.

        Note: OpenFDA does not provide pricing information.
        This returns a placeholder response.

        Args:
            drug_name: Drug name
            dosage: Dosage strength
            quantity: Quantity

        Returns:
            Dictionary with pricing information
        """
        # OpenFDA doesn't provide pricing
        # This would need to be integrated with another service
        return {
            'price': 0.0,
            'insurance_coverage': False,
            'generic_available': False,
            'generic_price': 0.0,
            'note': 'Pricing information not available through OpenFDA'
        }

    def get_formulary_status(
        self,
        drug_name: str,
        insurance_type: str
    ) -> Dict[str, Any]:
        """
        Check if drug is on insurance formulary.

        Note: OpenFDA does not provide formulary information.
        This returns a placeholder response.

        Args:
            drug_name: Drug name
            insurance_type: Type of insurance

        Returns:
            Dictionary with formulary status
        """
        # OpenFDA doesn't provide formulary information
        return {
            'on_formulary': False,
            'tier': None,
            'prior_authorization_required': False,
            'alternatives_on_formulary': [],
            'note': 'Formulary information not available through OpenFDA'
        }

    # Helper methods for extracting data from OpenFDA responses

    def _extract_indications(self, result: Dict) -> List[str]:
        """Extract indications from drug label."""
        indications = result.get('indications_and_usage', [])

        # Clean up and limit
        cleaned = []
        for indication in indications[:3]:  # Limit to first 3
            # Remove HTML tags if present
            import re
            text = re.sub(r'<[^>]+>', '', indication)
            cleaned.append(text.strip())

        return cleaned

    def _extract_contraindications(self, result: Dict) -> List[str]:
        """Extract contraindications from drug label."""
        contraindications = result.get('contraindications', [])

        # Clean up and limit
        cleaned = []
        for contra in contraindications[:5]:  # Limit to first 5
            import re
            text = re.sub(r'<[^>]+>', '', contra)
            if text.strip():
                cleaned.append(text.strip())

        return cleaned

    def _extract_side_effects(self, adverse_reactions: List) -> List[str]:
        """Extract and categorize side effects."""
        effects = []

        for reaction in adverse_reactions[:10]:  # Limit to first 10
            import re
            text = re.sub(r'<[^>]+>', '', reaction)
            if text.strip():
                effects.append(text.strip())

        return effects

    def _extract_pregnancy_category(self, result: Dict) -> str:
        """Extract pregnancy category."""
        # Check pregnancy section
        pregnancy_info = result.get('pregnancy', [])

        for info in pregnancy_info:
            import re
            text = re.sub(r'<[^>]+>', '', info).upper()

            # Look for pregnancy category (A, B, C, D, X)
            match = re.search(r'PREGNANCY CATEGORY\s+([A-X])', text)
            if match:
                return match.group(1)

        return 'N'  # Not classified

    def _determine_drug_category(self, result: Dict) -> DrugCategory:
        """Determine if drug is prescription, OTC, or controlled."""
        openfda = result.get('openfda', {})
        product_types = openfda.get('product_type', [])

        for pt in product_types:
            if 'HUMAN PRESCRIPTION DRUG' in pt.upper():
                return DrugCategory.PRESCRIPTION
            elif 'HUMAN OTC DRUG' in pt.upper():
                return DrugCategory.OTC
            elif 'CONTROLLED' in pt.upper():
                return DrugCategory.CONTROLLED

        return DrugCategory.PRESCRIPTION  # Default

    def _extract_dosage_info(self, result: Dict) -> Dict[str, str]:
        """Extract dosage information."""
        dosage_info = {
            'adult': '',
            'pediatric': '',
            'minimum': '',
            'maximum': ''
        }

        dosages = result.get('dosage_and_administration', [])

        # Extract adult dosage
        for dosage in dosages:
            import re
            text = re.sub(r'<[^>]+>', '', dosage)

            if 'adult' in text.lower():
                dosage_info['adult'] = text[:200]  # Truncate if too long
            elif 'pediatric' in text.lower() or 'children' in text.lower():
                dosage_info['pediatric'] = text[:200]

        return dosage_info

    def _extract_interactions(self, result: Dict) -> List[Dict[str, Any]]:
        """Extract drug interactions."""
        interactions_section = result.get('drug_interactions', [])

        interactions = []

        # Parse interaction text (simplified)
        for interaction_text in interactions_section[:5]:
            interactions.append({
                'description': interaction_text[:500],
                'severity': 'moderate'  # Default severity
            })

        return interactions

    def _extract_frequency(self, result: Dict) -> str:
        """Extract dosing frequency."""
        # Look for frequency in dosage section
        dosages = result.get('dosage_and_administration', [])

        for dosage in dosages:
            import re
            text = re.sub(r'<[^>]+>', '', dosage).lower()

            # Look for frequency keywords
            if 'once daily' in text:
                return 'Once daily'
            elif 'twice daily' in text or 'bid' in text:
                return 'Twice daily'
            elif 'three times daily' in text or 'tid' in text:
                return 'Three times daily'
            elif 'four times daily' in text or 'qid' in text:
                return 'Four times daily'
            elif 'as needed' in text or 'prn' in text:
                return 'As needed'

        return ''

    def _extract_duration(self, result: Dict) -> str:
        """Extract treatment duration."""
        # This would require parsing the dosage section
        # For now, return empty string
        return ''

    def _extract_management(self, interaction_text: str) -> str:
        """Extract management recommendations from interaction text."""
        # Look for management keywords
        management_keywords = ['avoid', 'monitor', 'consider', 'may be used']

        for keyword in management_keywords:
            if keyword in interaction_text.lower():
                return f"{keyword.capitalize()} use"

        return 'Consult healthcare provider'

    def _calculate_similarity(self, input_str: str, match_str: str) -> float:
        """Calculate similarity between two strings."""
        input_lower = input_str.lower()
        match_lower = match_str.lower()

        # Simple similarity: check if input is contained in match or vice versa
        if input_lower in match_lower:
            return 0.9
        elif match_lower in input_lower:
            return 0.8
        else:
            # Calculate word overlap
            input_words = set(input_lower.split())
            match_words = set(match_lower.split())

            if input_words and match_words:
                overlap = len(input_words & match_words)
                total = len(input_words | match_words)
                return overlap / total if total > 0 else 0.0

        return 0.0

    def _generate_pregnancy_recommendation(self, category: str) -> str:
        """Generate pregnancy recommendation based on category."""
        recommendations = {
            'A': 'Generally considered safe to use during pregnancy.',
            'B': 'Generally considered safe, but benefits should outweigh risks.',
            'C': 'Use only if potential benefit justifies potential risk to fetus.',
            'D': 'Contraindicated in pregnancy unless benefits clearly outweigh risks.',
            'X': 'Contraindicated in pregnancy - do not use.',
            'N': 'Pregnancy safety not established - consult healthcare provider.'
        }

        return recommendations.get(category, 'Consult healthcare provider.')
