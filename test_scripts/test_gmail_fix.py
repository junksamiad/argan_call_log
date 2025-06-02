#!/usr/bin/env python3
"""
Test Gmail Fix - Email Address Extraction
Tests the complete email flow with the problematic email format that was causing Gmail blocking
"""

import asyncio
import json
import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.append('backend')

from backend.email_functions.webhook_handler import WebhookHandler

async def test_gmail_fix():
    """Test the complete email flow with the exact format that was causing Gmail issues"""
    
    # Load environment variables
    load_dotenv()
    
    print("🧪 Testing Gmail Delivery Fix")
    print("=" * 60)
    
    # Initialize webhook handler
    webhook_handler = WebhookHandler()
    
    # Simulate webhook data with the problematic format that was causing Gmail blocking
    test_webhook_data = {
        "from": "cvrcontractsltd <cvrcontractsltd@gmail.com>",  # This format was causing the issue
        "to": ["email@email.adaptixinnovation.co.uk"],
        "subject": "Test Staffing Issue - Gmail Delivery Fix",
        "text": "Hi,\n\nWe need urgent help with a staffing issue at our company. Please get back to us ASAP.\n\nRegards,\nCVR Contracts",
        "html": "<p>Hi,</p><p>We need urgent help with a staffing issue at our company. Please get back to us ASAP.</p><p>Regards,<br>CVR Contracts</p>",
        "message_id": "test-message-gmail-fix-123",
        "timestamp": "2025-05-31T22:15:00Z"
    }
    
    print(f"📧 Raw webhook 'from' field: {test_webhook_data['from']}")
    print(f"📝 Subject: {test_webhook_data['subject']}")
    print()
    
    # Test the email extraction first
    print("🔍 Testing Email Extraction:")
    extracted_data = webhook_handler._extract_email_data(test_webhook_data)
    print(f"   Original 'from': {test_webhook_data['from']}")
    print(f"   Extracted sender: {extracted_data['sender']}")
    print(f"   Extracted name: {extracted_data['sender_name']}")
    print(f"   Full sender: {extracted_data['sender_full']}")
    print()
    
    # Verify the extraction is working
    if extracted_data['sender'] == "cvrcontractsltd@gmail.com":
        print("✅ Email extraction working correctly!")
    else:
        print(f"❌ Email extraction failed! Got: {extracted_data['sender']}")
        return
    
    print("🚀 Processing full webhook flow...")
    print()
    
    try:
        # Process the webhook
        result = await webhook_handler.process_webhook(test_webhook_data)
        
        print("✅ Webhook Processing Result:")
        print(json.dumps(result, indent=2))
        print()
        
        if result.get('success'):
            print("🎉 SUCCESS! Email processed completely")
            print(f"🎫 Ticket: {result.get('ticket_number', 'Unknown')}")
            print(f"📊 Airtable Record: {result.get('airtable_record_id', 'Unknown')}")
            print(f"🤖 AI Classification: {result.get('ai_classification', 'Unknown')}")
            print(f"📧 Email sent to: {extracted_data['sender']} (clean format)")
            print()
            print("🔔 Check SendGrid Activity Feed for delivery status:")
            print("   1. Login to SendGrid Dashboard")
            print("   2. Go to Activity Feed")
            print("   3. Look for 'Test Staffing Issue - Gmail Delivery Fix'")
            print("   4. Check if Gmail accepts it this time!")
            print()
            print("📊 Check Airtable for AI Summary and HR Categorization:")
            print("   - AI Summary should contain a concise summary of the staffing issue")
            print("   - Query Type should be categorized (likely 'General Inquiry' or 'Other')")
        else:
            print(f"❌ FAILED: {result.get('message', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_gmail_fix()) 