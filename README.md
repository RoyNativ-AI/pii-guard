<h1 align="center">PII Guard</h1>

<h4 align="center">Detect and anonymize PII in text with regex + optional LLM guards.</h4>

<p align="center">
  <a href="https://www.python.org/downloads/">
    <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python 3.8+">
  </a>
  <a href="https://pypi.org/project/pii-guard/">
    <img src="https://img.shields.io/badge/pip-pii--guard-green.svg" alt="pip install">
  </a>
  <a href="https://github.com/RoyNativ-AI/pii-guard/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/license-Proprietary-red.svg" alt="License">
  </a>
  <a href="https://github.com/RoyNativ-AI/pii-guard/stargazers">
    <img src="https://img.shields.io/github/stars/RoyNativ-AI/pii-guard?style=social" alt="Stars">
  </a>
</p>

<p align="center">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-features">Features</a> •
  <a href="#-why-pii-guard">Why PII Guard</a> •
  <a href="#-llm-guards">LLM Guards</a> •
  <a href="#-configuration">Configuration</a> •
  <a href="#-licensing">Licensing</a>
</p>

---

## Quick Start

```bash
# Install
pip install pii-guard

# Use
python -c "
from privacy_protector import PrivacyProtector
protector = PrivacyProtector()
print(protector.anonymize('Contact john@example.com or 555-1234'))
"
```

**That's it.** Emails, phones, SSNs, credit cards - all anonymized.

---

## Why PII Guard?

| Problem | How We Solve It |
|---------|-----------------|
| **GDPR/HIPAA compliance** | Detect and mask PII before storage or processing |
| **LLM data leakage** | Clean training data before sending to AI models |
| **Slow regex libraries** | Optimized patterns with early termination |
| **Inconsistent fakes** | Same input always produces same output |
| **Missing context** | LLM guards catch names/addresses that regex misses |
| **Complex setup** | One line: `pip install pii-guard` |

---

## Features

```
Regex Detection       Fast pattern matching for structured PII
LLM Guards            AI-powered detection for names, addresses
Realistic Fakes       Faker-generated data preserves format
Consistency           Same input → same output (deterministic)
Multiple Guards       OpenAI, Llama Guard, AWS Bedrock, Presidio
Batch Processing      Process files or text arrays
Custom Patterns       Add your own regex patterns
Multi-Language        Localization for 50+ countries
```

---

## Supported PII Types

| Type | Examples | Detection |
|------|----------|-----------|
| **Email** | john@example.com | Regex |
| **Phone** | 555-123-4567, +1-555-123-4567 | Regex |
| **SSN** | 123-45-6789 | Regex |
| **Credit Card** | 4111-1111-1111-1111 | Regex |
| **IP Address** | 192.168.1.1 | Regex |
| **Date of Birth** | 01/15/1985, 1985-01-15 | Regex |
| **Name** | John Smith | LLM Guard |
| **Address** | 123 Main St, New York | LLM Guard |

---

## Basic Usage

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

### With Detailed Report

```python
result = protector.anonymize_with_report(text)

print(f"PII Found: {result.pii_found}")
print(f"Processing Time: {result.processing_time_ms}ms")

for r in result.replacements:
    print(f"[{r['type']}] {r['original']} -> {r['replacement']}")
```

---

## LLM Guards

For detecting names, addresses, and unstructured PII that regex can't catch.

<details>
<summary><strong>OpenAI Guard</strong></summary>

```python
protector = PrivacyProtector(guard_provider="openai")
# Requires OPENAI_API_KEY environment variable
```

</details>

<details>
<summary><strong>AWS Bedrock Guard</strong></summary>

```python
protector = PrivacyProtector(
    guard_provider="bedrock",
    guardrail_id="your-guardrail-id",
    region="us-east-1"
)
```

</details>

<details>
<summary><strong>Llama Guard (Local)</strong></summary>

```python
protector = PrivacyProtector(
    guard_provider="llama",
    base_url="http://localhost:11434",
    model="llama-guard3"
)
```

</details>

<details>
<summary><strong>Microsoft Presidio</strong></summary>

```python
protector = PrivacyProtector(guard_provider="presidio")
# Requires: pip install presidio-analyzer
```

</details>

---

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

