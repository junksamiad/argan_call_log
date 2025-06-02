"""
Test script for AI Email Classification System
Tests the new AI classifier with sample email data
"""

import asyncio
import os
import sys
import logging
from datetime import datetime

# Add backend to path
sys.path.append('backend')

from backend.email_functions.classification import EmailClassifierAgent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_ai_classifier():
    """Test the AI classifier with sample email data"""
    
    print("🤖 Testing AI Email Classification System")
    print("=" * 50)
    
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ ERROR: OPENAI_API_KEY not found in environment variables")
        print("Please set your OpenAI API key in .env file or environment")
        return
    
    # Initialize the classifier
    classifier = EmailClassifierAgent()
    
    # Test Case 1: New Email (should be classified as NEW_EMAIL)
    print("\n📧 Test Case 1: New Email Query")
    print("-" * 30)
    
    new_email_data = {
        'sender': 'john.doe@company.com',
        'sender_name': 'John Doe',
        'subject': 'Question about annual leave policy',
        'body_text': 'Hi, I have a question about the annual leave policy. How many days am I entitled to this year? Thanks, John',
        'body_html': '<p>Hi, I have a question about the annual leave policy. How many days am I entitled to this year?</p><p>Thanks, John</p>',
        'message_id': 'test-new-email-001',
        'email_date': datetime.now().isoformat(),
        'recipients': ['hr@arganconsultancy.com'],
        'cc': [],
        'dkim': 'pass',
        'spf': 'pass'
    }
    
    try:
        result1 = await classifier.classify_email(new_email_data)
        print(f"Classification: {result1.EMAIL_CLASSIFICATION}")
        print(f"Sender: {result1.EMAIL_DATA.sender_email}")
        print(f"Subject: {result1.EMAIL_DATA.subject}")
        print(f"Ticket Number: {result1.EMAIL_DATA.ticket_number}")
        print(f"Confidence: {result1.confidence_score}")
        print(f"Notes: {result1.notes}")
    except Exception as e:
        print(f"❌ Error in Test Case 1: {e}")
    
    # Test Case 2: Existing Email with Ticket (should be classified as EXISTING_EMAIL)
    print("\n📧 Test Case 2: Reply to Existing Ticket")
    print("-" * 30)
    
    existing_email_data = {
        'sender': 'john.doe@company.com',
        'sender_name': 'John Doe',
        'subject': 'Re: [ARG-20250531-0001] Question about annual leave policy',
        'body_text': 'Thanks for the information. I have one more question - can I carry over unused days to next year?',
        'body_html': '<p>Thanks for the information. I have one more question - can I carry over unused days to next year?</p>',
        'message_id': 'test-existing-email-001',
        'email_date': datetime.now().isoformat(),
        'recipients': ['hr@arganconsultancy.com'],
        'cc': [],
        'dkim': 'pass',
        'spf': 'pass'
    }
    
    try:
        result2 = await classifier.classify_email(existing_email_data)
        print(f"Classification: {result2.EMAIL_CLASSIFICATION}")
        print(f"Sender: {result2.EMAIL_DATA.sender_email}")
        print(f"Subject: {result2.EMAIL_DATA.subject}")
        print(f"Ticket Number: {result2.EMAIL_DATA.ticket_number}")
        print(f"Ticket Found In: {result2.EMAIL_DATA.ticket_found_in}")
        print(f"Confidence: {result2.confidence_score}")
        print(f"Notes: {result2.notes}")
    except Exception as e:
        print(f"❌ Error in Test Case 2: {e}")
    
    # Test Case 3: Edge case - Ticket in body but not subject
    print("\n📧 Test Case 3: Ticket Number in Body")
    print("-" * 30)
    
    edge_case_data = {
        'sender': 'jane.smith@company.com',
        'sender_name': 'Jane Smith',
        'subject': 'Follow up on my request',
        'body_text': 'Hi, I wanted to follow up on my previous request. My ticket number was ARG-20250531-0002. Any updates?',
        'body_html': '<p>Hi, I wanted to follow up on my previous request. My ticket number was ARG-20250531-0002. Any updates?</p>',
        'message_id': 'test-edge-case-001',
        'email_date': datetime.now().isoformat(),
        'recipients': ['hr@arganconsultancy.com'],
        'cc': [],
        'dkim': 'pass',
        'spf': 'pass'
    }
    
    try:
        result3 = await classifier.classify_email(edge_case_data)
        print(f"Classification: {result3.EMAIL_CLASSIFICATION}")
        print(f"Sender: {result3.EMAIL_DATA.sender_email}")
        print(f"Subject: {result3.EMAIL_DATA.subject}")
        print(f"Ticket Number: {result3.EMAIL_DATA.ticket_number}")
        print(f"Ticket Found In: {result3.EMAIL_DATA.ticket_found_in}")
        print(f"Confidence: {result3.confidence_score}")
        print(f"Urgency Keywords: {result3.EMAIL_DATA.urgency_keywords_list}")
    except Exception as e:
        print(f"❌ Error in Test Case 3: {e}")
    
    print("\n✅ AI Classification Tests Complete!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_ai_classifier()) 