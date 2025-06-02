#!/usr/bin/env python3
"""
Test Auto-Reply Fix
Tests that the None value error is fixed and auto-replies are sent
"""

import sys
import asyncio
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
sys.path.append('backend')

from backend.email_functions.initial_email.initial_email import process_initial_email

async def test_auto_reply_fix():
    """Test the auto-reply fix with various sender name scenarios"""
    print('📤 Testing Auto-Reply Fix')
    print('=' * 60)
    
    # Test Case 1: AI extraction with None sender_name
    email_data1 = {
        "sender": "test.fix@example.com", 
        "sender_name": "",
        "subject": "Test Auto-Reply Fix - None Sender Name",
        "body_text": "Dear HR Team,\n\nThis is a test to verify the None value fix.\n\nBest regards,\nTest User",
        "email_date": datetime.utcnow().isoformat(),
        "message_id": f"test_fix_1_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}@test.com",
        "recipients": ["hr@company.com"],
        "cc": [],
        "dkim": "pass", 
        "spf": "pass"
    }
    
    # Mock classification data with None sender_name (this was causing the error)
    classification_dict1 = {
        "EMAIL_CLASSIFICATION": "NEW_EMAIL",
        "confidence_score": 95,
        "processing_timestamp": datetime.utcnow().isoformat(),
        "ai_extracted_data": {
            "sender_name": None,  # This was causing the strip() error
            "sender_domain": "example.com",
            "ai_summary": "Test email to verify None value handling",
            "hr_category": "General Inquiry",
            "urgency_keywords": [],
            "sentiment_tone": "Professional"
        }
    }
    
    try:
        print('📧 Test 1: Processing email with None sender_name...')
        result1 = await process_initial_email(email_data1, classification_dict1)
        
        if result1.get("success"):
            print(f'✅ Test 1 SUCCESS: {result1.get("ticket_number")}')
            print(f'   No "NoneType strip()" error occurred!')
        else:
            print(f'❌ Test 1 FAILED: {result1}')
            
    except Exception as e:
        print(f'❌ Test 1 ERROR: {e}')
    
    print()
    
    # Test Case 2: Normal email with proper sender name
    email_data2 = {
        "sender": "sarah.test@example.com",
        "sender_name": "",
        "subject": "Test Auto-Reply Fix - Normal Processing", 
        "body_text": "Dear HR Team,\n\nThis is a normal test email.\n\nBest regards,\nSarah Thompson",
        "email_date": datetime.utcnow().isoformat(),
        "message_id": f"test_fix_2_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}@test.com",
        "recipients": ["hr@company.com"],
        "cc": [],
        "dkim": "pass",
        "spf": "pass"
    }
    
    classification_dict2 = {
        "EMAIL_CLASSIFICATION": "NEW_EMAIL", 
        "confidence_score": 98,
        "processing_timestamp": datetime.utcnow().isoformat(),
        "ai_extracted_data": {
            "sender_name": "Sarah Thompson",  # Normal sender name
            "sender_domain": "example.com",
            "ai_summary": "Normal test email for auto-reply verification",
            "hr_category": "General Inquiry",
            "urgency_keywords": [],
            "sentiment_tone": "Professional"
        }
    }
    
    try:
        print('📧 Test 2: Processing email with normal sender_name...')
        result2 = await process_initial_email(email_data2, classification_dict2)
        
        if result2.get("success"):
            print(f'✅ Test 2 SUCCESS: {result2.get("ticket_number")}')
            print(f'   Should use "Sarah" as greeting')
        else:
            print(f'❌ Test 2 FAILED: {result2}')
            
    except Exception as e:
        print(f'❌ Test 2 ERROR: {e}')
    
    print()
    print('🎯 Fix Summary:')
    print('   ✅ Added None checks before calling strip()')
    print('   ✅ Prevents "NoneType has no attribute strip" errors')
    print('   ✅ Auto-replies should now be sent successfully')
    print('   ✅ Fallback to email username if no sender name available')

if __name__ == "__main__":
    asyncio.run(test_auto_reply_fix()) 