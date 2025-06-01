#!/usr/bin/env python3
"""
Test Real Query Summarization
Test AI summarization with the actual email content that was sent to the system
"""

import asyncio
import json
import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.append('backend')

from backend.email_functions.classification.email_classifier_agent import EmailClassifierAgent

async def test_real_query():
    """Test AI summarization with the actual care home email content"""
    
    # Load environment variables
    load_dotenv()
    
    print("🧪 Testing AI Summarization with Real Care Home Query")
    print("=" * 70)
    
    # Initialize AI classifier
    classifier = EmailClassifierAgent()
    
    # The actual email content from the user
    real_email_data = {
        "sender": "cvrcontractsltd@gmail.com",
        "sender_name": "cvrcontractsltd",
        "subject": "Concern Regarding Punctuality and Performance of Care Assistant",
        "body_text": """Dear HR Team,

I hope you are well. I am writing to seek your advice on an ongoing issue with one of our care assistants, Ms Jane Smith, who has recently shown a pattern of late arrivals and noticeably reduced performance during shifts. Over the past six weeks, Jane has arrived late on seven occasions—sometimes by as much as 45 minutes—which has disrupted staff rotas and affected continuity of care for our residents. Additionally, her daily care notes have become increasingly sparse, and I have received informal feedback from senior carers that she appears distracted and unengaged with residents' personal care routines.

To give you a clearer picture:

Attendance records: Jane's timecard shows lateness on 15 April (30 minutes late), 18 April (20 minutes late), 22 April (45 minutes late), and four further instances in May. On one occasion, she left an early evening shift 1 hour before her scheduled finish without prior approval.
Performance observations: During spot checks on 8 May and 15 May, I observed that Jane skirted key duties—such as assistance with mealtimes and medication rounds—and deferred tasks to other staff without explanation. She also failed to complete important daily logs for two residents with complex care needs.
Informal conversations: I have spoken with Jane twice (on 10 May and 20 May) to remind her of our expectations. She cited "personal issues" but did not offer any details. She has declined to discuss any support she might need.

I am concerned that if this pattern continues, it will not only jeopardise the quality of care we provide but also place unfair burden on her colleagues. At present, I am unsure whether to initiate a formal performance improvement plan (PIP) or first hold a disciplinary hearing. Before taking any formal steps, I would appreciate your guidance on:

The correct sequence for issuing informal warnings versus moving straight to a formal written warning under our disciplinary policy.
Whether we need to offer any additional support—such as an occupational health referral or counselling—before commencing formal proceedings.
The documentation required to ensure our process remains fair and compliant with statutory regulations (e.g., ACAS Code of Practice).
Suggested wording for an invitation to a formal performance review meeting, should that be necessary.

I have attached copies of her timecard reports, notes from our meetings, and the draft PIP template we use. Please let me know if any further documentation is needed. I would appreciate your advice at your earliest convenience, ideally by the end of this week, so that we can address the matter promptly.

Thank you for your support.

Kind regards,

Sarah Thompson
Home Manager
Willow Grove Care Home
Tel: 020 7946 0857""",
        "message_id": "real-care-home-001",
        "email_date": "2025-06-01T10:30:00Z",
        "recipients": ["hr@arganconsultancy.com"],
        "cc": [],
        "dkim": "pass",
        "spf": "pass"
    }
    
    print(f"📧 From: {real_email_data['sender']}")
    print(f"📝 Subject: {real_email_data['subject']}")
    print(f"📄 Body Length: {len(real_email_data['body_text'])} characters")
    print()
    
    try:
        # Classify the email with AI
        result = await classifier.classify_email(real_email_data)
        
        # Extract the AI analysis
        ai_data = result.EMAIL_DATA
        
        print("🤖 AI ANALYSIS RESULTS:")
        print("-" * 40)
        print(f"✅ Classification: {result.EMAIL_CLASSIFICATION}")
        print(f"🤖 AI Confidence: {result.confidence_score}")
        print()
        print(f"📝 AI Summary:")
        print(f"   {ai_data.ai_summary}")
        print()
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
        
        print()
        print("🎯 EXPECTED RESULTS:")
        print("- Category should be 'Complaint' or 'Policy Question'")
        print("- Summary should mention performance issues, care assistant, disciplinary guidance")
        print("- Should detect urgency (end of week deadline)")
        print("- Should identify this as a management/HR policy query")
        
    except Exception as e:
        print(f"❌ Error testing real query: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_real_query()) 