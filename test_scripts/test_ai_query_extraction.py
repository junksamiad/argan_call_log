#!/usr/bin/env python3
"""
Test script for AI query extraction functionality
Tests that the AI can extract clean customer queries from HTML when body_text is missing
"""

import asyncio
import json
import os
import sys
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.email_functions.classification.email_classifier_agent import EmailClassifierAgent


async def test_ai_query_extraction():
    """Test AI query extraction from HTML-only emails"""
    
    print("🧪 Testing AI Query Extraction")
    print("=" * 60)
    
    # Initialize AI classifier
    classifier = EmailClassifierAgent()
    
    # Test Case 1: HTML-only email (like ARG-20250601-0009)
    html_only_email = {
        'sender': 'test@example.com',
        'sender_name': 'Test User',
        'subject': 'Urgent HR Question',
        'recipients': ['hr@company.com'],
        'body_text': '',  # Empty plain text
        'body_html': '<div dir="auto">Can you help me understand the company leave policy? I need to take time off next month for a family emergency.</div>',
        'message_id': 'test_html_only_001',
        'email_date': datetime.utcnow().isoformat()
    }
    
    # Test Case 2: Complex HTML email
    complex_html_email = {
        'sender': 'employee@company.com',
        'sender_name': 'Jane Doe',
        'subject': 'Performance Review Question',
        'recipients': ['hr@company.com'],
        'body_text': '',  # Empty plain text
        'body_html': '''
        <div dir="ltr">
            <div>Hi HR Team,</div>
            <div><br></div>
            <div>I have a question about my upcoming performance review scheduled for next week.</div>
            <div><br></div>
            <div>Could you please clarify what documents I need to prepare and whether I should complete a self-assessment beforehand?</div>
            <div><br></div>
            <div>Thanks!</div>
            <div>Jane</div>
        </div>
        ''',
        'message_id': 'test_complex_html_002',
        'email_date': datetime.utcnow().isoformat()
    }
    
    # Test Case 3: Both HTML and text available
    both_formats_email = {
        'sender': 'manager@company.com',
        'sender_name': 'Bob Manager',
        'subject': 'Staff Training Query',
        'recipients': ['hr@company.com'],
        'body_text': 'What training programs are available for new hires?',
        'body_html': '<p>What training programs are available for new hires?</p>',
        'message_id': 'test_both_formats_003',
        'email_date': datetime.utcnow().isoformat()
    }
    
    test_cases = [
        ("HTML-only Email", html_only_email),
        ("Complex HTML Email", complex_html_email),
        ("Both Formats Email", both_formats_email)
    ]
    
    for test_name, email_data in test_cases:
        print(f"\n📧 TEST: {test_name}")
        print("-" * 40)
        
        try:
            # Classify the email
            result = await classifier.classify_email(email_data)
            
            # Extract the query
            extracted_query = result.EMAIL_DATA.query if hasattr(result, 'EMAIL_DATA') else "Not found"
            
            print(f"📄 Original body_text: '{email_data['body_text']}'")
            print(f"🌐 Original body_html: '{email_data['body_html'][:100]}...'")
            print(f"🤖 AI-extracted query: '{extracted_query}'")
            print(f"📊 AI classification: {result.EMAIL_CLASSIFICATION}")
            print(f"📈 Confidence: {result.confidence_score}")
            
            # Validate extraction success
            if extracted_query and extracted_query.strip() and extracted_query != "Not found":
                print("✅ Query extraction successful!")
            else:
                print("❌ Query extraction failed!")
                
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n🎯 AI Query Extraction testing completed!")


if __name__ == "__main__":
    asyncio.run(test_ai_query_extraction()) 