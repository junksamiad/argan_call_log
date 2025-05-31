#!/usr/bin/env python3
"""
Email Auto-Reply Handler
Simple integration script to handle incoming emails and send auto-replies
"""

import asyncio
import sys
import os
import logging
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.services.auto_reply_service import AutoReplyService
from backend.models.database import Base
from config.settings import settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = getattr(settings, 'DATABASE_URL', 'sqlite:///argan_email.db')
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


async def handle_incoming_email(email_data: dict) -> dict:
    """
    Handle an incoming email and send auto-reply
    
    Args:
        email_data: Dictionary containing email information:
            - sender: sender email address (required)
            - subject: email subject (required)
            - body_text: email body text (required)
            - body_html: email body HTML (optional)
            - message_id: unique message ID (optional, will generate if not provided)
            - recipients: list of recipients (optional)
            - cc: list of CC recipients (optional)
            - email_date: datetime of email (optional, will use current time)
    
    Returns:
        Dictionary with processing results
    """
    db = SessionLocal()
    try:
        logger.info(f"Processing incoming email from {email_data.get('sender')}")
        
        # Validate required fields
        required_fields = ['sender', 'subject', 'body_text']
        for field in required_fields:
            if not email_data.get(field):
                raise ValueError(f"Missing required field: {field}")
        
        # Set defaults for optional fields
        if not email_data.get('message_id'):
            email_data['message_id'] = f"msg-{datetime.utcnow().timestamp()}"
        
        if not email_data.get('email_date'):
            email_data['email_date'] = datetime.utcnow()
        
        if not email_data.get('recipients'):
            email_data['recipients'] = ['hr@arganconsultancy.co.uk']
        
        # Create auto-reply service and process email
        auto_reply_service = AutoReplyService(db)
        result = await auto_reply_service.process_incoming_email_and_reply(email_data)
        
        if result.get('success'):
            logger.info(f"Successfully processed email. Ticket: {result.get('ticket_number')}")
        else:
            logger.error(f"Failed to process email: {result.get('message')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error handling incoming email: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to handle incoming email"
        }
    finally:
        db.close()


async def test_with_sample_email():
    """Test the handler with a sample email"""
    print("🧪 Testing Auto-Reply Handler with Sample Email")
    print("=" * 60)
    
    sample_email = {
        'sender': 'test.employee@company.com',
        'subject': 'Question about sick leave policy',
        'body_text': '''Hi HR Team,

I hope this email finds you well. I have a question about the sick leave policy.

Specifically, I'd like to know:
1. How many sick days am I entitled to per year?
2. Do I need a doctor's note for absences longer than 2 days?
3. Can unused sick days be carried over to the next year?

I would appreciate your guidance on this matter.

Best regards,
Test Employee''',
        'body_html': '''<p>Hi HR Team,</p>
<p>I hope this email finds you well. I have a question about the sick leave policy.</p>
<p>Specifically, I'd like to know:</p>
<ol>
<li>How many sick days am I entitled to per year?</li>
<li>Do I need a doctor's note for absences longer than 2 days?</li>
<li>Can unused sick days be carried over to the next year?</li>
</ol>
<p>I would appreciate your guidance on this matter.</p>
<p>Best regards,<br>Test Employee</p>'''
    }
    
    try:
        result = await handle_incoming_email(sample_email)
        
        print("📧 Sample Email Processed:")
        print(f"From: {sample_email['sender']}")
        print(f"Subject: {sample_email['subject']}")
        print(f"Body: {sample_email['body_text'][:100]}...")
        print()
        
        print("📋 Processing Result:")
        print(f"Success: {result.get('success')}")
        print(f"Ticket Number: {result.get('ticket_number')}")
        print(f"Auto-Reply Sent: {result.get('auto_reply_sent')}")
        print(f"Message: {result.get('message')}")
        
        if result.get('success'):
            print("\n✅ Auto-reply system working correctly!")
            print(f"🎫 Generated ticket: {result.get('ticket_number')}")
            print("📧 Auto-reply sent to sender")
            print("📧 Copy sent to advice@arganconsultancy.co.uk")
        else:
            print(f"\n❌ Error: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Email Auto-Reply Handler')
    parser.add_argument('--test', action='store_true', help='Run test with sample email')
    parser.add_argument('--sender', help='Sender email address')
    parser.add_argument('--subject', help='Email subject')
    parser.add_argument('--body', help='Email body text')
    
    args = parser.parse_args()
    
    if args.test:
        # Run test
        asyncio.run(test_with_sample_email())
    elif args.sender and args.subject and args.body:
        # Process provided email
        email_data = {
            'sender': args.sender,
            'subject': args.subject,
            'body_text': args.body
        }
        
        async def process_email():
            result = await handle_incoming_email(email_data)
            print(f"Processing result: {result}")
        
        asyncio.run(process_email())
    else:
        print("Usage:")
        print("  python email_auto_reply_handler.py --test")
        print("  python email_auto_reply_handler.py --sender email@example.com --subject 'Subject' --body 'Body text'")
        print()
        print("This script provides an auto-reply system that:")
        print("✅ Generates unique ticket numbers (ARG-YYYYMMDD-XXXX)")
        print("✅ Sends professional auto-reply to sender")
        print("✅ CCs advice@arganconsultancy.co.uk")
        print("✅ Tracks emails in database")
        print("✅ Handles both new emails and replies to existing tickets")


if __name__ == "__main__":
    main() 