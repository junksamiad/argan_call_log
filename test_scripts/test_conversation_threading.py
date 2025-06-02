#!/usr/bin/env python3
"""
Comprehensive Conversation Threading Test
Creates a test ticket and sends progressively complex email replies
to test conversation history building, deduplication, and chronological ordering
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.airtable_service import AirtableService
from backend.email_functions.email_router import EmailRouter


class ConversationThreadingTest:
    def __init__(self):
        self.airtable = AirtableService()
        self.router = EmailRouter()
        self.test_ticket_number = None
        
    def create_test_ticket(self):
        """Create a test ticket in Airtable"""
        print("🎫 Creating test ticket in Airtable...")
        
        # Generate today's ticket number
        today = datetime.now().strftime("%Y%m%d")
        counter = self.airtable.get_ticket_counter()
        ticket_number = f"ARG-{today}-{counter:04d}"
        
        # Create initial email data for the test ticket
        initial_email_data = {
            "sender": "test.employee@company.com",
            "sender_name": "Test Employee",
            "subject": f"Medical Leave Request - {ticket_number}",
            "recipients": ["hr@argan.com"],
            "cc": [],
            "message_id": "initial_test_message",
            "email_date": (datetime.now() - timedelta(days=3)).isoformat(),
            "body_text": "I need to request 6 weeks of medical leave starting March 1st, 2025. I have attached the required medical documentation from my physician.",
            "body_html": "<p>I need to request 6 weeks of medical leave starting March 1st, 2025. I have attached the required medical documentation from my physician.</p>",
            "attachments": ["medical_cert.pdf"],
            "dkim": "pass",
            "spf": "pass"
        }
        
        # Create the record
        try:
            record = self.airtable.create_email_record(
                email_data=initial_email_data,
                ticket_number=ticket_number,
                classification_data={
                    "EMAIL_CLASSIFICATION": "NEW_EMAIL",
                    "confidence_score": 0.99,
                    "ai_extracted_data": {
                        "category": "Leave Request",
                        "priority": "Normal",
                        "urgency_keywords": ["medical leave", "documentation"]
                    }
                }
            )
            
            self.test_ticket_number = ticket_number
            print(f"✅ Created test ticket: {ticket_number}")
            print(f"   Record ID: {record['id']}")
            return ticket_number
            
        except Exception as e:
            print(f"❌ Failed to create test ticket: {e}")
            return None

    def create_email_reply_1(self):
        """Create first reply email (ticket in subject)"""
        return {
            "sender": "hr.support@argan.com",
            "sender_name": "HR Support Team",
            "subject": f"Re: {self.test_ticket_number} - Medical Leave Request",
            "recipients": ["test.employee@company.com"],
            "cc": [],
            "message_id": "reply_1_test_message",
            "email_date": (datetime.now() - timedelta(days=2)).isoformat(),
            "body_text": """Thank you for your medical leave request. We have received your documentation and are reviewing it.

We will need some additional information:
1. Exact start and end dates
2. Contact information for your physician
3. Whether you plan to use FMLA

We'll get back to you within 2 business days.

Best regards,
HR Support Team

On """ + (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d at %I:%M %p") + """, Test Employee <test.employee@company.com> wrote:
> I need to request 6 weeks of medical leave starting March 1st, 2025. 
> I have attached the required medical documentation from my physician.""",
            "body_html": "<html>...</html>",
            "attachments": [],
            "dkim": "pass",
            "spf": "pass"
        }

    def create_email_reply_2(self):
        """Create second reply email (ticket in body)"""
        return {
            "sender": "test.employee@company.com",
            "sender_name": "Test Employee", 
            "subject": "Re: Medical Leave Request - Additional Information",
            "recipients": ["hr@argan.com"],
            "cc": [],
            "message_id": "reply_2_test_message",
            "email_date": (datetime.now() - timedelta(days=1)).isoformat(),
            "body_text": f"""Hi HR Team,

Thank you for your quick response regarding ticket {self.test_ticket_number}.

Here are the additional details you requested:
1. Start date: March 1st, 2025
2. End date: April 15th, 2025 (6.5 weeks)
3. Physician: Dr. Sarah Johnson, (555) 123-4567
4. Yes, I plan to use FMLA benefits

Please let me know if you need anything else.

Best regards,
Test Employee

