#!/usr/bin/env python3
"""
Test Deduplication Fix
Tests that duplicate emails are properly detected and handled
"""

import sys
import asyncio
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
sys.path.append('backend')

from backend.email_functions.initial_email.initial_email import process_initial_email

async def test_deduplication_fix():
    """Test the deduplication logic"""
    print('🔄 Testing Email Deduplication Fix')
    print('=' * 60)
    
    # Create test email data
    email_data = {
        "sender": "test.dedup@example.com",
        "sender_name": "",
        "subject": "Test Deduplication - Sarah Thompson Query",
        "body_text": "Dear HR Team,\n\nThis is a test to ensure deduplication works properly.\n\nBest regards,\nSarah Thompson",
        "email_date": datetime.utcnow().isoformat(),
        "message_id": f"test_dedup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}@test.com",
        "recipients": ["hr@company.com"],
        "cc": [],
        "dkim": "pass",
        "spf": "pass"
    }
    
    # Mock AI classification data with proper sender name
    class MockEmailData:
        def __init__(self):
            self.sender_name = "Sarah Thompson"
            self.sender_domain = "example.com"
            self.ai_summary = "Test email to verify deduplication logic works correctly"
            self.hr_category = "General Inquiry"
            self.urgency_keywords = []
            self.sentiment_tone = "Professional"
    
    class MockClassificationData:
        def __init__(self):
            self.EMAIL_CLASSIFICATION = "NEW_EMAIL"
            self.confidence_score = 95
            self.processing_timestamp = datetime.utcnow().isoformat()
            self.EMAIL_DATA = MockEmailData()
    
    # Convert to dict format for compatibility
    classification_dict = {
        "EMAIL_CLASSIFICATION": "NEW_EMAIL",
        "confidence_score": 95,
        "processing_timestamp": datetime.utcnow().isoformat(),
        "ai_extracted_data": {
            "sender_name": "Sarah Thompson",
            "sender_domain": "example.com",
            "ai_summary": "Test email to verify deduplication logic works correctly",
            "hr_category": "General Inquiry",
            "urgency_keywords": [],
            "sentiment_tone": "Professional"
        }
    }
    
    try:
        print('📧 Processing email first time...')
        result1 = await process_initial_email(email_data, classification_dict)
        
        if result1.get("success"):
            ticket1 = result1.get("ticket_number")
            print(f'✅ First processing successful: {ticket1}')
            print(f'   Duplicate detected: {result1.get("duplicate_detected", False)}')
        else:
            print(f'❌ First processing failed: {result1}')
            return
        
        print()
        print('📧 Processing same email again (should detect duplicate)...')
        result2 = await process_initial_email(email_data, classification_dict)
        
        if result2.get("success"):
            ticket2 = result2.get("ticket_number")
            duplicate_detected = result2.get("duplicate_detected", False)
            
            print(f'✅ Second processing result: {ticket2}')
            print(f'   Duplicate detected: {duplicate_detected}')
            
            if duplicate_detected and ticket1 == ticket2:
                print('🎉 SUCCESS: Deduplication working correctly!')
                print(f'   Same ticket returned: {ticket1} = {ticket2}')
                print(f'   No duplicate record created')
            else:
                print('❌ FAILURE: Deduplication not working')
                print(f'   Expected duplicate detection: True, got: {duplicate_detected}')
                print(f'   Expected same ticket: {ticket1} = {ticket2}')
        else:
            print(f'❌ Second processing failed: {result2}')
        
        print()
        print('📊 Summary:')
        print(f'   This fix should prevent duplicate records like:')
        print(f'   ARG-20250601-0001 (with AI data, no auto-reply)')
        print(f'   ARG-20250601-0002 (no AI data, with auto-reply)')
        print(f'   ')
        print(f'   Instead, we get:')
        print(f'   Single record with both AI data AND auto-reply')
        print(f'   Auto-reply uses proper sender name from AI extraction')
        
    except Exception as e:
        print(f'❌ Test failed: {e}')

if __name__ == "__main__":
    asyncio.run(test_deduplication_fix()) 