#!/usr/bin/env python3
"""
Test IONOS with the special username from the email client settings
"""

import imaplib
import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# IONOS Configuration
EMAIL_ADDRESS = "argan-bot@arganhrconsultancy.co.uk"
EMAIL_USERNAME = "mp1018396404-1748417273476"  # Special IONOS username
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "Arg@n-Recru1ment123")

# Server settings
IMAP_SERVER = "imap.ionos.com"
IMAP_PORT = 993
SMTP_SERVER = "smtp.ionos.com"
SMTP_PORT = 465

print("=== IONOS Authentication Test with Special Username ===")
print(f"Email Address: {EMAIL_ADDRESS}")
print(f"Username: {EMAIL_USERNAME}")
print(f"Password length: {len(EMAIL_PASSWORD)} characters")
print()

def test_imap():
    """Test IMAP with IONOS username"""
    print("=== Testing IMAP ===")
    try:
        print(f"Connecting to {IMAP_SERVER}:{IMAP_PORT}...")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        print("✓ Connected")
        
        print(f"Logging in with username: {EMAIL_USERNAME}")
        mail.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        print("✓ IMAP login successful!")
        
        # List folders
        _, folders = mail.list()
        print("\nAvailable folders:")
        for folder in folders[:5]:
            print(f"  - {folder.decode()}")
        
        mail.logout()
        return True
        
    except Exception as e:
        print(f"✗ IMAP test failed: {e}")
        return False

def test_smtp():
    """Test SMTP with IONOS username"""
    print("\n=== Testing SMTP ===")
    try:
        print(f"Connecting to {SMTP_SERVER}:{SMTP_PORT}...")
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        print("✓ Connected")
        
        print(f"Logging in with username: {EMAIL_USERNAME}")
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        print("✓ SMTP login successful!")
        
        # Send test email
        msg = MIMEText("Test email using IONOS username")
        msg['Subject'] = 'IONOS Username Test'
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = EMAIL_ADDRESS
        
        server.send_message(msg)
        print("✓ Test email sent!")
        
        server.quit()
        return True
        
    except Exception as e:
        print(f"✗ SMTP test failed: {e}")
        return False

def test_smtp_port_587():
    """Test SMTP with port 587 (as shown in screenshot)"""
    print("\n=== Testing SMTP Port 587 ===")
    try:
        print(f"Connecting to {SMTP_SERVER}:587...")
        server = smtplib.SMTP(SMTP_SERVER, 587)
        server.starttls()
        print("✓ Connected with STARTTLS")
        
        print(f"Logging in with username: {EMAIL_USERNAME}")
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        print("✓ SMTP login successful on port 587!")
        
        server.quit()
        return True
        
    except Exception as e:
        print(f"✗ SMTP port 587 test failed: {e}")
        return False

if __name__ == "__main__":
    # Test IMAP
    imap_success = test_imap()
    
    # Test SMTP
    smtp_success = test_smtp()
    
    # Test alternative SMTP port
    smtp_587_success = test_smtp_port_587()
    
    print("\n=== Summary ===")
    print(f"IMAP: {'✓ PASSED' if imap_success else '✗ FAILED'}")
    print(f"SMTP (465): {'✓ PASSED' if smtp_success else '✗ FAILED'}")
    print(f"SMTP (587): {'✓ PASSED' if smtp_587_success else '✗ FAILED'}")
    
    print("\n=== Next Steps ===")
    print("1. Add EMAIL_USERNAME=mp1018396404-1748417273476 to your .env file")
    print("2. The email service will automatically use this username for authentication")
    print("3. Consider using port 587 for SMTP if 465 doesn't work") 