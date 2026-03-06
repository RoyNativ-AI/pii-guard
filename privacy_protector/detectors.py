"""
PII Detectors - Regex-based detection for common sensitive data patterns
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class PIIType(str, Enum):
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    IP_ADDRESS = "ip_address"
    DATE = "date"
    ADDRESS = "address"
    PASSPORT = "passport"
    DRIVER_LICENSE = "driver_license"
    BANK_ACCOUNT = "bank_account"
    NAME = "name"  # Detected by LLM only
    CUSTOM = "custom"


@dataclass
class PIIMatch:
    """Represents a detected PII match."""
    pii_type: PIIType
    value: str
    start: int
    end: int
    confidence: float = 1.0


class RegexDetector:
    """
    Regex-based PII detector for common patterns.
    Fast and reliable for structured data like emails, phones, SSN, etc.
    """

    PATTERNS: Dict[PIIType, List[Tuple[str, float]]] = {
        PIIType.EMAIL: [
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 0.99),
        ],
        PIIType.PHONE: [
            # US formats
            (r'\b\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b', 0.95),
            # International
            (r'\b\+[1-9]\d{1,14}\b', 0.90),
            # Israeli format
            (r'\b0[2-9]\d{7,8}\b', 0.90),
            (r'\b\+972[-.\s]?[0-9]{1,2}[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b', 0.95),
        ],
        PIIType.SSN: [
            # US SSN
            (r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b', 0.95),
        ],
        PIIType.CREDIT_CARD: [
            # Visa
            (r'\b4[0-9]{3}[-\s]?[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{4}\b', 0.98),
            # Mastercard
            (r'\b5[1-5][0-9]{2}[-\s]?[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{4}\b', 0.98),
            # Amex
            (r'\b3[47][0-9]{2}[-\s]?[0-9]{6}[-\s]?[0-9]{5}\b', 0.98),
            # Generic 16 digits
            (r'\b[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{4}\b', 0.85),
        ],
        PIIType.IP_ADDRESS: [
            # IPv4
            (r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b', 0.99),
            # IPv6 (simplified)
            (r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b', 0.99),
        ],
        PIIType.DATE: [
            # ISO format
            (r'\b\d{4}[-/]\d{2}[-/]\d{2}\b', 0.90),
            # US format
            (r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b', 0.85),
            # Written format
            (r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}\b', 0.90),
        ],
        PIIType.PASSPORT: [
            # US Passport
            (r'\b[A-Z]{1,2}[0-9]{6,9}\b', 0.70),
        ],
        PIIType.DRIVER_LICENSE: [
            # Generic pattern (varies by state/country)
            (r'\b[A-Z]{1,2}[0-9]{5,8}\b', 0.60),
        ],
        PIIType.BANK_ACCOUNT: [
            # IBAN
            (r'\b[A-Z]{2}[0-9]{2}[A-Z0-9]{4}[0-9]{7}([A-Z0-9]?){0,16}\b', 0.95),
            # Generic account number
            (r'\b[0-9]{8,17}\b', 0.50),
        ],
    }

    def __init__(self, enabled_types: Optional[List[PIIType]] = None):
        """
        Initialize detector with optional type filtering.

        Args:
            enabled_types: List of PII types to detect. None means all.
        """
        self.enabled_types = enabled_types or list(self.PATTERNS.keys())
        self._compiled_patterns: Dict[PIIType, List[Tuple[re.Pattern, float]]] = {}
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns for performance."""
        for pii_type in self.enabled_types:
            if pii_type in self.PATTERNS:
                self._compiled_patterns[pii_type] = [
                    (re.compile(pattern, re.IGNORECASE), confidence)
                    for pattern, confidence in self.PATTERNS[pii_type]
                ]

    def detect(self, text: str) -> List[PIIMatch]:
        """
        Detect PII in text using regex patterns.

        Args:
            text: Input text to scan

        Returns:
            List of PIIMatch objects
        """
        matches = []
        seen_spans = set()

        for pii_type, patterns in self._compiled_patterns.items():
            for pattern, confidence in patterns:
                for match in pattern.finditer(text):
                    span = (match.start(), match.end())
                    # Avoid overlapping matches
                    if not any(self._spans_overlap(span, seen) for seen in seen_spans):
                        matches.append(PIIMatch(
                            pii_type=pii_type,
                            value=match.group(),
                            start=match.start(),
                            end=match.end(),
                            confidence=confidence
                        ))
                        seen_spans.add(span)

        # Sort by position
        matches.sort(key=lambda m: m.start)
        return matches

    @staticmethod
    def _spans_overlap(span1: Tuple[int, int], span2: Tuple[int, int]) -> bool:
        """Check if two spans overlap."""
        return not (span1[1] <= span2[0] or span2[1] <= span1[0])

    def add_custom_pattern(self, name: str, pattern: str, confidence: float = 0.80):
        """
        Add a custom detection pattern.

        Args:
            name: Pattern identifier
            pattern: Regex pattern string
            confidence: Confidence score (0.0-1.0)
        """
        if PIIType.CUSTOM not in self._compiled_patterns:
            self._compiled_patterns[PIIType.CUSTOM] = []

        self._compiled_patterns[PIIType.CUSTOM].append(
            (re.compile(pattern), confidence)
        )
