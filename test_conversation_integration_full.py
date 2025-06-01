"""
Full Integration Test for Conversation History with Airtable
Tests the complete NEW_EMAIL path including database record creation
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Add the backend directory to the Python path
sys.path.append('backend')

# Load environment variables
load_dotenv()

from backend.email_functions.initial_email.initial_email import process_initial_email
from backend.airtable_service import AirtableService

async def test_full_conversation_integration():
    """Test the complete conversation history integration with Airtable"""
    print("🧪 Testing Full Conversation History Integration")
    print("=" * 60)
    
    # Mock email data (similar to what SendGrid webhook would send)
    email_data = {
        "sender": "test.manager@careHome.com",
        "sender_name": "Test Care Manager",
        "subject": "Staff Training Query - Conversation History Test",
        "body_text": "Hello HR Team,\n\nI need guidance on the new mandatory training requirements for our care staff. When do these need to be completed by?\n\nBest regards,\nTest Manager",
        "body_html": "<p>Hello HR Team,</p><p>I need guidance on the new mandatory training requirements for our care staff. When do these need to be completed by?</p><p>Best regards,<br>Test Manager</p>",
        "email_date": datetime.utcnow().isoformat(),
        "message_id": f"test_conversation_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}@sendgrid.net",
        "recipients": ["hr@company.com"],
        "cc": [],
        "dkim": "pass",
        "spf": "pass"
    }
    
    # Mock AI classification data in the format expected by airtable service
    ai_extracted_data = {
        "ai_summary": "Care manager requesting guidance on mandatory training requirements and completion deadlines for care staff",
        "hr_category": "Training",
        "sender_name": "Test Care Manager",
        "sender_domain": "careHome.com",
        "urgency_keywords": ["mandatory", "requirements"],
        "sentiment_tone": "Professional, seeking guidance",
        "mentioned_people": [],
        "mentioned_departments": ["HR Team"],
        "deadline_mentions": ["need to be completed by"],
        "policy_references": ["training requirements"],
        "contact_phone": "",
        "contact_address": ""
    }
    
    # Create the object format for conversation history creation
    class MockAIData:
        def __init__(self, data):
            for key, value in data.items():
                setattr(self, key, value)
    
    class MockClassificationData:
        def __init__(self, ai_data, classification_type, confidence, timestamp):
            self.EMAIL_DATA = MockAIData(ai_data)
            self.EMAIL_CLASSIFICATION = classification_type
            self.confidence_score = confidence
            self.processing_timestamp = timestamp
    
    # Create both formats
    classification_data_dict = {
        "EMAIL_CLASSIFICATION": "NEW_EMAIL",
        "confidence_score": 95,
        "processing_timestamp": datetime.utcnow().isoformat(),
        "ai_extracted_data": ai_extracted_data
    }
    
    # Create object version for functions that expect it
    classification_data_obj = MockClassificationData(
        ai_extracted_data, 
        "NEW_EMAIL", 
        95, 
        datetime.utcnow().isoformat()
    )
    
    # We'll pass the dict format which the functions should handle
    classification_data = classification_data_dict
    
    print(f"📧 Test Email Details:")
    print(f"   Sender: {email_data['sender']}")
    print(f"   Subject: {email_data['subject']}")
    print(f"   Body Length: {len(email_data['body_text'])} chars")
    print(f"   AI Classification: {classification_data['EMAIL_CLASSIFICATION']}")
    print(f"   AI Confidence: {classification_data['confidence_score']}%")
    print(f"   HR Category: {classification_data['ai_extracted_data']['hr_category']}")
    print(f"   AI Summary: {classification_data['ai_extracted_data']['ai_summary']}")
    
    try:
        # Test the full email processing pipeline
        print(f"\n🚀 Processing email through full pipeline...")
        
        result = await process_initial_email(email_data, classification_data)
        
        if result.get("success"):
            ticket_number = result.get("ticket_number")
            airtable_record_id = result.get("airtable_record_id")
            
            print(f"\n✅ Email Processing Successful!")
            print(f"   Ticket Number: {ticket_number}")
            print(f"   Airtable Record ID: {airtable_record_id}")
            print(f"   AI Classification: {result.get('ai_classification')}")
            print(f"   AI Confidence: {result.get('ai_confidence')}%")
            
            # Now verify the record was created with conversation history
            print(f"\n🔍 Verifying Airtable Record...")
            
            airtable = AirtableService()
            
            # Find the record we just created
            created_record = airtable.find_ticket(ticket_number)
            
            if created_record:
                print(f"✅ Found record in Airtable!")
                
                # Check the conversation history field
                conversation_history_json = created_record['fields'].get('Conversation History', '[]')
                
                if conversation_history_json and conversation_history_json != '[]':
                    try:
                        conversation_history = json.loads(conversation_history_json)
                        
                        print(f"\n📜 Conversation History Analysis:")
                        print(f"   JSON Length: {len(conversation_history_json)} chars")
                        print(f"   Message Count: {len(conversation_history)}")
                        
                        if len(conversation_history) > 0:
                            first_message = conversation_history[0]
                            
                            print(f"\n📝 First Message Details:")
                            print(f"   Message ID: {first_message.get('message_id')}")
                            print(f"   Timestamp: {first_message.get('timestamp')}")
                            print(f"   Sender: {first_message.get('sender')}")
                            print(f"   Message Type: {first_message.get('message_type')}")
                            print(f"   Source: {first_message.get('source')}")
                            print(f"   Thread Position: {first_message.get('thread_position')}")
                            print(f"   Content Hash: {first_message.get('content_hash')}")
                            print(f"   AI Summary: {first_message.get('ai_summary')}")
                            print(f"   Body Text Length: {len(first_message.get('body_text', ''))} chars")
                            
                            # Verify all required fields are present
                            required_fields = [
                                'message_id', 'timestamp', 'sender', 'message_type',
                                'source', 'subject', 'body_text', 'content_hash',
                                'thread_position', 'ai_summary'
                            ]
                            
                            missing_fields = [field for field in required_fields if field not in first_message]
                            
                            if not missing_fields:
                                print(f"✅ All required conversation fields present!")
                            else:
                                print(f"❌ Missing fields: {missing_fields}")
                                return False
                            
                            # Check other Airtable fields
                            print(f"\n📊 Other Airtable Fields:")
                            print(f"   AI Summary: {created_record['fields'].get('AI Summary', 'MISSING')}")
                            print(f"   Query Type: {created_record['fields'].get('Query Type', 'MISSING')}")
                            print(f"   Status: {created_record['fields'].get('Status', 'MISSING')}")
                            print(f"   Message Type: {created_record['fields'].get('Message Type', 'MISSING')}")
                            print(f"   Created At: {created_record['fields'].get('Created At', 'MISSING')}")
                            
                            print(f"\n🎉 Full Integration Test PASSED!")
                            print(f"✅ Conversation history is working end-to-end!")
                            return True
                            
                        else:
                            print(f"❌ Conversation history is empty")
                            return False
                            
                    except json.JSONDecodeError as e:
                        print(f"❌ Failed to parse conversation history JSON: {e}")
                        return False
                        
                else:
                    print(f"❌ No conversation history found in record")
                    return False
                    
            else:
                print(f"❌ Could not find record with ticket number {ticket_number}")
                return False
                
        else:
            print(f"❌ Email processing failed: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Integration test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_airtable_connection():
    """Test Airtable connection before running full test"""
    print("🔗 Testing Airtable Connection...")
    
    try:
        airtable = AirtableService()
        health_check = airtable.health_check()
        
        if health_check:
            print("✅ Airtable connection successful!")
            return True
        else:
            print("❌ Airtable health check failed")
            return False
            
    except Exception as e:
        print(f"❌ Airtable connection error: {e}")
        return False

async def main():
    """Run the full test suite"""
    print("🚀 Full Conversation History Integration Test Suite")
    print("=" * 70)
    
    # First test Airtable connection
    connection_ok = await test_airtable_connection()
    if not connection_ok:
        print("\n❌ Cannot proceed without Airtable connection")
        return False
    
    # Run the full integration test
    integration_result = await test_full_conversation_integration()
    
    print(f"\n📊 Final Test Results:")
    print(f"   Airtable Connection: {'✅ PASS' if connection_ok else '❌ FAIL'}")
    print(f"   Full Integration: {'✅ PASS' if integration_result else '❌ FAIL'}")
    
    if connection_ok and integration_result:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"✅ Conversation history is fully integrated and working!")
        print(f"✅ New emails will now have conversation tracking!")
        return True
    else:
        print(f"\n❌ Some tests failed. Please check the setup.")
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    if not result:
        sys.exit(1) 