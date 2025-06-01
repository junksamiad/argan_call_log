"""
Complete Email Processing Pipeline Test
Tests the entire flow: Email Data → AI Classification → Airtable Storage
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.email_functions.email_router import route_email_async
from backend.airtable_service import AirtableService


async def test_complete_pipeline():
    """Test the complete email processing pipeline"""
    
    print("🧪 COMPLETE EMAIL PIPELINE TEST")
    print("=" * 60)
    
    # Mock email data - realistic care home scenario
    mock_email_data = {
        'sender': 'manager@sunshinecare.co.uk',
        'sender_name': 'Sarah Williams',
        'subject': 'Urgent: Staff Performance Issue Requiring HR Guidance',
        'body_text': '''Dear HR Team,

I hope you are well. I am writing to seek your urgent advice on an ongoing issue with one of our care assistants, Ms Jane Smith, who has recently shown a pattern of late arrivals and noticeable decline in work performance.

Over the past three weeks, Ms Smith has:
- Arrived late to her shifts on five occasions (15-45 minutes late)
- Appeared disengaged during shifts according to staff feedback
- Missed important care tasks documented in resident care plans
- Failed to respond to informal coaching attempts

This situation is affecting both resident care quality and team morale. I have spoken with Ms Smith informally about these concerns, but there has been no improvement. 

Could you please advise on the appropriate next steps? Should we initiate a formal disciplinary process, and if so, what documentation do I need to prepare? I want to ensure we handle this sensitively but maintain our high standards of care.

I would appreciate your guidance on this matter at your earliest convenience, as it is affecting the quality of care we provide to our residents. Please respond by end of week if possible.

Thank you for your time and assistance.

Best regards,
Sarah Williams
Home Manager
Sunshine Care Home
sarah.williams@sunshinecare.co.uk
01234 567890''',
        'body_html': '<p>Dear HR Team...</p>',  # Simplified HTML
        'recipients': ['email@email.adaptixinnovation.co.uk'],
        'cc': [],
        'message_id': 'test-pipeline-123',
        'email_date': '2024-06-01T15:30:00Z',
        'dkim': 'pass',
        'spf': 'pass',
        'attachments': []
    }
    
    print("📧 Mock Email Data:")
    print(f"   From: {mock_email_data['sender']}")
    print(f"   Subject: {mock_email_data['subject']}")
    print(f"   Body Length: {len(mock_email_data['body_text'])} characters")
    print()
    
    try:
        print("🤖 Step 1: Processing through Email Router (with AI Classification)...")
        result = await route_email_async(mock_email_data)
        
        if result.get('success'):
            print("✅ Email processing successful!")
            print(f"   Ticket Number: {result.get('ticket_number')}")
            print(f"   AI Classification: {result.get('ai_classification')}")
            print(f"   AI Confidence: {result.get('ai_confidence')}")
            print(f"   Airtable Record ID: {result.get('airtable_record_id')}")
            print()
            
            print("📊 Step 2: Checking Airtable Record...")
            airtable = AirtableService()
            record_id = result.get('airtable_record_id')
            
            if record_id:
                # Get the record from Airtable
                records = airtable.table.all()
                if records:
                    latest_record = records[-1]
                    fields = latest_record['fields']
                    
                    print("✅ Airtable Record Retrieved:")
                    print(f"   Record ID: {latest_record['id']}")
                    
                    # Check AI fields specifically
                    ai_fields = {
                        'AI Summary': fields.get('AI Summary', 'MISSING'),
                        'Query Type': fields.get('Query Type', 'MISSING'), 
                        'HR Category': fields.get('HR Category', 'MISSING'),
                        'Sentiment Tone': fields.get('Sentiment Tone', 'MISSING'),
                        'AI Confidence': fields.get('AI Confidence', 'MISSING'),
                        'Urgency Keywords': fields.get('Urgency Keywords', 'MISSING')
                    }
                    
                    print("\n🤖 AI PROCESSING RESULTS:")
                    print("-" * 40)
                    for field, value in ai_fields.items():
                        status = "✅" if value != 'MISSING' and value != '' else "❌"
                        display_value = str(value)[:80] + "..." if len(str(value)) > 80 else str(value)
                        print(f"{status} {field}: {display_value}")
                    
                    # Check if we have the critical fields
                    has_summary = fields.get('AI Summary') and fields.get('AI Summary').strip()
                    has_category = fields.get('Query Type') and fields.get('Query Type').strip()
                    
                    print(f"\n📋 CRITICAL FIELDS STATUS:")
                    print(f"   AI Summary: {'✅ POPULATED' if has_summary else '❌ MISSING'}")
                    print(f"   HR Category: {'✅ POPULATED' if has_category else '❌ MISSING'}")
                    
                    if has_summary and has_category:
                        print("\n🎉 SUCCESS: All AI fields are working correctly!")
                        print(f"   Summary: {fields.get('AI Summary')[:100]}...")
                        print(f"   Category: {fields.get('Query Type')}")
                    else:
                        print("\n⚠️  ISSUE: Some AI fields are missing")
                        
                    # Check conversation history
                    conv_history = fields.get('Conversation History', '')
                    if conv_history and conv_history != '[]':
                        print(f"   Conversation History: ✅ POPULATED ({len(conv_history)} chars)")
                    else:
                        print(f"   Conversation History: ❌ EMPTY (expected for new emails)")
                        
                else:
                    print("❌ No records found in Airtable")
            else:
                print("❌ No record ID returned from processing")
                
        else:
            print("❌ Email processing failed:")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            print(f"   Message: {result.get('message', 'No message')}")
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Starting complete pipeline test...")
    asyncio.run(test_complete_pipeline()) 