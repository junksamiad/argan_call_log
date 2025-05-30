#!/usr/bin/env python3
"""
SendGrid Email Sending Test
Tests the ability to send emails through SendGrid API
"""

import os
import sys
import ssl
import certifi

# Fix SSL certificate issues on macOS
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, From, To, Subject, PlainTextContent, HtmlContent
from dotenv import load_dotenv

def test_sendgrid_sending():
    """Test SendGrid email sending functionality"""
    
    # Load environment variables
    load_dotenv()
    
    # Get configuration
    api_key = os.getenv('SENDGRID_API_KEY')
    from_email = os.getenv('EMAIL_ADDRESS', 'support@email.adaptixinnovation.co.uk')
    
    if not api_key:
        print("❌ ERROR: SENDGRID_API_KEY not found in environment variables")
        print("Please add your SendGrid API key to your .env file:")
        print("SENDGRID_API_KEY=SG.your-api-key-here")
        return False
    
    if not api_key.startswith('SG.'):
        print("❌ ERROR: Invalid SendGrid API key format")
        print("SendGrid API keys should start with 'SG.'")
        return False
    
    print("🔧 SendGrid Configuration:")
    print(f"   📧 From Email: {from_email}")
    print(f"   🔑 API Key: {api_key[:10]}...{api_key[-4:]}")
    print()
    
    # Get test recipient
    test_email = input("Enter your email address to receive the test email: ").strip()
    if not test_email or '@' not in test_email:
        print("❌ Invalid email address")
        return False
    
    try:
        # Create SendGrid client
        sg = SendGridAPIClient(api_key=api_key)
        
        # Create test email
        message = Mail(
            from_email=From(from_email, "Argan HR System Test"),
            to_emails=To(test_email),
            subject=Subject("🧪 SendGrid Test - HR Email System"),
            plain_text_content=PlainTextContent("""
Hello!

This is a test email from your Argan HR Email Management System.

If you're receiving this email, it means:
✅ SendGrid API key is working
✅ Email sending functionality is operational
✅ Your system can send responses to HR queries

System Details:
- Sent via SendGrid API
- From: Argan HR Consultancy System
- Test performed: Email sending capability

Best regards,
Argan HR System
            """),
            html_content=HtmlContent("""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2c5aa0;">🧪 SendGrid Test Email</h2>
    
    <p>Hello!</p>
    
    <p>This is a test email from your <strong>Argan HR Email Management System</strong>.</p>
    
    <div style="background-color: #f0f8ff; padding: 15px; border-left: 4px solid #2c5aa0; margin: 20px 0;">
        <p><strong>If you're receiving this email, it means:</strong></p>
        <ul>
            <li>✅ SendGrid API key is working</li>
            <li>✅ Email sending functionality is operational</li>
            <li>✅ Your system can send responses to HR queries</li>
        </ul>
    </div>
    
    <h3>System Details:</h3>
    <ul>
        <li><strong>Sent via:</strong> SendGrid API</li>
        <li><strong>From:</strong> Argan HR Consultancy System</li>
        <li><strong>Test performed:</strong> Email sending capability</li>
    </ul>
    
    <p style="margin-top: 30px;">
        Best regards,<br>
        <strong>Argan HR System</strong>
    </p>
</body>
</html>
            """)
        )
        
        print("📤 Sending test email...")
        
        # Send the email
        response = sg.send(message)
        
        # Check response
        if response.status_code == 202:
            print("✅ SUCCESS! Test email sent successfully")
            print(f"   📊 Status Code: {response.status_code}")
            print(f"   📧 Sent to: {test_email}")
            print(f"   📬 From: {from_email}")
            print()
            print("🔍 Check your email inbox (and spam folder) for the test message.")
            print("   If you receive it, your SendGrid sending is working perfectly!")
            return True
        else:
            print(f"❌ FAILED: Unexpected status code {response.status_code}")
            print(f"Response body: {response.body}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR sending email: {e}")
        
        # Provide specific error guidance
        error_str = str(e).lower()
        if 'unauthorized' in error_str or '401' in error_str:
            print("\n💡 This looks like an API key issue:")
            print("   1. Check your SendGrid API key is correct")
            print("   2. Ensure the API key has 'Mail Send' permissions")
            print("   3. Verify the key hasn't expired")
        elif 'forbidden' in error_str or '403' in error_str:
            print("\n💡 This looks like a permissions issue:")
            print("   1. Check your SendGrid account is active")
            print("   2. Verify your API key has sending permissions")
            print("   3. Check if your account has sending limits")
        elif 'domain' in error_str:
            print("\n💡 This looks like a domain authentication issue:")
            print("   1. Verify your sender domain is authenticated in SendGrid")
            print("   2. Check DNS records are properly configured")
        
        return False

def check_sendgrid_setup():
    """Check SendGrid account setup and permissions"""
    load_dotenv()
    api_key = os.getenv('SENDGRID_API_KEY')
    
    if not api_key:
        print("❌ No SendGrid API key found")
        return False
    
    try:
        sg = SendGridAPIClient(api_key=api_key)
        
        print("🔍 Checking SendGrid account setup...")
        
        # Check API key permissions (this will fail if key is invalid)
        response = sg.client.user.get()
        if response.status_code == 200:
            print("✅ API key is valid and has basic permissions")
        
        # Try to get sender identities
        try:
            senders_response = sg.client.senders.get()
            if senders_response.status_code == 200:
                print("✅ Can access sender identities")
            else:
                print("⚠️  Limited access to sender identities")
        except:
            print("⚠️  Cannot check sender identities (may need different permissions)")
        
        return True
        
    except Exception as e:
        print(f"❌ SendGrid setup check failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 SENDGRID EMAIL SENDING TEST")
    print("=" * 60)
    print()
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ No .env file found!")
        print("Please create a .env file with your SendGrid configuration:")
        print()
        print("1. Copy env.example to .env:")
        print("   cp env.example .env")
        print()
        print("2. Edit .env and add your SendGrid API key:")
        print("   SENDGRID_API_KEY=SG.your-actual-api-key-here")
        print()
        sys.exit(1)
    
    # Check SendGrid setup
    if not check_sendgrid_setup():
        print("\n❌ SendGrid setup check failed. Please fix the issues above.")
        sys.exit(1)
    
    print()
    
    # Run sending test
    success = test_sendgrid_sending()
    
    print()
    print("=" * 60)
    if success:
        print("🎉 SENDGRID SENDING TEST PASSED!")
        print("Your system is ready to send email responses!")
    else:
        print("❌ SENDGRID SENDING TEST FAILED!")
        print("Please fix the issues above before proceeding.")
    print("=" * 60) 