On """ + (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d at %I:%M %p") + """, HR Support Team <hr.support@argan.com> wrote:
> Thank you for your medical leave request. We have received your documentation and are reviewing it.
> 
> We will need some additional information:
> 1. Exact start and end dates
> 2. Contact information for your physician
> 3. Whether you plan to use FMLA
> 
> We'll get back to you within 2 business days.
> 
> Best regards,
> HR Support Team
> 
> On """ + (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d at %I:%M %p") + """, Test Employee <test.employee@company.com> wrote:
>> I need to request 6 weeks of medical leave starting March 1st, 2025. 
>> I have attached the required medical documentation from my physician.""",
            "body_html": "<html>...</html>",
            "attachments": [],
            "dkim": "pass",
            "spf": "pass"
        }

    def create_email_reply_3(self):
        """Create third reply email with even more thread history"""
        return {
            "sender": "hr.support@argan.com",
            "sender_name": "HR Support Team",
            "subject": f"Re: {self.test_ticket_number} - Medical Leave Approved",
            "recipients": ["test.employee@company.com"],
            "cc": ["payroll@argan.com"],
            "message_id": "reply_3_test_message", 
            "email_date": datetime.now().isoformat(),
            "body_text": f"""Dear Test Employee,

Your medical leave request has been approved for the period March 1st through April 15th, 2025.

We have:
- Processed your FMLA paperwork
- Notified payroll of the leave dates
- Set up temporary coverage for your responsibilities

You should receive official documentation within 24 hours.

Best regards,
HR Support Team

