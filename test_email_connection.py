#!/usr/bin/env python3
"""
Test script to verify IONOS email connection
"""

import imaplib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import sys
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

print(f"Using email: {EMAIL_ADDRESS}")
print(f"Password length: {len(EMAIL_PASSWORD)} characters")

def test_imap_connection():
    """Test IMAP connection and list folders"""
    print("\n=== Testing IMAP Connection ===")
    try:
        # Connect to IMAP
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        print(f"✓ Connected to IMAP server {IMAP_SERVER}:{IMAP_PORT}")
        
        # Login
        mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        print(f"✓ Successfully logged in as {EMAIL_ADDRESS}")
        
        # List folders
        print("\nAvailable folders:")
        status, folders = mail.list()
        for folder in folders:
            print(f"  - {folder.decode()}")
            
        # Select INBOX
        mail.select('INBOX')
        
        # Check for emails
        status, messages = mail.search(None, 'ALL')
        email_count = len(messages[0].split()) if messages[0] else 0
        print(f"\n✓ INBOX contains {email_count} emails")
        
        # Check for unread emails
        status, unread = mail.search(None, 'UNSEEN')
        unread_count = len(unread[0].split()) if unread[0] else 0
        print(f"✓ {unread_count} unread emails")
        
        # Logout
        mail.close()
        mail.logout()
        print("\n✓ IMAP test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n✗ IMAP test failed: {str(e)}")
        return False


def test_smtp_connection():
    """Test SMTP connection by sending a test email"""
    print("\n=== Testing SMTP Connection ===")
    try:
        # Create test message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = EMAIL_ADDRESS  # Send to self
        msg['Subject'] = f"Test Email - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        body = """This is a test email from the Argan HR Email Management System.
        
If you receive this email, the SMTP configuration is working correctly.

System Details:
- SMTP Server: smtp.ionos.com
- Port: 465
- Encryption: SSL/TLS

This is an automated test message."""
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect to SMTP
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        print(f"✓ Connected to SMTP server {SMTP_SERVER}:{SMTP_PORT}")
        
        # Login
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        print(f"✓ Successfully authenticated")
        
        # Send email
        server.send_message(msg)
        print(f"✓ Test email sent to {EMAIL_ADDRESS}")
        
        # Disconnect
        server.quit()
        print("\n✓ SMTP test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n✗ SMTP test failed: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("Argan HR Email Management System - Email Connection Test")
    print("=" * 60)
    print(f"Testing email account: {EMAIL_ADDRESS}")
    
    # Test IMAP
    imap_success = test_imap_connection()
    
    # Test SMTP
    smtp_success = test_smtp_connection()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY:")
    print(f"  IMAP Connection: {'✓ PASSED' if imap_success else '✗ FAILED'}")
    print(f"  SMTP Connection: {'✓ PASSED' if smtp_success else '✗ FAILED'}")
    
    if imap_success and smtp_success:
        print("\n✓ All tests passed! Email integration is ready.")
        return 0
    else:
        print("\n✗ Some tests failed. Please check the configuration.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 