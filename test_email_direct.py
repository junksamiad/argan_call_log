"""
Direct email test to diagnose delivery issues
"""

import asyncio
import os
from dotenv import load_dotenv
from backend.email_functions.email_service import EmailService

async def test_direct_email():
    """Test sending email directly"""
    
    load_dotenv()
    
    print("🧪 Testing direct email sending...")
    
    email_service = EmailService()
    
    # Test email content
    result = await email_service.send_hr_response(
        to_email="bloxtersamiad@gmail.com",  # Your test email
        subject="Direct Test Email from HR System",
        content_text="""Hello,

This is a direct test email from the HR email management system.

If you receive this, the email sending is working correctly.

Test details:
- Sent directly from email service
- Using verified sender address
- With proper headers

Best regards,
HR System Test""",
        content_html="""<div style="font-family: Arial, sans-serif;">
<h2>Direct Test Email</h2>
<p>Hello,</p>
<p>This is a direct test email from the HR email management system.</p>
<p><strong>If you receive this, the email sending is working correctly.</strong></p>
<h3>Test details:</h3>
<ul>
<li>Sent directly from email service</li>
<li>Using verified sender address</li>
<li>With proper headers</li>
</ul>
<p>Best regards,<br><strong>HR System Test</strong></p>
</div>""",
        ticket_number="TEST-001"
    )
    
    print(f"📧 Email result: {result}")
    
    if result.get('success'):
        print("✅ Email sent successfully!")
        print("📱 Check your email (including spam folder)")
        print(f"📧 Recipient: {result.get('recipient')}")
        print(f"📝 Subject: {result.get('subject')}")
    else:
        print("❌ Email failed!")
        print(f"Error: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(test_direct_email()) 