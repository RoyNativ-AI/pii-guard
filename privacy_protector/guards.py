"""
LLM Guard Providers - AI-powered PII detection for names and unstructured data
Supports: Llama Guard, AWS Bedrock Guardrails, Azure Content Safety, Presidio
"""

import os
import json
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from .detectors import PIIMatch, PIIType


@dataclass
class GuardResult:
    """Result from an LLM Guard check."""
    matches: List[PIIMatch]
    raw_response: Optional[Dict[str, Any]] = None
    model_used: Optional[str] = None


class LLMGuard(ABC):
    """Abstract base class for LLM-based PII detection."""

    @abstractmethod
    def detect(self, text: str) -> GuardResult:
        """Detect PII using LLM."""
        pass


class LlamaGuard(LLMGuard):
    """
    Llama Guard integration for PII detection.
    Uses Ollama or vLLM for local inference.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama-guard3",
    ):
        import httpx
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.client = httpx.Client(timeout=60.0)

    def detect(self, text: str) -> GuardResult:
        """Detect PII using Llama Guard."""
        prompt = self._build_prompt(text)

        response = self.client.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }
        )
        response.raise_for_status()

        result = response.json()
        return self._parse_response(text, result)

    def _build_prompt(self, text: str) -> str:
        return f"""Analyze the following text and identify all personally identifiable information (PII).

For each PII found, return a JSON object with:
- "type": the category (name, email, phone, address, ssn, credit_card, date_of_birth, etc.)
- "value": the exact text that contains PII
- "start": character position where it starts
- "end": character position where it ends

Return a JSON array of all PII found. If no PII found, return an empty array [].

Text to analyze:
{text}

