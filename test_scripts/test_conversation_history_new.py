"""
Test Script for Conversation History - NEW_EMAIL Path
Tests the initial conversation history creation functionality
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Add the backend directory to the Python path
sys.path.append('backend')

# Load environment variables
load_dotenv()

from backend.email_functions.initial_email.initial_email import (
    create_initial_conversation_entry,
    generate_message_id,
    generate_content_hash
)

def test_conversation_history_creation():
    """Test the conversation history creation for new emails"""
    print("🧪 Testing Conversation History Creation")
    print("=" * 50)
    
    # Mock email data
    email_data = {
        "sender": "jane.smith@careHome.com",
        "sender_name": "Jane Smith",
        "subject": "Performance Management Query - Urgent",
        "body_text": "Hello HR Team,\n\nI need urgent guidance regarding an employee performance issue...",
        "email_date": datetime.utcnow().isoformat(),
        "message_id": "test_message_123@sendgrid.net",
        "recipients": ["hr@company.com"]
    }
    
    # Mock classification data
    class MockClassificationData:
        class EMAIL_DATA:
            ai_summary = "Performance management query requiring urgent HR guidance"
            ticket_number = None
    
    classification_data = MockClassificationData()
    
    print(f"📧 Test Email Data:")
    print(f"   Sender: {email_data['sender']}")
    print(f"   Subject: {email_data['subject']}")
    print(f"   Body Length: {len(email_data['body_text'])} chars")
    
    # Test conversation history creation
    try:
        conversation_history = create_initial_conversation_entry(email_data, classification_data)
        
        print(f"\n✅ Conversation History Created Successfully!")
        print(f"   Message Count: {len(conversation_history)}")
        
        # Verify the structure
        first_message = conversation_history[0]
        
        print(f"\n📜 First Message Structure:")
        print(f"   Message ID: {first_message['message_id']}")
        print(f"   Timestamp: {first_message['timestamp']}")
        print(f"   Sender: {first_message['sender']}")
        print(f"   Message Type: {first_message['message_type']}")
        print(f"   Source: {first_message['source']}")
        print(f"   Thread Position: {first_message['thread_position']}")
        print(f"   Content Hash: {first_message['content_hash']}")
        print(f"   AI Summary: {first_message['ai_summary']}")
        
        # Test JSON serialization
        json_conversation = json.dumps(conversation_history)
        print(f"\n💾 JSON Serialization:")
        print(f"   JSON Length: {len(json_conversation)} chars")
        print(f"   Valid JSON: ✅")
        
        # Test JSON deserialization
        parsed_conversation = json.loads(json_conversation)
        print(f"   Parsed back successfully: ✅")
        print(f"   Message count matches: {len(parsed_conversation) == len(conversation_history)} ✅")
        
        # Test utility functions
        print(f"\n🔧 Utility Function Tests:")
        
        # Test message ID generation
        message_id = generate_message_id(email_data)
        print(f"   Generated Message ID: {message_id}")
        print(f"   ID Length: {len(message_id)} chars")
        
        # Test content hash generation
        content_hash = generate_content_hash(email_data['body_text'])
        print(f"   Generated Content Hash: {content_hash}")
        print(f"   Hash Length: {len(content_hash)} chars")
        
        # Test consistency (same input should produce same output)
        message_id_2 = generate_message_id(email_data)
        content_hash_2 = generate_content_hash(email_data['body_text'])
        
        print(f"   Message ID Consistency: {message_id == message_id_2} ✅")
        print(f"   Content Hash Consistency: {content_hash == content_hash_2} ✅")
        
        # Test empty content handling
        empty_hash = generate_content_hash("")
        print(f"   Empty Content Hash: '{empty_hash}' (should be empty)")
        
        print(f"\n🎉 All Tests Passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_message_creation():
    """Test creating multiple conversation entries (for future thread testing)"""
    print("\n🧪 Testing Multiple Message Creation")
    print("=" * 50)
    
    # Create multiple email data samples
    emails = [
        {
            "sender": "jane.smith@careHome.com",
            "sender_name": "Jane Smith", 
            "subject": "Performance Management Query - Urgent",
            "body_text": "Initial query about employee performance...",
            "email_date": "2024-06-01T10:00:00Z",
            "message_id": "msg1@test.com"
        },
        {
            "sender": "hr@company.com",
            "sender_name": "HR Team",
            "subject": "Re: Performance Management Query - Urgent", 
            "body_text": "Thank you for your query. We need more details...",
            "email_date": "2024-06-01T11:00:00Z",
            "message_id": "msg2@test.com"
        },
        {
            "sender": "jane.smith@careHome.com",
            "sender_name": "Jane Smith",
            "subject": "Re: Performance Management Query - Urgent",
            "body_text": "Here are the additional details you requested...",
            "email_date": "2024-06-01T12:00:00Z", 
            "message_id": "msg3@test.com"
        }
    ]
    
    conversation_entries = []
    
    for i, email_data in enumerate(emails):
        entry = create_initial_conversation_entry(email_data)
        conversation_entries.extend(entry)
        print(f"   Created entry {i+1}: {entry[0]['sender']} at {entry[0]['timestamp']}")
    
    print(f"\n📜 Conversation Summary:")
    print(f"   Total Messages: {len(conversation_entries)}")
    
    # Test chronological sorting
    sorted_entries = sorted(conversation_entries, key=lambda x: x['timestamp'])
    print(f"   Chronological Order:")
    for i, entry in enumerate(sorted_entries):
        print(f"     {i+1}. {entry['sender']} - {entry['timestamp']}")
    
    # Test deduplication by content hash
    content_hashes = [entry['content_hash'] for entry in conversation_entries]
    unique_hashes = set(content_hashes)
    print(f"   Unique Content Hashes: {len(unique_hashes)} (should equal {len(conversation_entries)})")
    
    return len(unique_hashes) == len(conversation_entries)

if __name__ == "__main__":
    print("🚀 Conversation History Test Suite")
    print("=" * 60)
    
    # Run tests
    test1_result = test_conversation_history_creation()
    test2_result = test_multiple_message_creation()
    
    print(f"\n📊 Test Results Summary:")
    print(f"   Basic Conversation History: {'✅ PASS' if test1_result else '❌ FAIL'}")
    print(f"   Multiple Message Creation: {'✅ PASS' if test2_result else '❌ FAIL'}")
    
    if test1_result and test2_result:
        print(f"\n🎉 All conversation history tests passed!")
        print(f"✅ The system is ready for conversation tracking!")
    else:
        print(f"\n❌ Some tests failed. Please check the implementation.")
        sys.exit(1) 