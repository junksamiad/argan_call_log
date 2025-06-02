#!/usr/bin/env python3
"""
Debug Email Issue
Tests the email service directly to see what's causing the empty error messages
"""

import sys
import asyncio
from dotenv import load_dotenv

load_dotenv()
sys.path.append('backend')

from backend.email_functions.email_service import EmailService

async def debug_email_issue():
    """Debug the email sending issue"""
    print('🔍 Debugging Email Service Issue')
    print('=' * 60)
    
    email_service = EmailService()
    
    # Test emails that were failing
    test_emails = [
        "junksamiad@gmail.com",
        "bloxtersamiad@gmail.com", 
        "cvrcontractsltd@gmail.com"  # This one worked
    ]
    
    for email in test_emails:
        print(f'📧 Testing email to: {email}')
        
        try:
            result = await email_service.send_hr_response(
                to_email=email,
                subject="Test Email - Debug Issue",
                content_text="This is a test email to debug the sending issue.",
                ticket_number="TEST-DEBUG-001"
            )
            
            print(f'   Result: {result}')
            
            if result.get('success'):
                print(f'   ✅ SUCCESS: Email sent to {email}')
            else:
                print(f'   ❌ FAILED: {result.get("message", "Unknown error")}')
                print(f'   📊 Status Code: {result.get("status_code", "Unknown")}')
                print(f'   📝 Error Details: {result.get("error", "No error details")}')
                
        except Exception as e:
            print(f'   💥 EXCEPTION: {e}')
            print(f'   📝 Exception Type: {type(e).__name__}')
        
        print()
    
    # Test SendGrid connection
    print('🔗 Testing SendGrid Connection:')
    try:
        connection_result = await email_service.test_connection()
        print(f'   Connection Result: {connection_result}')
    except Exception as e:
        print(f'   💥 Connection Exception: {e}')

if __name__ == "__main__":
    asyncio.run(debug_email_issue()) 