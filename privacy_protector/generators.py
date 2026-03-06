"""
Fake Data Generators - Generate realistic replacement data using Faker
"""

import hashlib
from typing import Dict, Optional, Any
from faker import Faker

from .detectors import PIIType


class FakeDataGenerator:
    """
    Generate realistic fake data to replace detected PII.
    Uses Faker library for high-quality fake data.
    """

    def __init__(
        self,
        locale: str = "en_US",
        consistent: bool = True,
        seed: Optional[int] = None
    ):
        """
        Initialize the generator.

        Args:
            locale: Faker locale for localized data (e.g., 'en_US', 'he_IL', 'de_DE')
            consistent: If True, same input always generates same output
            seed: Random seed for reproducibility
        """
        self.faker = Faker(locale)
        self.consistent = consistent
        self._cache: Dict[str, str] = {}

        if seed:
            Faker.seed(seed)

    def generate(self, pii_type: PIIType, original: str) -> str:
        """
        Generate fake data to replace the original PII.

        Args:
            pii_type: Type of PII detected
            original: Original PII value

        Returns:
            Fake replacement data
        """
        if self.consistent and original in self._cache:
            return self._cache[original]

        # Set seed based on original value for consistency
        if self.consistent:
            seed = int(hashlib.md5(original.encode()).hexdigest()[:8], 16)
            self.faker.seed_instance(seed)

        fake_value = self._generate_by_type(pii_type, original)

        if self.consistent:
            self._cache[original] = fake_value

        return fake_value

    def _generate_by_type(self, pii_type: PIIType, original: str) -> str:
        """Generate fake data based on PII type."""
        generators = {
            PIIType.EMAIL: self._generate_email,
            PIIType.PHONE: self._generate_phone,
            PIIType.SSN: self._generate_ssn,
            PIIType.CREDIT_CARD: self._generate_credit_card,
            PIIType.IP_ADDRESS: self._generate_ip,
            PIIType.DATE: self._generate_date,
            PIIType.ADDRESS: self._generate_address,
            PIIType.PASSPORT: self._generate_passport,
            PIIType.DRIVER_LICENSE: self._generate_driver_license,
            PIIType.BANK_ACCOUNT: self._generate_bank_account,
            PIIType.NAME: self._generate_name,
        }

        generator = generators.get(pii_type, self._generate_generic)
        return generator(original)

    def _generate_email(self, original: str) -> str:
        """Generate fake email preserving domain structure."""
        return self.faker.email()

    def _generate_phone(self, original: str) -> str:
        """Generate fake phone number preserving format."""
        # Detect format and preserve it
        if original.startswith('+972'):
            return f"+972-{self.faker.random_int(50, 59)}-{self.faker.random_int(100, 999)}-{self.faker.random_int(1000, 9999)}"
        elif original.startswith('+1') or original.startswith('1'):
            return self.faker.phone_number()
        elif '(' in original:
            area = self.faker.random_int(200, 999)
            return f"({area}) {self.faker.random_int(100, 999)}-{self.faker.random_int(1000, 9999)}"
        else:
            return self.faker.phone_number()

    def _generate_ssn(self, original: str) -> str:
        """Generate fake SSN preserving format."""
        ssn = self.faker.ssn()
        # Preserve original format (with or without dashes)
        if '-' not in original:
            ssn = ssn.replace('-', '')
        return ssn

    def _generate_credit_card(self, original: str) -> str:
        """Generate fake credit card preserving format."""
        cc = self.faker.credit_card_number()
        # Match original separator
        if '-' in original:
            return '-'.join([cc[i:i+4] for i in range(0, 16, 4)])
        elif ' ' in original:
            return ' '.join([cc[i:i+4] for i in range(0, 16, 4)])
        return cc

    def _generate_ip(self, original: str) -> str:
        """Generate fake IP address."""
        if ':' in original:  # IPv6
            return self.faker.ipv6()
        return self.faker.ipv4()

    def _generate_date(self, original: str) -> str:
        """Generate fake date preserving format."""
        fake_date = self.faker.date_object()

        # Detect format
        if '/' in original:
            if original.index('/') < 3:  # MM/DD/YYYY
                return fake_date.strftime('%m/%d/%Y')
            return fake_date.strftime('%Y/%m/%d')
        elif '-' in original:
            return fake_date.strftime('%Y-%m-%d')
        else:
            return fake_date.strftime('%B %d, %Y')

    def _generate_address(self, original: str) -> str:
        """Generate fake address."""
        return self.faker.address().replace('\n', ', ')

    def _generate_passport(self, original: str) -> str:
        """Generate fake passport number."""
        prefix = ''.join(c for c in original if c.isalpha())
        num_digits = len([c for c in original if c.isdigit()])
        return f"{prefix}{self.faker.random_int(10**(num_digits-1), 10**num_digits - 1)}"

    def _generate_driver_license(self, original: str) -> str:
        """Generate fake driver license."""
        return self._generate_passport(original)  # Similar format

    def _generate_bank_account(self, original: str) -> str:
        """Generate fake bank account number."""
        if original[:2].isalpha():  # IBAN
            return self.faker.iban()
        return ''.join(str(self.faker.random_digit()) for _ in range(len(original)))

    def _generate_name(self, original: str) -> str:
        """Generate fake name."""
        # Try to preserve structure (first only, first last, full)
        parts = original.split()
        if len(parts) == 1:
            return self.faker.first_name()
        elif len(parts) == 2:
            return self.faker.name()
        else:
            return f"{self.faker.first_name()} {self.faker.last_name()}"

    def _generate_generic(self, original: str) -> str:
        """Generate generic replacement."""
        return f"[REDACTED-{self.faker.random_int(1000, 9999)}]"

    def clear_cache(self):
        """Clear the consistency cache."""
        self._cache.clear()
