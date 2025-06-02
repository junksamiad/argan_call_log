#!/usr/bin/env python3
"""
Test script for Thread Parser AI Agent
Tests the fixed OpenAI Responses API integration
"""

import asyncio
import json
import os
import sys
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.email_functions.existing_email.thread_parser_ai import ThreadParserAI


def create_test_email_data():
    """Create sample email data with a simple thread"""
    return {
        "sender": "john.smith@company.com",
        "sender_name": "John Smith",
        "subject": "Re: ARG-20250531-0001 - Leave Request Follow-up",
        "recipients": ["hr@argan.com"],
        "message_id": "test_message_123",
        "email_date": "2025-01-06T15:30:00Z",
        "body_text": """Thanks for getting back to me about the medical leave.

I wanted to clarify - I'll need the leave starting January 15th, not January 1st as originally mentioned.

Please let me know if you need any additional documentation.

Best regards,
John

On 2025-01-06 at 10:15 AM, HR Support <hr@argan.com> wrote:
> Hi John,
> 
> We've received your medical leave request and are reviewing the documentation.
> Can you confirm the exact start date you need?
> 
> Best,
> HR Team

On 2025-01-05 at 2:30 PM, John Smith <john.smith@company.com> wrote:
>> I'm submitting a request for 6 weeks medical leave due to surgery.
>> I've attached the required medical documentation.
>> 
>> Please let me know the next steps.
>> 
>> Thanks,
>> John Smith""",
        "body_html": "<html>...</html>",
        "attachments": None
    }


async def test_thread_parser():
    """Test the Thread Parser AI agent"""
    print("🧵 Testing Thread Parser AI Agent...")
    print("=" * 50)
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key in the .env file")
        return False
    
    try:
        # Initialize the thread parser
        parser = ThreadParserAI()
        print("✅ Thread Parser AI initialized successfully")
        
        # Create test email data
        email_data = create_test_email_data()
        print(f"📧 Test email from: {email_data['sender']}")
        print(f"📧 Subject: {email_data['subject']}")
        
        # Parse the thread
        print("\n🔍 Parsing email thread...")
        messages = await parser.parse_email_thread(email_data)
        
        # Display results
        print(f"\n📊 Parsing Results:")
        print(f"📈 Extracted {len(messages)} messages from thread")
        
        for i, message in enumerate(messages, 1):
            print(f"\n--- Message {i} ---")
            print(f"Sender: {message['sender']}")
            print(f"Name: {message['sender_name']}")
            print(f"Timestamp: {message['timestamp']}")
            print(f"Type: {message['message_type']}")
            print(f"Source: {message['source']}")
            print(f"Content: {message['body_text'][:100]}...")
            print(f"Hash: {message['content_hash']}")
        
        # Validate results
        print(f"\n🧪 Validation:")
        
        if len(messages) >= 1:
            print("✅ Successfully extracted at least one message")
        else:
            print("❌ No messages extracted")
            return False
        
        # Check for proper structure
        required_fields = ['sender', 'timestamp', 'body_text', 'message_type', 'content_hash']
        for message in messages:
            missing_fields = [field for field in required_fields if field not in message]
            if missing_fields:
                print(f"❌ Missing fields in message: {missing_fields}")
                return False
        
        print("✅ All messages have required fields")
        
        # Check chronological order
        timestamps = [message['timestamp'] for message in messages]
        if timestamps == sorted(timestamps):
            print("✅ Messages are in chronological order")
        else:
            print("⚠️ Messages may not be in chronological order")
        
        print("\n🎉 Thread Parser test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during thread parsing test: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_simple_email():
    """Test with a simple single-message email"""
    print("\n🧵 Testing with simple email (no thread)...")
    
    simple_email = {
        "sender": "employee@company.com",
        "sender_name": "Test Employee",
        "subject": "Re: ARG-20250531-0002 - Quick Question",
        "recipients": ["hr@argan.com"],
        "message_id": "simple_test_456",
        "email_date": "2025-01-06T16:00:00Z",
        "body_text": "Just wanted to follow up on my previous question about vacation policies. When can I expect a response?",
        "body_html": "",
        "attachments": None
    }
    
    try:
        parser = ThreadParserAI()
        messages = await parser.parse_email_thread(simple_email)
        
        print(f"📊 Simple email parsing: {len(messages)} message(s) extracted")
        
        if len(messages) == 1:
            print("✅ Correctly identified as single message")
            message = messages[0]
            print(f"   Sender: {message['sender']}")
            print(f"   Content: {message['body_text'][:50]}...")
            return True
        else:
            print(f"⚠️ Expected 1 message, got {len(messages)}")
            return False
            
    except Exception as e:
        print(f"❌ Error in simple email test: {e}")
        return False


async def main():
    """Run all thread parser tests"""
    print("🚀 Starting Thread Parser AI Tests")
    print("=" * 60)
    
    # Test 1: Complex thread parsing
    test1_result = await test_thread_parser()
    
    # Test 2: Simple email parsing
    test2_result = await test_simple_email()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Summary:")
    print(f"   Complex Thread Test: {'✅ PASSED' if test1_result else '❌ FAILED'}")
    print(f"   Simple Email Test:   {'✅ PASSED' if test2_result else '❌ FAILED'}")
    
    if test1_result and test2_result:
        print("\n🎉 All Thread Parser tests PASSED!")
        print("The Thread Parser AI is working correctly with the Responses API.")
    else:
        print("\n❌ Some tests FAILED!")
        print("Please check the error messages above.")


if __name__ == "__main__":
    asyncio.run(main()) 