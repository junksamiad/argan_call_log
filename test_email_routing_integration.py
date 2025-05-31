"""
Integration test for the complete email routing system with AI classification
Tests the entire flow from email input to handler routing
"""

import asyncio
import os
import sys
import logging
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import json
from backend.email_functions.webhook_handler import WebhookHandler

# Add backend to path
sys.path.append('backend')

from backend.database import Base
from backend.email_functions.email_router import EmailRouter
from backend.email_functions.auto_reply import send_auto_reply

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_complete_email_routing():
    """Test the complete email routing system with AI classification"""
    
    print("🔄 Testing Complete Email Routing with AI Classification")
    print("=" * 60)
    
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ ERROR: OPENAI_API_KEY not found in environment variables")
        print("Please create a .env file with your OpenAI API key")
        print("Example: echo 'OPENAI_API_KEY=sk-...' > .env")
        return
    
    # Set up test database
    engine = create_engine("sqlite:///test_email_routing.db", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_session = SessionLocal()
    
    try:
        # Initialize the email router
        router = EmailRouter(db_session)
        
        # Test Case 1: New Email (should go to initial email handler)
        print("\n📧 Test Case 1: New Email (Should create new ticket)")
        print("-" * 50)
        
        new_email = {
            'sender': 'employee@testcompany.com',
            'sender_name': 'Test Employee',
            'subject': 'Urgent: Question about maternity leave policy',
            'body_text': 'Hi HR team, I need urgent information about maternity leave policy. When can I start my leave? This is time-sensitive as my due date is approaching.',
            'body_html': '<p>Hi HR team, I need urgent information about maternity leave policy. When can I start my leave? This is time-sensitive as my due date is approaching.</p>',
            'message_id': 'test-integration-new-001',
            'email_date': datetime.now().isoformat(),
            'recipients': ['hr@arganconsultancy.com'],
            'cc': [],
            'dkim': 'pass',
            'spf': 'pass'
        }
        
        try:
            result1 = await router.route_email(new_email)
            print(f"✅ Routing Result:")
            print(f"   Success: {result1.get('success')}")
            print(f"   Ticket Number: {result1.get('ticket_number')}")
            print(f"   Message: {result1.get('message')}")
            print(f"   Auto-reply Sent: {result1.get('auto_reply_sent')}")
        except Exception as e:
            print(f"❌ Error in Test Case 1: {e}")
        
        # Test Case 2: Reply to Existing Ticket
        print("\n📧 Test Case 2: Reply to Existing Ticket")
        print("-" * 50)
        
        reply_email = {
            'sender': 'employee@testcompany.com',
            'sender_name': 'Test Employee',
            'subject': 'Re: [ARG-20250531-0001] Question about maternity leave policy',
            'body_text': 'Thank you for the quick response. I have one follow-up question: do I need to provide any documentation before starting my leave?',
            'body_html': '<p>Thank you for the quick response. I have one follow-up question: do I need to provide any documentation before starting my leave?</p>',
            'message_id': 'test-integration-reply-001',
            'email_date': datetime.now().isoformat(),
            'recipients': ['hr@arganconsultancy.com'],
            'cc': [],
            'dkim': 'pass',
            'spf': 'pass'
        }
        
        try:
            result2 = await router.route_email(reply_email)
            print(f"✅ Routing Result:")
            print(f"   Success: {result2.get('success')}")
            print(f"   Ticket Number: {result2.get('ticket_number')}")
            print(f"   Action: {result2.get('action')}")
            print(f"   AI Enhanced: {result2.get('ai_enhanced')}")
            print(f"   Urgency Detected: {result2.get('urgency_detected')}")
            print(f"   Sentiment: {result2.get('sentiment')}")
        except Exception as e:
            print(f"❌ Error in Test Case 2: {e}")
        
        # Test Case 3: Email with ticket in body (edge case)
        print("\n📧 Test Case 3: Ticket Reference in Body Text")
        print("-" * 50)
        
        edge_case_email = {
            'sender': 'manager@testcompany.com',
            'sender_name': 'Test Manager',
            'subject': 'Follow up on employee request',
            'body_text': 'Hi HR, I wanted to follow up on the employee request with ticket ARG-20250531-0001. Can you provide an update on the status?',
            'body_html': '<p>Hi HR, I wanted to follow up on the employee request with ticket ARG-20250531-0001. Can you provide an update on the status?</p>',
            'message_id': 'test-integration-edge-001',
            'email_date': datetime.now().isoformat(),
            'recipients': ['hr@arganconsultancy.com'],
            'cc': [],
            'dkim': 'pass',
            'spf': 'pass'
        }
        
        try:
            result3 = await router.route_email(edge_case_email)
            print(f"✅ Routing Result:")
            print(f"   Success: {result3.get('success')}")
            print(f"   Ticket Number: {result3.get('ticket_number')}")
            print(f"   Action: {result3.get('action')}")
            print(f"   AI Enhanced: {result3.get('ai_enhanced')}")
        except Exception as e:
            print(f"❌ Error in Test Case 3: {e}")
        
        print("\n✅ Integration Testing Complete!")
        print("=" * 60)
        
    finally:
        db_session.close()
        # Clean up test database
        import os
        if os.path.exists("test_email_routing.db"):
            os.remove("test_email_routing.db")
        print("🧹 Test database cleaned up")


async def test_auto_reply():
    """Test the auto-reply function directly"""
    
    load_dotenv()
    
    print("🧪 Testing auto-reply function specifically...")
    
    # Test with the same data that would come from webhook
    result = await send_auto_reply(
        recipient="bloxtersamiad@gmail.com",
        ticket_number="ARG-20250531-TEST",
        original_subject="Test Email...over and out",
        sender_name="Lee H",
        priority="Normal",
        ai_summary="Test email from user requesting system testing",
        cc_addresses=None  # CC is disabled for testing
    )
    
    print(f"📧 Auto-reply result: {result}")
    
    if result.get('success'):
        print("✅ Auto-reply sent successfully!")
        print("📱 Check your email (including spam folder)")
        print("📝 Subject should be: [ARG-20250531-TEST] Thank you for contacting Argan Consultancy HR")
    else:
        print("❌ Auto-reply failed!")
        print(f"Error: {result.get('error')}")


async def test_full_email_flow():
    """Test the complete email flow with the exact format that was causing Gmail issues"""
    
    print("🧪 Testing Full Email Processing Flow")
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
        "message_id": "test-message-123-gmail-fix",
        "timestamp": "2025-05-31T22:15:00Z"
    }
    
    print(f"📧 Raw webhook 'from' field: {test_webhook_data['from']}")
    print(f"📝 Subject: {test_webhook_data['subject']}")
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
            print(f"📧 Email should be sent to: cvrcontractsltd@gmail.com (clean format)")
        else:
            print(f"❌ FAILED: {result.get('message', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    print("=" * 60)


if __name__ == "__main__":
    # Load environment variables if .env file exists
    if os.path.exists('.env'):
        load_dotenv()
    
    asyncio.run(test_complete_email_routing())
    asyncio.run(test_auto_reply())
    asyncio.run(test_full_email_flow()) 