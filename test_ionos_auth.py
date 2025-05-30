#!/usr/bin/env python3
"""
Detailed IONOS authentication test script
"""

import imaplib
import smtplib
import ssl
import socket
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Email configuration from environment
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "argan-bot@arganhrconsultancy.co.uk")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "Dashboard2025!")
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.ionos.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.ionos.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))

print("=== IONOS Authentication Detailed Test ===")
print(f"Email: {EMAIL_ADDRESS}")
print(f"Password length: {len(EMAIL_PASSWORD)} characters")
print(f"Password starts with: {EMAIL_PASSWORD[:3]}... ends with: ...{EMAIL_PASSWORD[-3:]}")
print()

def test_connectivity():
    """Test basic connectivity to servers"""
    print("=== Testing Basic Connectivity ===")
    
    # Test IMAP connectivity
    try:
        print(f"Testing connection to {IMAP_SERVER}:{IMAP_PORT}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((IMAP_SERVER, IMAP_PORT))
        sock.close()
        if result == 0:
            print("✓ IMAP server is reachable")
        else:
            print("✗ Cannot reach IMAP server")
    except Exception as e:
        print(f"✗ IMAP connectivity test failed: {e}")
    
    # Test SMTP connectivity
    try:
        print(f"Testing connection to {SMTP_SERVER}:{SMTP_PORT}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((SMTP_SERVER, SMTP_PORT))
        sock.close()
        if result == 0:
            print("✓ SMTP server is reachable")
        else:
            print("✗ Cannot reach SMTP server")
    except Exception as e:
        print(f"✗ SMTP connectivity test failed: {e}")

def test_ssl_support():
    """Test SSL/TLS support"""
    print("\n=== Testing SSL/TLS Support ===")
    try:
        context = ssl.create_default_context()
        print(f"SSL version: {ssl.OPENSSL_VERSION}")
        print("✓ SSL/TLS support available")
    except Exception as e:
        print(f"✗ SSL/TLS error: {e}")

def test_imap_detailed():
    """Test IMAP with detailed error handling"""
    print("\n=== Detailed IMAP Test ===")
    
    try:
        # Test raw connection
        print(f"1. Creating SSL connection to {IMAP_SERVER}:{IMAP_PORT}...")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        print("✓ SSL connection established")
        
        # Get capabilities
        print("\n2. Getting server capabilities...")
        typ, data = mail.capability()
        if typ == 'OK':
            print(f"✓ Server capabilities: {data[0].decode()}")
        
        # Test login
        print(f"\n3. Attempting login with email: {EMAIL_ADDRESS}")
        try:
            mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            print("✓ IMAP login successful!")
            
            # List folders
            print("\n4. Listing available folders...")
            typ, folders = mail.list()
            if typ == 'OK':
                print("✓ Available folders:")
                for folder in folders[:5]:  # Show first 5 folders
                    print(f"  - {folder.decode()}")
            
            mail.logout()
            
        except imaplib.IMAP4.error as e:
            error_msg = str(e)
            print(f"✗ IMAP login failed: {error_msg}")
            
            # Check specific error types
            if "authentication failed" in error_msg.lower():
                print("\nPossible causes:")
                print("1. Incorrect password")
                print("2. Account locked or disabled")
                print("3. Two-factor authentication enabled")
                print("4. Special characters in password need escaping")
            elif "invalid credentials" in error_msg.lower():
                print("\nThe username or password is incorrect.")
                
    except Exception as e:
        print(f"✗ IMAP connection error: {type(e).__name__}: {e}")

def test_smtp_detailed():
    """Test SMTP with detailed error handling"""
    print("\n=== Detailed SMTP Test ===")
    
    try:
        # Test connection
        print(f"1. Creating SSL connection to {SMTP_SERVER}:{SMTP_PORT}...")
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.set_debuglevel(1)  # Enable debug output
        print("✓ SSL connection established")
        
        # Get server info
        print("\n2. Getting server info...")
        server.ehlo()
        
        # Test login
        print(f"\n3. Attempting login with email: {EMAIL_ADDRESS}")
        try:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            print("✓ SMTP login successful!")
            server.quit()
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"✗ SMTP authentication failed: {e}")
            print("\nError code:", e.smtp_code)
            print("Error message:", e.smtp_error.decode() if isinstance(e.smtp_error, bytes) else e.smtp_error)
            
    except Exception as e:
        print(f"✗ SMTP connection error: {type(e).__name__}: {e}")

def main():
    test_connectivity()
    test_ssl_support()
    test_imap_detailed()
    test_smtp_detailed()
    
    print("\n=== Test Summary ===")
    print("Check the detailed output above to identify the specific issue.")

if __name__ == "__main__":
    main() 