#!/usr/bin/env python3
"""
Test script for SendGrid integration
"""

import os
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import requests
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# Configuration
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "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")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "support@email.adaptixinnovation.co.uk")
PARSE_DOMAIN = os.getenv("PARSE_DOMAIN", "email.adaptixinnovation.co.uk")

print("=== SendGrid Integration Test ===")
print(f"From Email: {EMAIL_ADDRESS}")
print(f"Parse Domain: {PARSE_DOMAIN}")
print()


def test_send_email():
    """Test sending an email via SendGrid"""
    print("=== Testing Email Send ===")
    
    try:
        # Create message
        message = Mail(
            from_email=EMAIL_ADDRESS,
            to_emails=EMAIL_ADDRESS,  # Send to self for testing
            subject=f'SendGrid Test - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            plain_text_content='This is a test email from the Argan HR Email Management System using SendGrid.'
        )
        
        # Send email
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        
        print(f"✓ Email sent successfully!")
        print(f"  Status Code: {response.status_code}")
        print(f"  Headers: {dict(response.headers)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to send email: {e}")
        return False


def test_api_key():
    """Test SendGrid API key validity"""
    print("=== Testing API Key ===")
    
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        
        # Test API key by getting account details
        response = requests.get(
            "https://api.sendgrid.com/v3/user/profile",
            headers={"Authorization": f"Bearer {SENDGRID_API_KEY}"}
        )
        
        if response.status_code == 200:
            profile = response.json()
            print("✓ API key is valid!")
            print(f"  Account: {profile.get('email', 'N/A')}")
            print(f"  Username: {profile.get('username', 'N/A')}")
            return True
        else:
            print(f"✗ API key validation failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Error testing API key: {e}")
        return False


def test_webhook_endpoint():
    """Provide instructions for testing the webhook"""
    print("\n=== Webhook Testing Instructions ===")
    print("1. First, ensure your FastAPI server is running:")
    print("   uvicorn backend.main:app --reload")
    print()
    print("2. For local testing, use ngrok to expose your endpoint:")
    print("   ngrok http 8000")
    print()
    print("3. Update SendGrid Inbound Parse settings:")
    print(f"   - Domain: {PARSE_DOMAIN}")
    print("   - URL: https://your-ngrok-url.ngrok.io/inbound")
    print()
    print("4. Send a test email to:")
    print(f"   test@{PARSE_DOMAIN}")
    print()
    print("5. Monitor your FastAPI logs for the incoming webhook")


def check_dns_records():
    """Check DNS configuration"""
    print("\n=== DNS Configuration Check ===")
    print("Please verify these DNS records are configured:")
    print()
    print("MX Records for email.adaptixinnovation.co.uk:")
    print("  - mxa.sendgrid.net (priority 10)")
    print("  - mxb.sendgrid.net (priority 20)")
    print()
    print("CNAME Records for authentication:")
    print("  - em8479.email → u53190391.wl142.sendgrid.net")
    print("  - s1._domainkey.email → s1.domainkey.u53190391.wl142.sendgrid.net")
    print("  - s2._domainkey.email → s2.domainkey.u53190391.wl142.sendgrid.net")
    print()
    print("Use 'dig' or 'nslookup' to verify:")
    print(f"  dig MX {PARSE_DOMAIN}")


if __name__ == "__main__":
    # Test API key
    api_key_valid = test_api_key()
    
    if api_key_valid:
        # Test sending email
        send_success = test_send_email()
        
        # Check DNS
        check_dns_records()
        
        # Webhook instructions
        test_webhook_endpoint()
        
        print("\n=== Summary ===")
        print(f"API Key Valid: {'✓' if api_key_valid else '✗'}")
        print(f"Email Send: {'✓' if send_success else '✗'}")
        print("\nNext steps:")
        print("1. Run the FastAPI server")
        print("2. Set up ngrok for local testing")
        print("3. Send test emails to trigger the webhook")
    else:
        print("\n✗ Fix the API key issue first!") 