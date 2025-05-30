#!/usr/bin/env python3
"""
Test different authentication variations for IONOS
"""

import imaplib
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "argan-bot@arganhrconsultancy.co.uk")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "Dashboard2025!")
IMAP_SERVER = "imap.ionos.com"
IMAP_PORT = 993

print("=== Testing Different Authentication Variations ===")
print(f"Full email: {EMAIL_ADDRESS}")
print(f"Password: {EMAIL_PASSWORD}")
print()

# Test variations
test_cases = [
    ("Full email address", EMAIL_ADDRESS, EMAIL_PASSWORD),
    ("Username only", "argan-bot", EMAIL_PASSWORD),
    ("Full email with escaped @", EMAIL_ADDRESS.replace("@", "\\@"), EMAIL_PASSWORD),
]

for test_name, username, password in test_cases:
    print(f"\nTesting: {test_name}")
    print(f"Username: {username}")
    
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(username, password)
        print("✓ Login successful!")
        mail.logout()
    except imaplib.IMAP4.error as e:
        print(f"✗ Login failed: {e}")
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {e}")

# Also test if the issue is with the password itself
print("\n=== Password Check ===")
print(f"Password contains @ symbol: {'@' in EMAIL_PASSWORD}")
print(f"Password contains special chars: {any(c in EMAIL_PASSWORD for c in '@!#$%^&*()_+-=[]{}|;:,.<>?')}")
print("\nNote: IONOS should accept passwords with special characters.")
print("\nPossible issues:")
print("1. The password might be incorrect (typo when entering it)")
print("2. The account might be locked")
print("3. The account might need to be activated for IMAP/SMTP access")
print("4. There might be IP-based restrictions") 