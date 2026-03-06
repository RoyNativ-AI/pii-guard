"""
Privacy Protector - Detect and anonymize PII in text
"""

from .protector import (
    PrivacyProtector,
    ProtectorConfig,
    AnonymizationResult,
)
from .detectors import (
    RegexDetector,
    PIIMatch,
    PIIType,
)
from .generators import (
    FakeDataGenerator,
)
from .guards import (
    LLMGuard,
    LlamaGuard,
    BedrockGuard,
    PresidioGuard,
    OpenAIGuard,
    get_guard,
)

__version__ = "2.0.0"
__all__ = [
    # Main API
    "PrivacyProtector",
    "ProtectorConfig",
    "AnonymizationResult",
    # Detectors
    "RegexDetector",
    "PIIMatch",
    "PIIType",
    # Generators
    "FakeDataGenerator",
    # Guards
    "LLMGuard",
    "LlamaGuard",
    "BedrockGuard",
    "PresidioGuard",
    "OpenAIGuard",
    "get_guard",
]