<details>
<summary><strong>View all options</strong></summary>

```python
config = ProtectorConfig(
    # Detection
    enabled_types=None,           # None = all types
    use_llm_guard=False,
    guard_provider="regex",       # 'regex', 'openai', 'presidio', 'bedrock', 'llama'
    guard_kwargs={},

    # Generation
    locale="en_US",               # Faker locale
    consistent_replacements=True, # Same input → same output
    seed=None,                    # Random seed for reproducibility

    # Output
    generate_report=True,
    preserve_format=True,
)
```

</details>

---

## File & Batch Processing

### Single File

```python
result = protector.process_file(
    input_file="sensitive_data.txt",
    output_file="anonymized_data.txt"
)
print(f"Anonymized {result.pii_found} PII items")
```

### Batch Processing

```python
texts = [
    "Email: john@example.com",
    "Phone: 555-1234",
    "SSN: 123-45-6789"
]

results = protector.process_batch(texts)
```

---

## Custom Patterns

```python
protector = PrivacyProtector()

# Add custom pattern for employee IDs
protector.add_custom_pattern("employee_id", r"EMP-\d{6}")

text = "Employee EMP-123456 reported the issue"
result = protector.anonymize(text)
# Employee [REDACTED-7433] reported the issue
```

---

## Localization

```python
# Israeli locale (Hebrew names, IL phone formats)
protector = PrivacyProtector(locale="he_IL")

# German locale
protector = PrivacyProtector(locale="de_DE")

# Japanese locale
protector = PrivacyProtector(locale="ja_JP")
```

---

## Use Cases

| Use Case | Description |
|----------|-------------|
| **GDPR Compliance** | Anonymize user data before analytics |
| **LLM Training** | Clean PII from training datasets |
| **Log Sanitization** | Strip PII from application logs |
| **Test Data** | Generate realistic fake data for testing |
| **Data Sharing** | Safely share datasets with third parties |
| **RAG Pipelines** | Clean documents before vector embedding |

---

## Comparison

| Feature | PII Guard | Presidio | regex only |
|---------|-----------|----------|------------|
| Setup | `pip install` | Complex | DIY |
| Names/Addresses | LLM Guards | NER models | No |
| Fake Data | Faker-powered | Basic | No |
| Consistency | Built-in | Manual | Manual |
| Performance | Optimized | Heavy | Fast |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Names not detected | Enable LLM guard: `guard_provider="openai"` |
| Inconsistent output | Set `consistent=True` |
| Wrong phone format | Change locale: `locale="de_DE"` |
| Missing PII type | Add custom pattern: `add_custom_pattern()` |

---

## Requirements

- Python 3.8+
- faker

```bash
pip install pii-guard
```

Optional (for LLM guards):
```bash
pip install openai              # For OpenAI guard
pip install presidio-analyzer   # For Presidio guard
pip install boto3               # For AWS Bedrock guard
```

---

## Licensing

**Proprietary Software** - All rights reserved by Officely AI.

This software requires a commercial license for any use beyond evaluation.

| Use Case | License Required |
|----------|------------------|
| Evaluation | Free |
| Personal/Academic | Contact us |
| Commercial | Required |

**Contact:** roy@officely.ai

See [LICENSE](LICENSE) for full terms.

---

## AI Prompt

Copy this to quickly set up with AI assistants:

```
I need to anonymize PII in my data. Use PII Guard from github.com/RoyNativ-AI/pii-guard

Setup:
pip install pii-guard

Usage:
from privacy_protector import PrivacyProtector
protector = PrivacyProtector()
clean_text = protector.anonymize(my_text)

I need to detect: [EMAILS / PHONES / SSN / ALL]
My use case: [GDPR / LLM TRAINING / LOGS]
```

---

<p align="center">
  <sub>Built by <a href="https://github.com/RoyNativ-AI">Roy Nativ</a> at <a href="https://officely.ai">Officely AI</a></sub>
</p>

<p align="center">
  <a href="https://github.com/RoyNativ-AI/pii-guard/issues">Report Bug</a> •
  <a href="https://github.com/RoyNativ-AI/pii-guard/issues">Request Feature</a> •
  <a href="mailto:roy@officely.ai">Get License</a>
</p>
