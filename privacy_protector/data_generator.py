import random

def generate_fake_data(data_type, original):
    if data_type == "name":
        return f"FAKE_NAME_{random.randint(1000, 9999)}"
    elif data_type == "phone":
        return ''.join(random.choice('0123456789') for _ in range(10))
    elif data_type == "email":
        return f"fake_email_{random.randint(1000, 9999)}@example.com"
    elif data_type == "creditcard":
        return ''.join(random.choice('0123456789') for _ in range(16))
    elif data_type == "id":
        return ''.join(random.choice('0123456789') for _ in range(len(original)))
    elif data_type == "address":
        return f"FAKE_ADDRESS_{random.randint(1000, 9999)}"
    elif data_type == "dob":
        return f"01/01/{random.randint(1950, 2000)}"
    elif data_type == "password":
        return "FAKE_PASSWORD"
    elif data_type == "bank_account":
        return ''.join(random.choice('0123456789') for _ in range(len(original)))
    elif data_type == "ip_address":
        return "0.0.0.0"
    else:
        return f"REDACTED_{random.randint(1000, 9999)}"