PII found (JSON array):"""

    def _parse_response(self, text: str, response: Dict) -> GuardResult:
        matches = []
        try:
            content = response.get("response", "[]")
            pii_list = json.loads(content)

            for item in pii_list:
                pii_type = self._map_type(item.get("type", ""))
                value = item.get("value", "")

                # Find position in text
                start = text.find(value)
                if start >= 0:
                    matches.append(PIIMatch(
                        pii_type=pii_type,
                        value=value,
                        start=start,
                        end=start + len(value),
                        confidence=0.85
                    ))
        except (json.JSONDecodeError, KeyError):
            pass

        return GuardResult(matches=matches, raw_response=response, model_used=self.model)

    def _map_type(self, type_str: str) -> PIIType:
        """Map LLM type string to PIIType."""
        type_map = {
            "name": PIIType.NAME,
            "email": PIIType.EMAIL,
            "phone": PIIType.PHONE,
            "address": PIIType.ADDRESS,
            "ssn": PIIType.SSN,
            "social_security": PIIType.SSN,
            "credit_card": PIIType.CREDIT_CARD,
            "date": PIIType.DATE,
            "date_of_birth": PIIType.DATE,
            "dob": PIIType.DATE,
            "ip": PIIType.IP_ADDRESS,
            "ip_address": PIIType.IP_ADDRESS,
        }
        return type_map.get(type_str.lower(), PIIType.CUSTOM)


class BedrockGuard(LLMGuard):
    """
    AWS Bedrock Guardrails integration for PII detection.
    Uses Amazon's managed guardrails for enterprise-grade detection.
    """

    def __init__(
        self,
        guardrail_id: str,
        guardrail_version: str = "DRAFT",
        region: str = "us-east-1",
    ):
        import boto3
        self.guardrail_id = guardrail_id
        self.guardrail_version = guardrail_version
        self.client = boto3.client('bedrock-runtime', region_name=region)

    def detect(self, text: str) -> GuardResult:
        """Detect PII using AWS Bedrock Guardrails."""
        response = self.client.apply_guardrail(
            guardrailIdentifier=self.guardrail_id,
            guardrailVersion=self.guardrail_version,
            source='INPUT',
            content=[{'text': {'text': text}}]
        )

        return self._parse_response(text, response)

    def _parse_response(self, text: str, response: Dict) -> GuardResult:
        matches = []

        # Extract PII findings from Bedrock response
        outputs = response.get('outputs', [])
        for output in outputs:
            assessments = output.get('assessments', [])
            for assessment in assessments:
                sensitive_info = assessment.get('sensitiveInformationPolicy', {})
                pii_entities = sensitive_info.get('piiEntities', [])

                for entity in pii_entities:
                    entity_type = entity.get('type', 'UNKNOWN')
                    # Bedrock returns masked text, we need to find original
                    pii_type = self._map_bedrock_type(entity_type)
                    matches.append(PIIMatch(
                        pii_type=pii_type,
                        value=entity.get('match', ''),
                        start=0,
                        end=0,
                        confidence=0.95
                    ))

        return GuardResult(matches=matches, raw_response=response, model_used="bedrock-guardrails")

    def _map_bedrock_type(self, bedrock_type: str) -> PIIType:
        """Map Bedrock PII type to PIIType."""
        type_map = {
            "NAME": PIIType.NAME,
            "EMAIL": PIIType.EMAIL,
            "PHONE": PIIType.PHONE,
            "ADDRESS": PIIType.ADDRESS,
            "SSN": PIIType.SSN,
            "US_SOCIAL_SECURITY_NUMBER": PIIType.SSN,
            "CREDIT_DEBIT_NUMBER": PIIType.CREDIT_CARD,
            "IP_ADDRESS": PIIType.IP_ADDRESS,
            "DATE_TIME": PIIType.DATE,
            "DRIVER_ID": PIIType.DRIVER_LICENSE,
            "PASSPORT_NUMBER": PIIType.PASSPORT,
            "BANK_ACCOUNT_NUMBER": PIIType.BANK_ACCOUNT,
        }
        return type_map.get(bedrock_type, PIIType.CUSTOM)


class PresidioGuard(LLMGuard):
    """
    Microsoft Presidio integration for PII detection.
    Open-source, runs locally, good for enterprise use.
    """

    def __init__(self, language: str = "en"):
        from presidio_analyzer import AnalyzerEngine
        self.analyzer = AnalyzerEngine()
        self.language = language

    def detect(self, text: str) -> GuardResult:
        """Detect PII using Presidio."""
        results = self.analyzer.analyze(
            text=text,
            language=self.language
        )

        matches = []
        for result in results:
            pii_type = self._map_presidio_type(result.entity_type)
            matches.append(PIIMatch(
                pii_type=pii_type,
                value=text[result.start:result.end],
                start=result.start,
                end=result.end,
                confidence=result.score
            ))

        return GuardResult(matches=matches, model_used="presidio")

    def _map_presidio_type(self, presidio_type: str) -> PIIType:
        """Map Presidio entity type to PIIType."""
        type_map = {
            "PERSON": PIIType.NAME,
            "EMAIL_ADDRESS": PIIType.EMAIL,
            "PHONE_NUMBER": PIIType.PHONE,
            "LOCATION": PIIType.ADDRESS,
            "US_SSN": PIIType.SSN,
            "CREDIT_CARD": PIIType.CREDIT_CARD,
            "IP_ADDRESS": PIIType.IP_ADDRESS,
            "DATE_TIME": PIIType.DATE,
            "US_DRIVER_LICENSE": PIIType.DRIVER_LICENSE,
            "US_PASSPORT": PIIType.PASSPORT,
            "US_BANK_NUMBER": PIIType.BANK_ACCOUNT,
            "IBAN_CODE": PIIType.BANK_ACCOUNT,
        }
        return type_map.get(presidio_type, PIIType.CUSTOM)


class OpenAIGuard(LLMGuard):
    """
    OpenAI-based PII detection.
    Uses GPT models for intelligent PII identification.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini"
    ):
        from openai import OpenAI
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key)
        self.model = model

    def detect(self, text: str) -> GuardResult:
        """Detect PII using OpenAI."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a strict PII detection system. Find ALL personally identifiable information.\n\n"
                        "IMPORTANT: Always detect these types:\n"
                        "- name: Any person's full name or partial name (first name, last name, or both)\n"
                        "- email: Email addresses\n"
                        "- phone: Phone numbers in any format\n"
                        "- address: Physical addresses, cities, streets\n"
                        "- ssn: Social security numbers\n"
                        "- credit_card: Credit/debit card numbers\n"
                        "- date: Dates that could be birthdays or significant personal dates\n"
                        "- ip_address: IP addresses\n\n"
                        "Return JSON: {\"pii\": [{\"type\": \"...\", \"value\": \"exact text\", \"start\": position, \"end\": position}]}\n"
                        "If no PII found, return: {\"pii\": []}\n\n"
                        "Be thorough - it's better to flag something as PII than to miss it."
                    )
                },
                {"role": "user", "content": f"Find ALL PII in this text:\n\n{text}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )

        return self._parse_response(text, response)

    def _parse_response(self, text: str, response) -> GuardResult:
        matches = []
        try:
            content = json.loads(response.choices[0].message.content)
            pii_list = content.get("pii", content.get("results", content))

            if isinstance(pii_list, list):
                for item in pii_list:
                    pii_type = self._map_type(item.get("type", ""))
                    value = item.get("value", "")
                    start = item.get("start", text.find(value))
                    end = item.get("end", start + len(value) if start >= 0 else 0)

                    if value and start >= 0:
                        matches.append(PIIMatch(
                            pii_type=pii_type,
                            value=value,
                            start=start,
                            end=end,
                            confidence=0.90
                        ))
        except (json.JSONDecodeError, KeyError):
            pass

        return GuardResult(
            matches=matches,
            raw_response={"content": response.choices[0].message.content},
            model_used=self.model
        )

    def _map_type(self, type_str: str) -> PIIType:
        """Map type string to PIIType."""
        type_map = {
            "name": PIIType.NAME,
            "email": PIIType.EMAIL,
            "phone": PIIType.PHONE,
            "address": PIIType.ADDRESS,
            "ssn": PIIType.SSN,
            "credit_card": PIIType.CREDIT_CARD,
            "date": PIIType.DATE,
            "ip_address": PIIType.IP_ADDRESS,
        }
        return type_map.get(type_str.lower(), PIIType.CUSTOM)


def get_guard(
    provider: str = "regex",
    **kwargs
) -> Optional[LLMGuard]:
    """
    Factory function to get the appropriate guard.

    Args:
        provider: Guard provider name
        **kwargs: Provider-specific arguments

    Returns:
        LLMGuard instance or None for regex-only mode
    """
    providers = {
        "llama": lambda: LlamaGuard(**kwargs),
        "llama-guard": lambda: LlamaGuard(**kwargs),
        "bedrock": lambda: BedrockGuard(**kwargs),
        "aws": lambda: BedrockGuard(**kwargs),
        "presidio": lambda: PresidioGuard(**kwargs),
        "openai": lambda: OpenAIGuard(**kwargs),
        "gpt": lambda: OpenAIGuard(**kwargs),
    }

    provider = provider.lower()
    if provider in ["regex", "none", ""]:
        return None

    if provider not in providers:
        raise ValueError(f"Unknown guard provider: {provider}. Supported: {list(providers.keys())}")

    return providers[provider]()