On """ + (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d at %I:%M %p") + """, Test Employee <test.employee@company.com> wrote:
> Hi HR Team,
> 
> Thank you for your quick response regarding ticket """ + self.test_ticket_number + """.
> 
> Here are the additional details you requested:
> 1. Start date: March 1st, 2025
> 2. End date: April 15th, 2025 (6.5 weeks)
> 3. Physician: Dr. Sarah Johnson, (555) 123-4567
> 4. Yes, I plan to use FMLA benefits
> 
> Please let me know if you need anything else.
> 
> Best regards,
> Test Employee
> 
> On """ + (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d at %I:%M %p") + """, HR Support Team <hr.support@argan.com> wrote:
>> Thank you for your medical leave request. We have received your documentation and are reviewing it.
>> 
>> We will need some additional information:
>> 1. Exact start and end dates
>> 2. Contact information for your physician
>> 3. Whether you plan to use FMLA
>> 
>> We'll get back to you within 2 business days.
>> 
>> Best regards,
>> HR Support Team
>> 
>> On """ + (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d at %I:%M %p") + """, Test Employee <test.employee@company.com> wrote:
>>> I need to request 6 weeks of medical leave starting March 1st, 2025. 
>>> I have attached the required medical documentation from my physician.""",
            "body_html": "<html>...</html>",
            "attachments": [],
            "dkim": "pass",
            "spf": "pass"
        }

    async def process_email_through_system(self, email_data, test_name):
        """Process an email through the complete system"""
        print(f"\n📧 Processing {test_name}...")
        print(f"   From: {email_data['sender']}")
        print(f"   Subject: {email_data['subject']}")
        
        try:
            # Route the email through the system
            result = await self.router.route_email(email_data)
            
            print(f"   Result: {result.get('success', False)}")
            if result.get('success'):
                print(f"   ✅ {result.get('message', 'Processed successfully')}")
                if 'new_messages_count' in result:
                    print(f"   📈 New messages added: {result['new_messages_count']}")
                    print(f"   📊 Total messages: {result['total_messages']}")
            else:
                print(f"   ❌ {result.get('error', 'Processing failed')}")
            
            return result.get('success', False)
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

    def verify_conversation_history(self):
        """Verify the conversation history is built correctly"""
        print(f"\n🔍 Verifying conversation history for {self.test_ticket_number}...")
        
        try:
            # Get the ticket record
            record = self.airtable.find_ticket(self.test_ticket_number)
            if not record:
                print("❌ Test ticket not found")
                return False
            
            # Get conversation history
            conversation_json = record['fields'].get('Conversation History', '[]')
            conversation = json.loads(conversation_json)
            
            print(f"📊 Conversation contains {len(conversation)} messages")
            
            # Check chronological order
            timestamps = [msg.get('timestamp', '') for msg in conversation]
            sorted_timestamps = sorted(timestamps)
            
            if timestamps == sorted_timestamps:
                print("✅ Messages are in chronological order")
            else:
                print("❌ Messages are not in chronological order")
                print(f"   Actual: {timestamps}")
                print(f"   Expected: {sorted_timestamps}")
                return False
            
            # Check for duplicates using content hashes
            content_hashes = [msg.get('content_hash', '') for msg in conversation if msg.get('content_hash')]
            unique_hashes = set(content_hashes)
            
            if len(content_hashes) == len(unique_hashes):
                print("✅ No duplicate messages found")
            else:
                print(f"❌ Found {len(content_hashes) - len(unique_hashes)} duplicate messages")
                return False
            
            # Display conversation summary
            print("\n📜 Conversation Summary:")
            for i, msg in enumerate(conversation, 1):
                sender = msg.get('sender', 'Unknown')
                timestamp = msg.get('timestamp', 'Unknown')
                content_preview = msg.get('body_text', '')[:50] + "..."
                msg_type = msg.get('message_type', 'unknown')
                source = msg.get('source', 'unknown')
                
                print(f"   {i}. [{timestamp}] {sender} ({msg_type}/{source})")
                print(f"      {content_preview}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error verifying conversation history: {e}")
            return False

    def cleanup_test_ticket(self):
        """Clean up the test ticket"""
        if self.test_ticket_number:
            print(f"\n🧹 Cleaning up test ticket {self.test_ticket_number}...")
            try:
                record = self.airtable.find_ticket(self.test_ticket_number)
                if record:
                    # Note: We could delete here, but let's leave it for manual inspection
                    print(f"✅ Test ticket remains in Airtable for inspection: {self.test_ticket_number}")
                else:
                    print("⚠️ Test ticket not found for cleanup")
            except Exception as e:
                print(f"❌ Error during cleanup: {e}")


async def main():
    """Run the comprehensive conversation threading test"""
    print("🚀 Starting Comprehensive Conversation Threading Test")
    print("=" * 70)
    
    # Check prerequisites
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        return
    
    if not os.getenv("AIRTABLE_API_KEY"):
        print("❌ Error: AIRTABLE_API_KEY environment variable not set")
        return
    
    test = ConversationThreadingTest()
    
    try:
        # Step 1: Create test ticket
        ticket_number = test.create_test_ticket()
        if not ticket_number:
            print("❌ Failed to create test ticket, aborting test")
            return
        
        # Step 2: Process first reply (ticket in subject)
        reply1 = test.create_email_reply_1()
        success1 = await test.process_email_through_system(reply1, "Reply 1 (ticket in subject)")
        
        # Step 3: Process second reply (ticket in body)
        reply2 = test.create_email_reply_2()
        success2 = await test.process_email_through_system(reply2, "Reply 2 (ticket in body)")
        
        # Step 4: Process third reply (complex thread)
        reply3 = test.create_email_reply_3()
        success3 = await test.process_email_through_system(reply3, "Reply 3 (complex thread)")
        
        # Step 5: Verify conversation history
        history_valid = test.verify_conversation_history()
        
        # Summary
        print("\n" + "=" * 70)
        print("📋 Test Results Summary:")
        print(f"   Test Ticket Creation:  {'✅ PASSED' if ticket_number else '❌ FAILED'}")
        print(f"   Reply 1 Processing:    {'✅ PASSED' if success1 else '❌ FAILED'}")
        print(f"   Reply 2 Processing:    {'✅ PASSED' if success2 else '❌ FAILED'}")
        print(f"   Reply 3 Processing:    {'✅ PASSED' if success3 else '❌ FAILED'}")
        print(f"   Conversation History:  {'✅ PASSED' if history_valid else '❌ FAILED'}")
        
        if all([ticket_number, success1, success2, success3, history_valid]):
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ Conversation threading is working correctly")
            print("✅ Deduplication is functioning properly")
            print("✅ Chronological ordering is maintained")
            print("✅ Both subject and body ticket detection work")
        else:
            print("\n❌ Some tests failed!")
            print("Please review the errors above")
        
        print(f"\n📍 Test ticket {ticket_number} remains in Airtable for inspection")
        
    except Exception as e:
        print(f"❌ Test execution error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup (optional)
        test.cleanup_test_ticket()


if __name__ == "__main__":
    asyncio.run(main()) 