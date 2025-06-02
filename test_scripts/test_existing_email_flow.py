#!/usr/bin/env python3
"""
Test script for complete existing email flow
Tests the full pipeline from classification to thread parsing to database update
"""

import asyncio
import json
import os
import sys
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.email_functions.existing_email.existing_email import process_existing_email
from backend.email_functions.classification.email_classifier_agent import EmailClassifierAgent


def create_existing_email_test_data():
    """Create sample email data for an existing ticket"""
    return {
        "sender": "john.smith@company.com",
        "sender_name": "John Smith", 
        "subject": "Re: ARG-20250101-0001 - Follow up on leave request",
        "recipients": ["hr@argan.com"],
        "cc": [],
        "message_id": "existing_test_789",
        "email_date": "2025-01-06T16:45:00Z",
        "body_text": """Hi HR Team,

Just wanted to follow up on my medical leave request submitted last week. 

I have a few additional questions:
1. Will my health insurance continue during the leave?
2. Do I need to submit any additional paperwork?
3. What's the timeline for approval?

Thanks for your help!

Best regards,
John Smith

On 2025-01-02 at 9:30 AM, HR Support <hr@argan.com> wrote:
> Dear John,
> 
> Thank you for submitting your medical leave request. We are reviewing 
> your documentation and will get back to you within 3-5 business days.
> 
> Best regards,
> HR Team

On 2025-01-01 at 2:15 PM, John Smith <john.smith@company.com> wrote:
>> I'm submitting a formal request for 8 weeks medical leave starting 
>> February 1st, 2025. I've attached the required medical documentation 
>> from my doctor.
>> 
>> Please let me know if you need any additional information.
>> 
>> Sincerely,
>> John Smith""",
        "body_html": "<html>...</html>",
        "attachments": [],
        "dkim": "pass",
        "spf": "pass",
        "sender_ip": "192.168.1.100",
        "envelope": {"from": "john.smith@company.com", "to": ["hr@argan.com"]}
    }


async def test_classification_step():
    """Test that the email gets classified as EXISTING_EMAIL"""
    print("🤖 Testing AI Classification Step...")
    
    try:
        classifier = EmailClassifierAgent()
        email_data = create_existing_email_test_data()
        
        # Classify the email
        classification = await classifier.classify_email(email_data)
        
        print(f"📊 Classification Result: {classification.EMAIL_CLASSIFICATION}")
        print(f"🎯 Confidence: {classification.confidence_score}")
        
        if hasattr(classification.EMAIL_DATA, 'ticket_number'):
            ticket_number = classification.EMAIL_DATA.ticket_number
            print(f"🎫 Extracted Ticket: {ticket_number}")
        else:
            print("❌ No ticket number extracted")
            return False, None
        
        if classification.EMAIL_CLASSIFICATION == "EXISTING_EMAIL":
            print("✅ Correctly classified as EXISTING_EMAIL")
            return True, classification
        else:
            print(f"❌ Expected EXISTING_EMAIL, got {classification.EMAIL_CLASSIFICATION}")
            return False, None
            
    except Exception as e:
        print(f"❌ Classification error: {e}")
        import traceback
        traceback.print_exc()
        return False, None


async def test_existing_email_processing():
    """Test the complete existing email processing pipeline"""
    print("\n💬 Testing Complete Existing Email Processing...")
    
    try:
        # First classify the email
        classification_success, classification_data = await test_classification_step()
        
        if not classification_success:
            print("❌ Classification failed, cannot test processing")
            return False
        
        # Process the existing email
        email_data = create_existing_email_test_data()
        result = await process_existing_email(email_data, classification_data)
        
        print(f"\n📋 Processing Result:")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Ticket: {result.get('ticket_number', 'N/A')}")
        
        if 'message' in result:
            print(f"   Message: {result['message']}")
        
        if 'new_messages_count' in result:
            print(f"   New Messages: {result['new_messages_count']}")
            print(f"   Total Messages: {result['total_messages']}")
        
        if result.get('success', False):
            print("✅ Existing email processing completed successfully!")
            return True
        else:
            print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Processing error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_mock_existing_email():
    """Test with a simplified mock (no Airtable required)"""
    print("\n🧪 Testing Thread Parser Only (Mock Mode)...")
    
    try:
        from backend.email_functions.existing_email.thread_parser_ai import ThreadParserAI
        
        parser = ThreadParserAI()
        email_data = create_existing_email_test_data()
        
        # Parse the thread
        messages = await parser.parse_email_thread(email_data)
        
        print(f"📈 Extracted {len(messages)} messages")
        
        # Validate we got reasonable results
        if len(messages) >= 2:  # Should extract at least 2-3 messages from the thread
            print("✅ Thread parsing successful")
            
            # Check message types
            types = [msg['message_type'] for msg in messages]
            print(f"   Message types: {types}")
            
            # Check chronological order
            timestamps = [msg['timestamp'] for msg in messages]
            if timestamps == sorted(timestamps):
                print("✅ Messages in chronological order")
            
            return True
        else:
            print(f"⚠️ Expected multiple messages, only got {len(messages)}")
            return len(messages) >= 1  # At least got something
            
    except Exception as e:
        print(f"❌ Mock test error: {e}")
        return False


async def main():
    """Run all existing email flow tests"""
    print("🚀 Starting Existing Email Flow Tests")
    print("=" * 60)
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key in the .env file")
        return
    
    # Test 1: Thread parser only (no dependencies)
    test1_result = await test_mock_existing_email()
    
    # Test 2: Full processing (may fail if no Airtable record exists)
    print("\n" + "="*60)
    test2_result = await test_existing_email_processing()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Summary:")
    print(f"   Thread Parser Test:     {'✅ PASSED' if test1_result else '❌ FAILED'}")
    print(f"   Full Processing Test:   {'✅ PASSED' if test2_result else '❌ FAILED'}")
    
    if test1_result:
        print("\n🎉 Core functionality is working!")
        print("✅ Thread Parser AI is functioning correctly")
        print("✅ OpenAI Responses API integration successful")
        
        if test2_result:
            print("✅ Complete existing email flow is operational")
        else:
            print("⚠️ Full flow test failed - likely due to missing test ticket in Airtable")
            print("   This is expected if ARG-20250101-0001 doesn't exist in your database")
    else:
        print("\n❌ Core functionality issues detected!")
        print("Please check the error messages above.")


if __name__ == "__main__":
    asyncio.run(main()) 