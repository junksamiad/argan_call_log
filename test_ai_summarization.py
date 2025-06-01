#!/usr/bin/env python3
"""
Test AI Summarization and HR Categorization
Tests the enhanced AI classifier with summarization and categorization features
"""

import asyncio
import json
import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.append('backend')

from backend.email_functions.classification.email_classifier_agent import EmailClassifierAgent

async def test_ai_summarization():
    """Test AI summarization and HR categorization with sample emails"""
    
    # Load environment variables
    load_dotenv()
    
    print("🧪 Testing AI Summarization & HR Categorization")
    print("=" * 60)
    
    # Initialize AI classifier
    classifier = EmailClassifierAgent()
    
    # Test cases with different HR scenarios
    test_emails = [
        {
            "name": "Leave Request",
            "email_data": {
                "sender": "sarah.jones@company.com",
                "sender_name": "Sarah Jones",
                "subject": "Maternity Leave Request",
                "body_text": "Hi HR Team,\n\nI hope this email finds you well. I am writing to formally request maternity leave as I am expecting my first child. My due date is March 15, 2025, and I would like to start my leave on March 1, 2025.\n\nI plan to take the full 12 weeks of FMLA leave and would like to discuss my options for additional unpaid leave if needed. I have already spoken with my manager about coverage for my responsibilities during my absence.\n\nPlease let me know what documentation you need from me and when we can schedule a meeting to discuss the details.\n\nThank you,\nSarah",
                "message_id": "test-leave-001",
                "email_date": "2025-01-15T10:30:00Z",
                "recipients": ["hr@arganconsultancy.com"],
                "cc": [],
                "dkim": "pass",
                "spf": "pass"
            }
        },
        {
            "name": "Workplace Complaint",
            "email_data": {
                "sender": "michael.brown@company.com",
                "sender_name": "Michael Brown",
                "subject": "URGENT: Workplace Harassment Issue",
                "body_text": "Dear HR,\n\nI need to report a serious workplace harassment issue that occurred today. My supervisor, Jane Smith, made inappropriate comments about my personal appearance and made unwelcome advances during our one-on-one meeting this afternoon.\n\nThis is not the first time this has happened, but today it crossed a line that made me very uncomfortable. I have documented the incidents with dates and times.\n\nI need immediate assistance with this matter as I'm concerned about retaliation. Please contact me as soon as possible to discuss next steps.\n\nRegards,\nMichael Brown\nAccounting Department",
                "message_id": "test-complaint-001",
                "email_date": "2025-01-15T16:45:00Z",
                "recipients": ["hr@arganconsultancy.com"],
                "cc": [],
                "dkim": "pass",
                "spf": "pass"
            }
        },
        {
            "name": "Benefits Question",
            "email_data": {
                "sender": "newemployee@company.com",
                "sender_name": "Alex Chen",
                "subject": "Questions about Health Insurance Enrollment",
                "body_text": "Hello,\n\nI'm a new employee starting next Monday and I have some questions about the health insurance enrollment process. I received the benefits package but I'm confused about the different plan options.\n\nSpecifically, I'd like to know:\n1. What's the difference between Plan A and Plan B?\n2. Can I add my spouse and children to the coverage?\n3. When is the enrollment deadline?\n4. Are there any pre-existing condition waiting periods?\n\nI'd appreciate if someone could schedule a call to walk me through the options or send me additional information.\n\nThanks,\nAlex Chen",
                "message_id": "test-benefits-001",
                "email_date": "2025-01-15T09:15:00Z",
                "recipients": ["hr@arganconsultancy.com"],
                "cc": [],
                "dkim": "pass",
                "spf": "pass"
            }
        }
    ]
    
    # Test each email
    for i, test_case in enumerate(test_emails, 1):
        print(f"\n📧 Test Case {i}: {test_case['name']}")
        print("-" * 40)
        
        try:
            # Classify the email
            result = await classifier.classify_email(test_case['email_data'])
            
            # Extract the AI analysis
            ai_data = result.EMAIL_DATA
            
            print(f"✅ Classification: {result.EMAIL_CLASSIFICATION}")
            print(f"🤖 AI Confidence: {result.confidence_score}")
            print(f"📝 AI Summary: {ai_data.ai_summary}")
            print(f"🏢 HR Category: {ai_data.hr_category}")
            print(f"😊 Sentiment: {ai_data.sentiment_tone}")
            
            if ai_data.urgency_keywords_list != "[]" and ai_data.urgency_keywords_list:
                try:
                    urgency = json.loads(ai_data.urgency_keywords_list)
                    print(f"🚨 Urgency Keywords: {urgency}")
                except:
                    print(f"🚨 Urgency Keywords: {ai_data.urgency_keywords_list}")
            
            if result.notes:
                print(f"📋 AI Notes: {result.notes}")
                
        except Exception as e:
            print(f"❌ Error testing {test_case['name']}: {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    print("=" * 60)
    print("✅ AI Summarization Testing Complete!")

if __name__ == "__main__":
    asyncio.run(test_ai_summarization()) 