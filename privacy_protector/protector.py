"""
Privacy Protector - Main API for PII detection and anonymization
"""

import json
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass, field
from pathlib import Path

from .detectors import RegexDetector, PIIMatch, PIIType
from .generators import FakeDataGenerator
from .guards import LLMGuard, get_guard


@dataclass
class ProtectorConfig:
    """Configuration for PrivacyProtector."""
    # Detection
    enabled_types: Optional[List[PIIType]] = None
    use_llm_guard: bool = False
    guard_provider: str = "regex"
    guard_kwargs: Dict[str, Any] = field(default_factory=dict)

    # Generation
    locale: str = "en_US"
    consistent_replacements: bool = True
    seed: Optional[int] = None

    # Output
    generate_report: bool = True
    preserve_format: bool = True


@dataclass
class AnonymizationResult:
    """Result of an anonymization operation."""
    original_text: str
    anonymized_text: str
    replacements: List[Dict[str, Any]]
    pii_found: int
    processing_time_ms: float = 0.0


@dataclass
class ReportEntry:
    """A single entry in the anonymization report."""
    pii_type: str
    original: str
    replacement: str
    position: int
    confidence: float


class PrivacyProtector:
    """
    Main class for detecting and anonymizing PII in text.

    Combines regex-based detection with optional LLM guards for
    comprehensive PII detection and realistic fake data generation.
    """

    def __init__(
        self,
        config: Optional[ProtectorConfig] = None,
        guard_provider: str = "regex",
        locale: str = "en_US",
        consistent: bool = True,
        **guard_kwargs
    ):
        """
        Initialize the Privacy Protector.

        Args:
            config: Full configuration object
            guard_provider: LLM guard provider ('regex', 'openai', 'presidio', 'bedrock', 'llama')
            locale: Faker locale for generating fake data
            consistent: If True, same input always produces same output
            **guard_kwargs: Additional arguments for the guard provider
        """
        self.config = config or ProtectorConfig(
            guard_provider=guard_provider,
            locale=locale,
            consistent_replacements=consistent,
            guard_kwargs=guard_kwargs,
            use_llm_guard=(guard_provider != "regex")
        )

        # Initialize components
        self.regex_detector = RegexDetector(self.config.enabled_types)
        self.generator = FakeDataGenerator(
            locale=self.config.locale,
            consistent=self.config.consistent_replacements,
            seed=self.config.seed
        )

        # Initialize LLM guard if needed
        self.llm_guard: Optional[LLMGuard] = None
        if self.config.use_llm_guard:
            self.llm_guard = get_guard(
                self.config.guard_provider,
                **self.config.guard_kwargs
            )

    def anonymize(self, text: str) -> str:
        """
        Anonymize text by replacing all detected PII with fake data.

        Args:
            text: Input text containing PII

        Returns:
            Anonymized text
        """
        result = self.anonymize_with_report(text)
        return result.anonymized_text

    def anonymize_with_report(self, text: str) -> AnonymizationResult:
        """
        Anonymize text and return detailed report.

        Args:
            text: Input text containing PII

        Returns:
            AnonymizationResult with anonymized text and replacement details
        """
        import time
        start_time = time.time()

        # Detect PII
        matches = self._detect_all(text)

        # Sort by position (reverse) to replace from end to start
        matches.sort(key=lambda m: m.start, reverse=True)

        # Replace each match
        result_text = text
        replacements = []

        for match in matches:
            fake_value = self.generator.generate(match.pii_type, match.value)
            result_text = (
                result_text[:match.start] +
                fake_value +
                result_text[match.end:]
            )
            replacements.append({
                "type": match.pii_type.value,
                "original": match.value,
                "replacement": fake_value,
                "position": match.start,
                "confidence": match.confidence
            })

        processing_time = (time.time() - start_time) * 1000

        return AnonymizationResult(
            original_text=text,
            anonymized_text=result_text,
            replacements=list(reversed(replacements)),  # Restore original order
            pii_found=len(matches),
            processing_time_ms=processing_time
        )

    def detect(self, text: str) -> List[PIIMatch]:
        """
        Detect PII without anonymizing.

        Args:
            text: Input text to scan

        Returns:
            List of detected PII matches
        """
        return self._detect_all(text)

    def _detect_all(self, text: str) -> List[PIIMatch]:
        """Combine regex and LLM guard detection."""
        # Always run regex detection
        matches = self.regex_detector.detect(text)

        # Add LLM guard matches if enabled
        if self.llm_guard:
            guard_result = self.llm_guard.detect(text)
            # Merge matches, avoiding duplicates
            existing_spans = {(m.start, m.end) for m in matches}
            for guard_match in guard_result.matches:
                if (guard_match.start, guard_match.end) not in existing_spans:
                    matches.append(guard_match)

        return matches

    def process_file(
        self,
        input_file: Union[str, Path],
        output_file: Optional[Union[str, Path]] = None
    ) -> AnonymizationResult:
        """
        Process a file and anonymize its contents.

        Args:
            input_file: Path to input file
            output_file: Path to output file (optional)

        Returns:
            AnonymizationResult
        """
        input_path = Path(input_file)

        with open(input_path, 'r', encoding='utf-8') as f:
            text = f.read()

        result = self.anonymize_with_report(text)

        if output_file:
            output_path = Path(output_file)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result.anonymized_text)

        return result

    def process_batch(
        self,
        texts: List[str]
    ) -> List[AnonymizationResult]:
        """
        Process multiple texts.

        Args:
            texts: List of texts to anonymize

        Returns:
            List of AnonymizationResult objects
        """
        return [self.anonymize_with_report(text) for text in texts]

    def add_custom_pattern(
        self,
        name: str,
        pattern: str,
        confidence: float = 0.80
    ):
        """
        Add a custom detection pattern.

        Args:
            name: Pattern identifier
            pattern: Regex pattern
            confidence: Detection confidence (0.0-1.0)
        """
        self.regex_detector.add_custom_pattern(name, pattern, confidence)

    def generate_report(
        self,
        result: AnonymizationResult,
        output_file: Optional[Union[str, Path]] = None,
        format: str = "json"
    ) -> str:
        """
        Generate a detailed report of anonymization.

        Args:
            result: AnonymizationResult to report on
            output_file: Optional file to save report
            format: Report format ('json', 'text')

        Returns:
            Report as string
        """
        if format == "json":
            report = {
                "summary": {
                    "pii_found": result.pii_found,
                    "processing_time_ms": result.processing_time_ms
                },
                "replacements": result.replacements
            }
            report_str = json.dumps(report, indent=2, ensure_ascii=False)
        else:
            lines = [
                "Privacy Protection Report",
                "=" * 40,
                f"PII Found: {result.pii_found}",
                f"Processing Time: {result.processing_time_ms:.2f}ms",
                "",
                "Replacements:",
                "-" * 40
            ]
            for r in result.replacements:
                lines.append(f"  [{r['type']}] {r['original']} -> {r['replacement']}")
            report_str = "\n".join(lines)

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_str)

        return report_str
