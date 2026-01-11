# PII Guard

Detect and anonymize PII (Personally Identifiable Information) in text using regex patterns and optional LLM guards.

## Features

- **Regex Detection** - Fast pattern matching for emails, phones, SSN, credit cards, IPs, dates
- **LLM Guards** - Optional AI-powered detection for names and complex PII
- **Realistic Fake Data** - Faker-powered replacement that preserves format
- **Consistent Mapping** - Same input always produces same output
- **Multiple Guards** - OpenAI, Llama Guard, AWS Bedrock, Presidio

## Installation

```bash
pip install pii-guard
```

## Quick Start

```python
from privacy_protector import PrivacyProtector

protector = PrivacyProtector()

text = """
Contact John Smith at john.smith@example.com or call 555-123-4567.
SSN: 123-45-6789, Credit Card: 4111-1111-1111-1111
"""

anonymized = protector.anonymize(text)
# Contact John Smith at tburns@example.org or call 302.920.5861.
# SSN: 033-50-2167, Credit Card: 3512-3853-3871-1096
```

## Supported PII Types

| Type | Examples | Detection |
|------|----------|-----------|
| Email | john@example.com | Regex |
| Phone | 555-123-4567, +1-555-123-4567 | Regex |
| SSN | 123-45-6789 | Regex |
| Credit Card | 4111-1111-1111-1111 | Regex |
| IP Address | 192.168.1.1 | Regex |
| Date | 01/15/1985, 2023-01-15 | Regex |
| Name | John Smith | LLM Guard |
| Address | 123 Main St | LLM Guard |

## LLM Guards

For detecting names and unstructured PII, enable an LLM guard:

### OpenAI Guard

```python
from privacy_protector import PrivacyProtector

protector = PrivacyProtector(guard_provider="openai")
# Requires OPENAI_API_KEY environment variable
```

### AWS Bedrock Guard

```python
protector = PrivacyProtector(
    guard_provider="bedrock",
    guardrail_id="your-guardrail-id",
    region="us-east-1"
)
```

### Llama Guard (Local)

```python
protector = PrivacyProtector(
    guard_provider="llama",
    base_url="http://localhost:11434",
    model="llama-guard3"
)
```

### Microsoft Presidio

```python
protector = PrivacyProtector(guard_provider="presidio")
# Requires: pip install presidio-analyzer
```

## Detailed Reports

```python
result = protector.anonymize_with_report(text)

print(f"PII Found: {result.pii_found}")
print(f"Processing Time: {result.processing_time_ms}ms")

for r in result.replacements:
    print(f"[{r['type']}] {r['original']} -> {r['replacement']}")
```

## Custom Patterns

```python
protector = PrivacyProtector()

# Add custom pattern for employee IDs
protector.add_custom_pattern("employee_id", r"EMP-\d{6}")

text = "Employee EMP-123456 reported the issue"
result = protector.anonymize(text)
# Employee [REDACTED-7433] reported the issue
```

## Configuration

```python
from privacy_protector import PrivacyProtector, ProtectorConfig, PIIType

config = ProtectorConfig(
    enabled_types=[PIIType.EMAIL, PIIType.PHONE, PIIType.SSN],
    locale="en_US",
    consistent_replacements=True,
    use_llm_guard=True,
    guard_provider="openai"
)

protector = PrivacyProtector(config=config)
```

## File Processing

```python
result = protector.process_file(
    input_file="sensitive_data.txt",
    output_file="anonymized_data.txt"
)

print(f"Anonymized {result.pii_found} PII items")
```

## Batch Processing

```python
texts = [
    "Email: john@example.com",
    "Phone: 555-1234",
    "SSN: 123-45-6789"
]

results = protector.process_batch(texts)
```

## Localization

```python
# Israeli locale
protector = PrivacyProtector(locale="he_IL")

# German locale
protector = PrivacyProtector(locale="de_DE")
```

## Consistency

Same input always produces same output (useful for testing):

```python
protector = PrivacyProtector(consistent=True)

result1 = protector.anonymize("test@example.com")
result2 = protector.anonymize("test@example.com")

assert result1 == result2  # Always true
```

## License

**Proprietary Software** - All rights reserved by Officely AI.

This software requires a commercial license for any use beyond evaluation.
See [LICENSE](LICENSE) for details.

Contact: roy@officely.ai

---

Built by [Officely AI](https://officely.ai)
