import re

def extract_info_with_regex(text):
    patterns = {
        "phone": r"(\+?\d{1,3})?\s?\d{7,10}\b",
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "creditcard": r"(\d{4}[-\s]?){3}\d{4}",
        "id": r"\b\d{9,}\b",
        "address": r"\b\d{1,4}\s\w+(\s\w+)*,\s?\w+(\s\w+)*\b",
        "dob": r"\b\d{1,2}/\d{1,2}/\d{4}\b",
        "password": r"(?i)password:\s*\S+",
        "bank_account": r"\b\d{9,18}\b",
        "ip_address": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"
    }
    matches = {}
    for key, pattern in patterns.items():
        matches[key] = re.findall(pattern, text)
    return matches