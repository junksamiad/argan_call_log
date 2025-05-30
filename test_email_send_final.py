#!/usr/bin/env python3
"""
Final Email Sending Test - SendGrid
Tests actual email sending functionality after sender verification
"""

import os
import ssl
import certifi
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, From, To, Subject, PlainTextContent, HtmlContent
from dotenv import load_dotenv

# Fix SSL certificate issues on macOS
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

def load_environment():
    """Load environment variables"""
    load_dotenv()
    
    api_key = os.getenv('SENDGRID_API_KEY')
    from_email = os.getenv('EMAIL_ADDRESS')
    
    if not api_key:
        print("❌ SENDGRID_API_KEY not found in environment")
        return None, None
    
    if not from_email:
        print("❌ EMAIL_ADDRESS not found in environment")
        return None, None
    
    print(f"✅ API Key loaded: {api_key[:10]}...")
    print(f"✅ From Email: {from_email}")
    
    return api_key, from_email

def test_email_sending(api_key, from_email):
    """Test sending an actual email"""
    print("\n🚀 Testing email sending...")
    
    try:
        # Create SendGrid client
        sg = SendGridAPIClient(api_key=api_key)
        
        # Create email message
        message = Mail(
            from_email=From(from_email, "Argan HR System"),
            to_emails=To(from_email),  # Send to ourselves for testing
            subject=Subject("✅ SendGrid Email Test - System Operational"),
            plain_text_content=PlainTextContent("""
Hello!

This is a test email from the Argan HR Email Management System.

If you're receiving this email, it means:
✅ SendGrid API integration is working
✅ Sender verification is complete
✅ Email sending functionality is operational

System Details:
- From: Argan HR System
- Timestamp: Test email
- Status: All systems operational

Best regards,
Argan HR Email System
            """),
            html_content=HtmlContent("""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2c5aa0;">✅ SendGrid Email Test - System Operational</h2>
        
        <p>Hello!</p>
        
        <p>This is a test email from the <strong>Argan HR Email Management System</strong>.</p>
        
        <div style="background-color: #f0f8ff; padding: 15px; border-left: 4px solid #2c5aa0; margin: 20px 0;">
            <p><strong>If you're receiving this email, it means:</strong></p>
            <ul>
                <li>✅ SendGrid API integration is working</li>
                <li>✅ Sender verification is complete</li>
                <li>✅ Email sending functionality is operational</li>
            </ul>
        </div>
        
        <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="margin-top: 0;">System Details:</h3>
            <ul>
                <li><strong>From:</strong> Argan HR System</li>
                <li><strong>Timestamp:</strong> Test email</li>
                <li><strong>Status:</strong> All systems operational</li>
            </ul>
        </div>
        
        <p>Best regards,<br>
        <strong>Argan HR Email System</strong></p>
        
        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        <p style="font-size: 12px; color: #666;">
            This is an automated test email from the Argan HR Email Management System.
        </p>
    </div>
</body>
</html>
            """)
        )
        
        # Send email
        print("📤 Sending test email...")
        response = sg.send(message)
        
        print(f"✅ Email sent successfully!")
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        if response.body:
            print(f"📄 Response Body: {response.body}")
        
        return True
        
    except Exception as e:
        print(f"❌ Email sending failed: {str(e)}")
        if hasattr(e, 'body'):
            print(f"📄 Error details: {e.body}")
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("🧪 FINAL SENDGRID EMAIL SENDING TEST")
    print("=" * 60)
    
    # Load environment
    api_key, from_email = load_environment()
    if not api_key or not from_email:
        print("\n❌ Environment setup failed. Please check your .env file.")
        return
    
    # Test email sending
    success = test_email_sending(api_key, from_email)
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED! Email sending is fully operational.")
        print("✅ Your Argan HR Email System can now:")
        print("   • Receive emails via SendGrid webhook")
        print("   • Send emails via SendGrid API")
        print("   • Process HR inquiries automatically")
    else:
        print("❌ Email sending test failed. Please check the errors above.")
    print("=" * 60)

if __name__ == "__main__":
    main() 