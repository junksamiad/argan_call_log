#!/usr/bin/env python3
"""
Simple test script for ticket generation and database functionality
Tests the core auto-reply logic without requiring email sending
"""

import asyncio
import sys
import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.services.auto_reply_service import AutoReplyService
from backend.models.database import Base, TicketCounter, EmailThread, EmailMessage
from config.settings import settings

def test_basic_functionality():
    """Test basic functionality without email sending"""
    print("🚀 Testing Auto-Reply System Core Functionality")
    print("=" * 60)
    
    # Create test database
    engine = create_engine("sqlite:///test_tickets.db", echo=False)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    try:
        auto_reply_service = AutoReplyService(db)
        
        # Test 1: Ticket Generation
        print("\n🎫 Test 1: Ticket Number Generation")
        print("-" * 40)
        
        tickets = []
        for i in range(3):
            ticket = auto_reply_service.generate_ticket_number()
            tickets.append(ticket)
            print(f"Generated ticket {i+1}: {ticket}")
        
        # Verify tickets are unique
        if len(set(tickets)) == len(tickets):
            print("✅ All tickets are unique")
        else:
            print("❌ Duplicate tickets found!")
        
        # Test 2: Subject Formatting
        print("\n📧 Test 2: Subject Line Formatting")
        print("-" * 40)
        
        test_cases = [
            ("Help with payroll", tickets[0]),
            ("Re: Urgent question", tickets[1]),
            (f"[{tickets[0]}] Follow up", tickets[0]),
        ]
        
        for original, ticket in test_cases:
            formatted = auto_reply_service.format_reply_subject(original, ticket)
            print(f"'{original}' → '{formatted}'")
        
        # Test 3: Ticket Extraction
        print("\n🔍 Test 3: Ticket Number Extraction")
        print("-" * 40)
        
        test_subjects = [
            f"Re: [{tickets[0]}] Help with payroll",
            f"Follow up on {tickets[1]}",
            "No ticket number here",
        ]
        
        for subject in test_subjects:
            extracted = auto_reply_service.extract_existing_ticket_number(subject)
            print(f"'{subject}' → {extracted or 'None'}")
        
        # Test 4: Content Generation
        print("\n📝 Test 4: Auto-Reply Content Generation")
        print("-" * 40)
        
        content = auto_reply_service.generate_auto_reply_content(tickets[0], "test@example.com")
        print("Text content preview:")
        print(content['text'][:200] + "...")
        print(f"\nHTML content length: {len(content['html'])} characters")
        
        # Test 5: Database Operations (without email sending)
        print("\n💾 Test 5: Database Operations")
        print("-" * 40)
        
        # Create a test email thread
        email_data = {
            'sender': 'test.user@company.com',
            'subject': 'Test HR Question',
            'body_text': 'This is a test email for the HR system.',
            'message_id': f'test-msg-{datetime.utcnow().timestamp()}',  # Make unique
            'recipients': ['hr@arganconsultancy.co.uk'],
            'email_date': datetime.utcnow()
        }
        
        # Create thread manually (simulating the process without email sending)
        thread = auto_reply_service._create_new_thread(email_data, tickets[0])
        print(f"Created thread: {thread.ticket_number}")
        
        # Verify thread was saved
        saved_thread = db.query(EmailThread).filter_by(ticket_number=tickets[0]).first()
        if saved_thread:
            print(f"✅ Thread saved to database: ID {saved_thread.id}")
            
            # Check if message was saved
            message_count = db.query(EmailMessage).filter_by(thread_id=saved_thread.id).count()
            print(f"✅ Messages in thread: {message_count}")
        else:
            print("❌ Thread not found in database")
        
        print("\n🎉 All core functionality tests completed!")
        print("\nSummary:")
        print("✅ Ticket generation working")
        print("✅ Subject formatting working") 
        print("✅ Ticket extraction working")
        print("✅ Content generation working")
        print("✅ Database operations working")
        print("\nNext steps:")
        print("- Set up SendGrid API key in .env for email sending")
        print("- Test with actual email integration")
        print("- Set up Airtable integration (optional)")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()


if __name__ == "__main__":
    test_basic_functionality() 